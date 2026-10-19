package org.fog.test.perfeval;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.Writer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Calendar;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.TimeUnit;

import org.cloudbus.cloudsim.Host;
import org.cloudbus.cloudsim.Log;
import org.cloudbus.cloudsim.Pe;
import org.cloudbus.cloudsim.Storage;
import org.cloudbus.cloudsim.core.CloudSim;
import org.cloudbus.cloudsim.core.SimEntity;
import org.cloudbus.cloudsim.core.SimEvent;
import org.cloudbus.cloudsim.power.PowerHost;
import org.cloudbus.cloudsim.provisioners.RamProvisionerSimple;
import org.cloudbus.cloudsim.sdn.overbooking.BwProvisionerOverbooking;
import org.cloudbus.cloudsim.sdn.overbooking.PeProvisionerOverbooking;
import org.fog.application.AppEdge;
import org.fog.application.Application;
import org.fog.application.selectivity.FractionalSelectivity;
import org.fog.entities.Actuator;
import org.fog.entities.FogBroker;
import org.fog.entities.FogDevice;
import org.fog.entities.FogDeviceCharacteristics;
import org.fog.entities.Tuple;
import org.fog.placement.Controller;
import org.fog.placement.ModuleMapping;
import org.fog.placement.ModulePlacementMapping;
import org.fog.policy.AppModuleAllocationPolicy;
import org.fog.scheduler.StreamOperatorScheduler;
import org.fog.utils.FogEvents;
import org.fog.utils.FogLinearPowerModel;
import org.fog.utils.FogUtils;
import org.fog.utils.distribution.DeterministicDistribution;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;

/**
 * A deliberately small, experiment-owned integration of the existing JSONL
 * RL service with classic iFogSim routing.  It neither changes FogDevice nor
 * uses destinationDeviceId as a routing shortcut: the decision selects one of
 * three modules statically hosted on Local, Edge, and Cloud respectively.
 */
public final class RlOffloadingIntegrationExperiment {
    private static final String APP_ID = "rl-offload-one-task";
    private static final String LOCAL_MODULE = "local_executor";
    private static final String EDGE_MODULE = "edge_executor";
    private static final String CLOUD_MODULE = "cloud_executor";
    private static final String RESULT_ENDPOINT = "RESULT_ENDPOINT";
    private static final long TASK_MI = 2500L;
    private static final int TASK_PES = 1;
    private static final long INPUT_BYTES = 12000L;
    private static final long RESULT_BYTES = 2000L;
    private static final double DEADLINE_MS = 500.0;
    private static final double WAN_UPLINK_MS = 45.0;
    private static final long AGENT_TIMEOUT_MS = 1000L;

    private RlOffloadingIntegrationExperiment() { }

    public static void main(String[] args) {
        try {
            Options options = Options.parse(args);
            Files.createDirectories(options.outputDir);
            try (Trace trace = new Trace(options.outputDir.resolve("java_trace.jsonl"));
                 PythonAdapter python = PythonAdapter.start(options, trace)) {
                run(options, trace, python);
            }
        } catch (Throwable t) {
            t.printStackTrace(System.err);
            System.exit(2);
        }
    }

    private static void run(Options options, Trace trace, PythonAdapter python) throws Exception {
        Log.disable();
        CloudSim.init(1, Calendar.getInstance(), false);
        FogBroker broker = new FogBroker("rl-integration-broker");
        TaskRegistry registry = new TaskRegistry(options, trace, python, broker.getId());

        List<FogDevice> devices = new ArrayList<FogDevice>();
        InstrumentedFogDevice cloud = createDevice("cloud", 44800, 40000, 100000, 100000, 0,
                16 * 103, 16 * 83.25, registry);
        cloud.setParentId(-1);
        InstrumentedFogDevice edge = createDevice("edge", 2800, 4000, 10000, 10000, 1,
                107.339, 83.4333, registry);
        edge.setParentId(cloud.getId());
        edge.setUplinkLatency(WAN_UPLINK_MS);
        InstrumentedFogDevice local = createDevice("local", 1000, 2000, 10000, 10000, 2,
                87.53, 82.44, registry);
        local.setParentId(edge.getId());
        local.setUplinkLatency(2.0);
        devices.add(cloud);
        devices.add(edge);
        devices.add(local);

        List<Actuator> actuators = new ArrayList<Actuator>();
        ResultEndpoint endpoint = new ResultEndpoint("result-endpoint", broker.getId(), APP_ID,
                local.getId(), 1.0, registry);
        actuators.add(endpoint);

        Application app = createApplication(APP_ID, broker.getId());
        ModuleMapping mapping = ModuleMapping.createModuleMapping();
        mapping.addModuleToDevice(LOCAL_MODULE, "local");
        mapping.addModuleToDevice(EDGE_MODULE, "edge");
        mapping.addModuleToDevice(CLOUD_MODULE, "cloud");
        Controller controller = new Controller("rl-integration-controller", devices,
                Collections.emptyList(), actuators);
        controller.submitApplication(app, new ModulePlacementMapping(devices, app, mapping));

        trace.record("config", mapOf(
            "run_id", options.runId, "python_mode", options.pythonMode,
            "python_policy", options.pythonPolicy, "fault_mode", options.faultMode,
            "task_mi", TASK_MI, "task_pes", TASK_PES, "deadline_ms", options.deadlineMs,
                "wan_latency_ms_configured", WAN_UPLINK_MS,
                "input_bytes", INPUT_BYTES, "result_bytes", RESULT_BYTES,
                "counted_links", "FogDevice parent-child uplink/downlink only",
                "created_at", Instant.now().toString()));
        new TaskEmitter("one-task-emitter", local, edge, registry);
        CloudSim.startSimulation();
        CloudSim.stopSimulation();

        if (!registry.terminal || registry.failed) {
            throw new IllegalStateException("simulation ended without a completed terminal task: " + registry.failureReason);
        }
        if (!registry.agentDecisionAccepted && options.faultMode == null) {
            throw new IllegalStateException("agent did not provide a valid decision; fallback trace is not an RL pass");
        }
        registry.assertConsistent();
        trace.record("acceptance", mapOf("status", "PASS", "task_id", registry.taskId,
                "requested_action", registry.requestedAction, "action_executed", registry.executedAction,
                "executing_device", registry.executingDevice, "latency_ms", registry.latencyMs,
                "bandwidth_bytes", registry.bandwidthBytes, "deadline_met", registry.deadlineMet,
                "decision_source", registry.agentDecisionAccepted ? "agent" : "fallback_error"));
    }

    private static Application createApplication(String appId, int userId) {
        Application app = Application.createApplication(appId, userId);
        app.addAppModule(LOCAL_MODULE, 64, 1000, 10000);
        app.addAppModule(EDGE_MODULE, 64, 1000, 10000);
        app.addAppModule(CLOUD_MODULE, 64, 1000, 10000);
        for (String module : new String[] { LOCAL_MODULE, EDGE_MODULE, CLOUD_MODULE }) {
            app.addAppEdge(module, RESULT_ENDPOINT, 1, RESULT_BYTES, "TASK_RESULT", Tuple.DOWN, AppEdge.ACTUATOR);
            app.addTupleMapping(module, "TASK_INPUT", "TASK_RESULT", new FractionalSelectivity(1.0));
        }
        return app;
    }

    private static InstrumentedFogDevice createDevice(String name, long mips, int ram, long upBw, long downBw,
            int level, double busyPower, double idlePower, TaskRegistry registry) throws Exception {
        List<Pe> pes = new ArrayList<Pe>();
        pes.add(new Pe(0, new PeProvisionerOverbooking(mips)));
        PowerHost host = new PowerHost(FogUtils.generateEntityId(), new RamProvisionerSimple(ram),
                new BwProvisionerOverbooking(10000), 1000000, pes, new StreamOperatorScheduler(pes),
                new FogLinearPowerModel(busyPower, idlePower));
        List<Host> hosts = new ArrayList<Host>();
        hosts.add(host);
        FogDeviceCharacteristics characteristics = new FogDeviceCharacteristics("x86", "Linux", "Xen", host,
                10.0, 3.0, 0.05, 0.001, 0.0);
        InstrumentedFogDevice device = new InstrumentedFogDevice(name, characteristics,
                new AppModuleAllocationPolicy(hosts), new LinkedList<Storage>(), 10, upBw, downBw, 0, 0.0, registry);
        device.setLevel(level);
        return device;
    }

    private static final class TaskEmitter extends SimEntity {
        private final InstrumentedFogDevice local;
        private final InstrumentedFogDevice edge;
        private final TaskRegistry registry;
        TaskEmitter(String name, InstrumentedFogDevice local, InstrumentedFogDevice edge, TaskRegistry registry) {
            super(name);
            this.local = local;
            this.edge = edge;
            this.registry = registry;
        }
        @Override public void startEntity() { send(getId(), 5.0, FogEvents.EMIT_TUPLE); }
        @Override public void processEvent(SimEvent event) {
            if (event.getTag() == FogEvents.TUPLE_ACK) return;
            if (event.getTag() != FogEvents.EMIT_TUPLE)
                throw new IllegalStateException("unexpected task-emitter event " + event.getTag());
            registry.createAndDecide(edge.getObservedUtilization(), edge.getUplinkLatency());
            Tuple tuple = new Tuple(APP_ID, FogUtils.generateTupleId(), Tuple.UP, TASK_MI, TASK_PES, INPUT_BYTES,
                    RESULT_BYTES, new org.cloudbus.cloudsim.UtilizationModelFull(),
                    new org.cloudbus.cloudsim.UtilizationModelFull(), new org.cloudbus.cloudsim.UtilizationModelFull());
            tuple.setUserId(registry.userId);
            tuple.setTupleType("TASK_INPUT");
            tuple.setSrcModuleName("TASK_SOURCE");
            tuple.setDestModuleName(moduleFor(registry.requestedAction));
            tuple.setActualTupleId(tuple.getCloudletId());
            registry.bindTuple(tuple.getCloudletId(), tuple.getActualTupleId());
            sendNow(local.getId(), FogEvents.TUPLE_ARRIVAL, tuple);
        }
        @Override public void shutdownEntity() { }
    }

    private static String moduleFor(String action) {
        if ("Local".equals(action)) return LOCAL_MODULE;
        if ("Edge".equals(action)) return EDGE_MODULE;
        if ("Cloud".equals(action)) return CLOUD_MODULE;
        throw new IllegalArgumentException("unknown action " + action);
    }

    private static final class InstrumentedFogDevice extends FogDevice {
        private final TaskRegistry registry;
        InstrumentedFogDevice(String name, FogDeviceCharacteristics characteristics,
                AppModuleAllocationPolicy policy, List<Storage> storage, double interval, long up, long down,
                double uplinkLatency, double rate, TaskRegistry registry) throws Exception {
            super(name, characteristics, policy, storage, interval, up, down, uplinkLatency, rate);
            this.registry = registry;
        }
        @Override protected void sendUpFreeLink(Tuple tuple) {
            registry.transfer(tuple, getId(), getParentId(), "uplink", tuple.getCloudletFileSize());
            super.sendUpFreeLink(tuple);
        }
        @Override protected void sendDownFreeLink(Tuple tuple, int childId) {
            registry.transfer(tuple, getId(), childId, "downlink", tuple.getCloudletFileSize());
            super.sendDownFreeLink(tuple, childId);
        }
        @Override protected void executeTuple(SimEvent event, String moduleName) {
            registry.execution((Tuple) event.getData(), getId(), getName(), moduleName, lastUtilization);
            super.executeTuple(event, moduleName);
        }
        double getObservedUtilization() { return lastUtilization; }
    }

    private static final class ResultEndpoint extends Actuator {
        private final TaskRegistry registry;
        ResultEndpoint(String name, int userId, String appId, int gatewayId, double latency, TaskRegistry registry) {
            super(name, userId, appId, gatewayId, latency, null, RESULT_ENDPOINT, "");
            this.registry = registry;
        }
        @Override public void processEvent(SimEvent event) {
            if (event.getTag() == FogEvents.TUPLE_ARRIVAL) registry.terminal((Tuple) event.getData(), getName());
            super.processEvent(event);
        }
    }

    private static final class TaskRegistry {
        private final Options options;
        private final Trace trace;
        private final PythonAdapter python;
        final int userId;
        String taskId;
        long cloudletId = -1;
        int actualTupleId = -1;
        double creationTime;
        double edgeUtilization;
        double wanLatency;
        String requestedAction;
        String executedAction;
        String executingDevice;
        String executingModule;
        double executingUtilization = Double.NaN;
        long bandwidthBytes;
        int transferCount;
        boolean agentDecisionAccepted;
        boolean terminal;
        boolean failed;
        String failureReason;
        double terminalTime;
        double latencyMs;
        boolean deadlineMet;
        TaskRegistry(Options options, Trace trace, PythonAdapter python, int userId) {
            this.options = options; this.trace = trace; this.python = python; this.userId = userId;
        }
        void createAndDecide(double edgeUtilization, double wanLatency) {
            creationTime = CloudSim.clock();
            this.edgeUtilization = edgeUtilization;
            this.wanLatency = wanLatency;
            taskId = options.runId + ":task:1";
            Map<String, Object> features = mapOf("task_mi", TASK_MI, "wan_latency_ms", wanLatency,
                    "edge_utilization", edgeUtilization, "deadline_ms", options.deadlineMs);
            try {
                if (options.faultMode != null) {
                    trace.record("fault_injection", mapOf("task_id", taskId, "mode", options.faultMode,
                            "boundary", "agent_response", "sent_to_python", false));
                    throw new IOException("injected " + options.faultMode + " response");
                }
                JSONObject response = python.request(mapOf("protocol_version", "1.0", "type", "observation",
                        "task_id", taskId, "features", features, "available_actions",
                        Arrays.asList("Local", "Edge", "Cloud"), "sim_time_ms", creationTime));
                requireType(response, "action");
                String responseTask = asString(response.get("task_id"));
                String action = asString(response.get("action"));
                long actionId = asLong(response.get("action_id"));
                if (!taskId.equals(responseTask) || !validAction(action, actionId))
                    throw new IllegalStateException("invalid action correlation");
                requestedAction = action;
                agentDecisionAccepted = true;
                trace.record("decision", mapOf("task_id", taskId, "source", "agent", "action", action,
                        "action_id", actionId, "model_version", response.get("model_version"), "features", features));
            } catch (Exception error) {
                requestedAction = "Edge";
                failureReason = error.getClass().getSimpleName() + ": " + error.getMessage();
                trace.record("decision", mapOf("task_id", taskId, "source", "fallback_error", "action", requestedAction,
                        "reason", failureReason));
            }
        }
        void bindTuple(long cloudletId, int actualTupleId) {
            this.cloudletId = cloudletId; this.actualTupleId = actualTupleId;
            trace.record("task_created", mapOf("task_id", taskId, "cloudlet_id", cloudletId,
                    "actual_tuple_id", actualTupleId, "creation_sim_time_ms", creationTime,
                    "task_mi", TASK_MI, "task_pes", TASK_PES, "deadline_ms", options.deadlineMs));
        }
        void transfer(Tuple tuple, int from, int to, String direction, long bytes) {
            if (!matches(tuple)) return;
            bandwidthBytes += bytes; transferCount++;
            trace.record("transfer", mapOf("task_id", taskId, "actual_tuple_id", actualTupleId,
                    "from_device_id", from, "to_device_id", to, "direction", direction,
                    "bytes", bytes, "sim_time_ms", CloudSim.clock()));
        }
        void execution(Tuple tuple, int deviceId, String device, String module, double utilization) {
            if (!matches(tuple)) return;
            executingDevice = device + "#" + deviceId;
            executingModule = module;
            executingUtilization = utilization;
            executedAction = actionForModule(module);
            trace.record("execution", mapOf("task_id", taskId, "device", executingDevice, "module", module,
                    "action_executed", executedAction, "utilization_at_admission", utilization,
                    "sim_time_ms", CloudSim.clock()));
        }
        void terminal(Tuple tuple, String endpoint) {
            if (!matches(tuple) || terminal) return;
            terminal = true; terminalTime = CloudSim.clock(); latencyMs = terminalTime - creationTime;
            deadlineMet = latencyMs <= options.deadlineMs;
            trace.record("terminal", mapOf("task_id", taskId, "endpoint", endpoint,
                    "terminal_sim_time_ms", terminalTime, "latency_ms", latencyMs,
                    "deadline_met", deadlineMet, "bandwidth_bytes", bandwidthBytes,
                    "transfer_count", transferCount));
            try {
                if (agentDecisionAccepted) {
                    JSONObject ack = python.request(mapOf("protocol_version", "1.0", "type", "outcome",
                            "task_id", taskId, "action_executed", executedAction, "status", "completed",
                            "latency_ms", latencyMs, "deadline_met", deadlineMet,
                            "resource_metrics", mapOf("bandwidth_bytes", bandwidthBytes,
                                    "energy_joules", null, "executing_node_utilization", executingUtilization),
                            "terminal", true, "sim_time_ms", terminalTime));
                    requireType(ack, "outcome_ack");
                    if (!taskId.equals(asString(ack.get("task_id")))) throw new IllegalStateException("outcome ack task mismatch");
                    trace.record("outcome_ack", mapOf("task_id", taskId, "response", ack));
                    if ("train".equals(options.pythonMode)) {
                        JSONObject saved = python.request(mapOf("protocol_version", "1.0", "type", "save"));
                        requireType(saved, "saved");
                        trace.record("saved", mapOf("response", saved));
                    }
                } else {
                    trace.record("fallback_no_outcome", mapOf("task_id", taskId,
                            "reason", failureReason));
                }
                JSONObject shutdown = python.request(mapOf("protocol_version", "1.0", "type", "shutdown"));
                requireType(shutdown, "shutdown_ack");
                if (asLong(shutdown.get("orphaned_tasks")) != 0) throw new IllegalStateException("orphaned task");
                trace.record("shutdown_ack", mapOf("response", shutdown));
            } catch (Exception error) {
                failed = true; failureReason = "outcome lifecycle failed: " + error;
                trace.record("failure", mapOf("task_id", taskId, "reason", failureReason));
            }
            // Controller's normal MAX_SIMULATION_TIME handler calls System.exit(0).
            // This experiment owns its terminal criterion, so end the event loop now.
            CloudSim.abruptallyTerminate();
        }
        void assertConsistent() {
            if (executedAction == null || executingDevice == null || !requestedAction.equals(executedAction))
                throw new IllegalStateException("requested/executed routing mismatch: " + requestedAction + "/" + executedAction);
            if (Double.isNaN(latencyMs) || latencyMs < 0 || Double.isNaN(executingUtilization)
                    || executingUtilization < 0 || executingUtilization > 1) throw new IllegalStateException("invalid measurements");
        }
        private boolean matches(Tuple tuple) { return actualTupleId >= 0 && tuple.getActualTupleId() == actualTupleId; }
    }

    private static String actionForModule(String module) {
        if (LOCAL_MODULE.equals(module)) return "Local";
        if (EDGE_MODULE.equals(module)) return "Edge";
        if (CLOUD_MODULE.equals(module)) return "Cloud";
        throw new IllegalArgumentException("unexpected module " + module);
    }
    private static boolean validAction(String action, long id) {
        return ("Local".equals(action) && id == 0) || ("Edge".equals(action) && id == 1)
                || ("Cloud".equals(action) && id == 2);
    }
    private static String asString(Object value) { if (!(value instanceof String)) throw new IllegalStateException("expected string"); return (String) value; }
    private static long asLong(Object value) { if (!(value instanceof Number)) throw new IllegalStateException("expected number"); return ((Number) value).longValue(); }
    private static void requireType(JSONObject message, String type) { if (!type.equals(message.get("type"))) throw new IllegalStateException("expected " + type + ", got " + message); }

    private static final class PythonAdapter implements AutoCloseable {
        private static final String EOF = "__EOF__";
        private final Process process;
        private final BufferedWriter stdin;
        private final BlockingQueue<String> stdout = new LinkedBlockingQueue<String>();
        private final Thread stdoutThread;
        private final Thread stderrThread;
        private final Trace trace;
        private boolean shutdown;
        private PythonAdapter(Process process, Trace trace, Path stderrPath) throws IOException {
            this.process = process; this.trace = trace;
            stdin = new BufferedWriter(new OutputStreamWriter(process.getOutputStream(), StandardCharsets.UTF_8));
            stdoutThread = new Thread(() -> drainStdout(), "rl-jsonl-stdout");
            stderrThread = new Thread(() -> drainStderr(stderrPath), "rl-jsonl-stderr");
            stdoutThread.setDaemon(true); stderrThread.setDaemon(true); stdoutThread.start(); stderrThread.start();
        }
        static PythonAdapter start(Options options, Trace trace) throws Exception {
            List<String> command = new ArrayList<String>();
            command.add(options.pythonExe.toString()); command.add("-m"); command.add("rl_model.server");
            command.add("--config"); command.add(options.rlRoot.resolve("config/default.json").toString());
            command.add("--mode"); command.add(options.pythonMode);
            if ("baseline".equals(options.pythonMode)) { command.add("--policy"); command.add(options.pythonPolicy); }
            command.add("--model-out"); command.add(options.outputDir.resolve("python_model.json").toString());
            command.add("--log-dir"); command.add(options.outputDir.resolve("python_logs").toString());
            command.add("--artifacts-dir"); command.add(options.outputDir.resolve("python_artifacts").toString());
            command.add("--seed"); command.add("123");
            ProcessBuilder pb = new ProcessBuilder(command);
            pb.directory(options.rlRoot.toFile());
            pb.environment().put("PYTHONPATH", options.rlRoot.resolve("src").toString());
                    PythonAdapter adapter = new PythonAdapter(pb.start(), trace, options.outputDir.resolve("python_stderr.log"));
            JSONObject hello = adapter.request(mapOf("protocol_version", "1.0", "type", "hello", "run_id", options.runId,
                    "phase", "dev", "sim_seed", 123, "simulator", mapOf("name", "iFogSim2", "experiment", "RlOffloadingIntegrationExperiment")));
            requireType(hello, "hello_ack");
            trace.record("hello_ack", mapOf("response", hello, "command", command));
            return adapter;
        }
        JSONObject request(Map<String, Object> message) throws Exception {
            if (!process.isAlive()) throw new IOException("python process exited " + process.exitValue());
            String line = JSONObject.toJSONString(message);
            trace.record("python_send", mapOf("json", message));
            stdin.write(line); stdin.newLine(); stdin.flush();
            String response = stdout.poll(AGENT_TIMEOUT_MS, TimeUnit.MILLISECONDS);
            if (response == null) throw new IOException("agent timeout after " + AGENT_TIMEOUT_MS + " ms");
            if (EOF.equals(response)) throw new IOException("python stdout EOF");
            Object parsed = new JSONParser().parse(response);
            if (!(parsed instanceof JSONObject)) throw new IOException("python response is not JSON object");
            JSONObject object = (JSONObject) parsed;
            if (!"1.0".equals(object.get("protocol_version"))) throw new IOException("protocol version mismatch");
            trace.record("python_receive", mapOf("json", object));
            if ("error".equals(object.get("type"))) throw new IOException("python error " + object);
            if ("shutdown".equals(message.get("type")) && "shutdown_ack".equals(object.get("type"))) shutdown = true;
            return object;
        }
        private void drainStdout() {
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream(), StandardCharsets.UTF_8))) {
                String line; while ((line = reader.readLine()) != null) stdout.put(line);
            } catch (Exception ignored) { } finally { stdout.offer(EOF); }
        }
        private void drainStderr(Path target) {
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getErrorStream(), StandardCharsets.UTF_8));
                    BufferedWriter writer = Files.newBufferedWriter(target, StandardCharsets.UTF_8)) {
                String line; while ((line = reader.readLine()) != null) { writer.write(line); writer.newLine(); writer.flush(); }
            } catch (IOException ignored) { }
        }
        @Override public void close() throws Exception {
            try { stdin.close(); } catch (IOException ignored) { }
            if (!shutdown && process.isAlive()) process.destroy();
            process.waitFor(2, TimeUnit.SECONDS);
            if (process.isAlive()) process.destroyForcibly();
            trace.record("python_process_exit", mapOf("shutdown_ack_received", shutdown,
                    "exit_code", process.isAlive() ? null : process.exitValue()));
        }
    }

    private static final class Trace implements AutoCloseable {
        private final BufferedWriter writer;
        Trace(Path path) throws IOException { writer = Files.newBufferedWriter(path, StandardCharsets.UTF_8); }
        synchronized void record(String record, Map<String, Object> values) {
            try { Map<String, Object> row = new LinkedHashMap<String, Object>(); row.put("record", record); row.putAll(values);
                writer.write(JSONObject.toJSONString(row)); writer.newLine(); writer.flush(); }
            catch (IOException e) { throw new IllegalStateException("trace write failed", e); }
        }
        @Override public void close() throws IOException { writer.close(); }
    }

    private static final class Options {
        Path outputDir; Path pythonExe; Path rlRoot; String runId; String pythonMode; String pythonPolicy;
        String faultMode; double deadlineMs;
        static Options parse(String[] args) {
            Options options = new Options();
            Path cwd = new File(".").toPath().toAbsolutePath().normalize();
            options.outputDir = cwd.resolve("audit_output/integration_prototype/runs/latest");
            options.pythonExe = Path.of("C:/Program Files/Maxon Cinema 4D 2025/resource/modules/python/libs/win64/python.exe");
            options.rlRoot = cwd.resolve("team-work/Ayoub/rl_model/rl_model");
            options.runId = "rl-ifogsim-one-task"; options.pythonMode = "train"; options.pythonPolicy = "edge";
            options.deadlineMs = DEADLINE_MS;
            for (int i = 0; i < args.length; i += 2) {
                if (i + 1 >= args.length) throw new IllegalArgumentException("missing value for " + args[i]);
                String key = args[i], value = args[i + 1];
                if ("--output".equals(key)) options.outputDir = Path.of(value).toAbsolutePath();
                else if ("--python".equals(key)) options.pythonExe = Path.of(value).toAbsolutePath();
                else if ("--rl-root".equals(key)) options.rlRoot = Path.of(value).toAbsolutePath();
                else if ("--run-id".equals(key)) options.runId = value;
                else if ("--mode".equals(key)) options.pythonMode = value;
                else if ("--policy".equals(key)) options.pythonPolicy = value;
                else if ("--fault".equals(key)) options.faultMode = value;
                else if ("--deadline-ms".equals(key)) options.deadlineMs = Double.parseDouble(value);
                else throw new IllegalArgumentException("unknown option " + key);
            }
            if (!options.pythonMode.equals("train") && !options.pythonMode.equals("baseline"))
                throw new IllegalArgumentException("mode must be train or baseline");
            if (options.faultMode != null && !options.faultMode.equals("timeout")
                    && !options.faultMode.equals("malformed"))
                throw new IllegalArgumentException("fault must be timeout or malformed");
            if (Double.isNaN(options.deadlineMs) || Double.isInfinite(options.deadlineMs) || options.deadlineMs < 0)
                throw new IllegalArgumentException("deadline-ms must be finite and non-negative");
            return options;
        }
    }

    private static Map<String, Object> mapOf(Object... pairs) {
        if (pairs.length % 2 != 0) throw new IllegalArgumentException("key/value pairs expected");
        Map<String, Object> map = new LinkedHashMap<String, Object>();
        for (int i = 0; i < pairs.length; i += 2) map.put((String) pairs[i], pairs[i + 1]);
        return map;
    }
}
