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
 * Protocol-v2 integration smoke test for nine-action Python service. This first
 * simulator adapter intentionally advertises only the three full-placement
 * actions for indivisible tasks. Partial branch execution is a separate stage.
 */
public final class RlOffloadingV2IntegrationExperiment {
    private static final String APP_ID = "rl-offload-multi-task";
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

    private RlOffloadingV2IntegrationExperiment() { }

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
            "task_count", options.taskCount, "inter_arrival_ms", options.interArrivalMs,
            "task_mi", TASK_MI, "task_pes", TASK_PES, "deadline_ms", options.deadlineMs,
            "wan_latency_ms_configured", WAN_UPLINK_MS,
            "input_bytes", INPUT_BYTES, "result_bytes", RESULT_BYTES,
            "counted_links", "FogDevice parent-child uplink/downlink only",
            "created_at", Instant.now().toString()));
        new TaskEmitter("multi-task-emitter", local, edge, cloud, registry);
        CloudSim.startSimulation();
        CloudSim.stopSimulation();

        if (!registry.runCompleted || registry.failed || registry.completedCount != options.taskCount) {
            throw new IllegalStateException("simulation ended before all tasks completed: "
                    + registry.completedCount + "/" + options.taskCount + "; " + registry.failureReason);
        }
        if (options.faultMode == null && registry.acceptedDecisionCount != options.taskCount) {
            throw new IllegalStateException("not every task received an accepted agent decision");
        }
        registry.assertConsistent();
        trace.record("acceptance", registry.acceptanceFields());
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
        private final InstrumentedFogDevice cloud;
        private final TaskRegistry registry;
        private int emitted;

        TaskEmitter(String name, InstrumentedFogDevice local, InstrumentedFogDevice edge,
                InstrumentedFogDevice cloud, TaskRegistry registry) {
            super(name);
            this.local = local;
            this.edge = edge;
            this.cloud = cloud;
            this.registry = registry;
        }

        @Override public void startEntity() {
            send(getId(), 5.0, FogEvents.EMIT_TUPLE);
        }

        @Override public void processEvent(SimEvent event) {
            if (event.getTag() == FogEvents.TUPLE_ACK) return;
            if (event.getTag() != FogEvents.EMIT_TUPLE)
                throw new IllegalStateException("unexpected task-emitter event " + event.getTag());
            if (emitted >= registry.options.taskCount)
                throw new IllegalStateException("emitter received more task events than configured");

            int sequence = ++emitted;
            TaskRecord task = registry.createAndDecide(sequence, local.getObservedUtilization(),
                    edge.getObservedUtilization(), cloud.getObservedUtilization(), edge.getUplinkLatency());
            Tuple tuple = new Tuple(APP_ID, FogUtils.generateTupleId(), Tuple.UP, TASK_MI, TASK_PES, INPUT_BYTES,
                    RESULT_BYTES, new org.cloudbus.cloudsim.UtilizationModelFull(),
                    new org.cloudbus.cloudsim.UtilizationModelFull(), new org.cloudbus.cloudsim.UtilizationModelFull());
            tuple.setUserId(registry.userId);
            tuple.setTupleType("TASK_INPUT");
            tuple.setSrcModuleName("TASK_SOURCE");
            tuple.setDestModuleName(moduleFor(task.requestedAction));
            tuple.setActualTupleId(tuple.getCloudletId());
            registry.bindTuple(task, tuple.getCloudletId(), tuple.getActualTupleId());
            sendNow(local.getId(), FogEvents.TUPLE_ARRIVAL, tuple);

            if (emitted < registry.options.taskCount)
                send(getId(), registry.options.interArrivalMs, FogEvents.EMIT_TUPLE);
        }

        @Override public void shutdownEntity() { }
    }

    private static String moduleFor(String action) {
        if ("LOCAL".equals(action)) return LOCAL_MODULE;
        if ("EDGE_FULL".equals(action)) return EDGE_MODULE;
        if ("CLOUD_FULL".equals(action)) return CLOUD_MODULE;
        throw new IllegalArgumentException("unknown v2 full-placement action " + action);
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

    private static final class TaskRecord {
        final String taskId;
        final int sequence;
        final double creationTime;
        final double edgeUtilization;
        final double wanLatency;
        String requestedAction;
        String executedAction;
        String executingDevice;
        String executingModule;
        double executingUtilization = Double.NaN;
        long cloudletId = -1;
        int actualTupleId = -1;
        long bandwidthBytes;
        int transferCount;
        boolean agentDecisionAccepted;
        boolean executionObserved;
        boolean terminal;
        boolean outcomeAcknowledged;
        double terminalTime;
        double latencyMs;
        boolean deadlineMet;
        String failureReason;

        TaskRecord(String taskId, int sequence, double creationTime, double edgeUtilization, double wanLatency) {
            this.taskId = taskId;
            this.sequence = sequence;
            this.creationTime = creationTime;
            this.edgeUtilization = edgeUtilization;
            this.wanLatency = wanLatency;
        }
    }

    private static final class TaskRegistry {
        final Options options;
        private final Trace trace;
        private final PythonAdapter python;
        final int userId;
        private final Map<String, TaskRecord> tasksById = new LinkedHashMap<String, TaskRecord>();
        private final Map<Integer, TaskRecord> tasksByTupleId = new LinkedHashMap<Integer, TaskRecord>();
        int acceptedDecisionCount;
        int completedCount;
        boolean runCompleted;
        boolean failed;
        String failureReason;

        TaskRegistry(Options options, Trace trace, PythonAdapter python, int userId) {
            this.options = options;
            this.trace = trace;
            this.python = python;
            this.userId = userId;
        }

        TaskRecord createAndDecide(int sequence, double localUtilization, double edgeUtilization, double cloudUtilization, double wanLatency) {
            String taskId = options.runId + ":task:" + sequence;
            TaskRecord task = new TaskRecord(taskId, sequence, CloudSim.clock(), edgeUtilization, wanLatency);
            if (tasksById.put(taskId, task) != null)
                throw new IllegalStateException("duplicate task_id " + taskId);

            Map<String, Object> features = mapOf("task_mi", TASK_MI, "wan_latency_ms", wanLatency,
                    "local_utilization", localUtilization, "edge_utilization", edgeUtilization,
                    "cloud_utilization", cloudUtilization, "deadline_ms", options.deadlineMs,
                    "splittability", 0);
            List<Integer> feasible = Arrays.asList(0, 4, 8);
            Map<String, Object> constraints = mapOf("splittability", "INDIVISIBLE",
                    "local_available", true, "edge_available", true, "cloud_available", true);
            try {
                if (options.faultMode != null) {
                    trace.record("fault_injection", mapOf("task_id", taskId, "mode", options.faultMode,
                            "boundary", "agent_response", "sent_to_python", false));
                    throw new IOException("injected " + options.faultMode + " response");
                }
                JSONObject response = python.request(mapOf("protocol_version", "2.0", "type", "observation",
                        "task_id", taskId, "features", features, "available_actions",
                        Arrays.asList("LOCAL", "EDGE_FULL", "CLOUD_FULL"),
                        "task_constraints", constraints, "sim_time_ms", task.creationTime));
                requireType(response, "action");
                OffloadingActionV2.Action selected = OffloadingActionV2.validateResponse(
                        (Map<?, ?>) response, taskId, feasible);
                task.requestedAction = selected.wireName;
                task.agentDecisionAccepted = true;
                acceptedDecisionCount++;
                trace.record("decision", mapOf("task_id", taskId, "source", "agent", "action", selected.wireName,
                        "action_id", selected.id, "model_version", response.get("model_version"), "features", features,
                        "sim_time_ms", task.creationTime));
            } catch (Exception error) {
                task.requestedAction = "EDGE_FULL";
                task.failureReason = error.getClass().getSimpleName() + ": " + error.getMessage();
                trace.record("decision", mapOf("task_id", taskId, "source", "fallback_error", "action", task.requestedAction,
                        "reason", task.failureReason, "sim_time_ms", task.creationTime));
            }
            return task;
        }

        void bindTuple(TaskRecord task, long cloudletId, int actualTupleId) {
            if (tasksByTupleId.containsKey(actualTupleId))
                throw new IllegalStateException("duplicate actualTupleId " + actualTupleId);
            task.cloudletId = cloudletId;
            task.actualTupleId = actualTupleId;
            tasksByTupleId.put(actualTupleId, task);
            trace.record("task_created", mapOf("task_id", task.taskId, "cloudlet_id", cloudletId,
                    "actual_tuple_id", actualTupleId, "creation_sim_time_ms", task.creationTime,
                    "task_mi", TASK_MI, "task_pes", TASK_PES, "deadline_ms", options.deadlineMs));
        }

        private TaskRecord resolve(Tuple tuple) {
            TaskRecord task = tasksByTupleId.get(tuple.getActualTupleId());
            return task;
        }

        void transfer(Tuple tuple, int from, int to, String direction, long bytes) {
            TaskRecord task = resolve(tuple);
            if (task == null) return;
            task.bandwidthBytes += bytes;
            task.transferCount++;
            trace.record("transfer", mapOf("task_id", task.taskId, "actual_tuple_id", task.actualTupleId,
                    "from_device_id", from, "to_device_id", to, "direction", direction,
                    "bytes", bytes, "sim_time_ms", CloudSim.clock()));
        }

        void execution(Tuple tuple, int deviceId, String device, String module, double utilization) {
            TaskRecord task = resolve(tuple);
            if (task == null) return;
            if (task.executionObserved)
                throw new IllegalStateException("duplicate execution admission for " + task.taskId);
            task.executingDevice = device + "#" + deviceId;
            task.executingModule = module;
            task.executingUtilization = utilization;
            task.executedAction = actionForModule(module);
            task.executionObserved = true;
            trace.record("execution", mapOf("task_id", task.taskId, "actual_tuple_id", task.actualTupleId,
                    "device", task.executingDevice, "module", module, "action_executed", task.executedAction,
                    "utilization_at_admission", utilization, "sim_time_ms", CloudSim.clock()));
        }

        void terminal(Tuple tuple, String endpoint) {
            TaskRecord task = resolve(tuple);
            if (task == null) return;
            if (task.terminal)
                throw new IllegalStateException("duplicate terminal event for " + task.taskId);
            task.terminal = true;
            task.terminalTime = CloudSim.clock();
            task.latencyMs = task.terminalTime - task.creationTime;
            task.deadlineMet = task.latencyMs <= options.deadlineMs;
            trace.record("terminal", mapOf("task_id", task.taskId, "actual_tuple_id", task.actualTupleId,
                    "endpoint", endpoint, "terminal_sim_time_ms", task.terminalTime, "latency_ms", task.latencyMs,
                    "deadline_met", task.deadlineMet, "bandwidth_bytes", task.bandwidthBytes,
                    "transfer_count", task.transferCount));

            try {
                if (task.agentDecisionAccepted) {
                    JSONObject ack = python.request(mapOf("protocol_version", "2.0", "type", "outcome",
                            "task_id", task.taskId, "action_executed", task.executedAction, "status", "completed",
                            "latency_ms", task.latencyMs, "deadline_met", task.deadlineMet,
                            "resource_metrics", mapOf("bandwidth_bytes", task.bandwidthBytes,
                                    "energy_joules", null, "executing_node_utilization", task.executingUtilization),
                            "sim_time_ms", task.terminalTime));
                    requireType(ack, "outcome_ack");
                    if (!task.taskId.equals(asString(ack.get("task_id"))))
                        throw new IllegalStateException("outcome ack task mismatch");
                    task.outcomeAcknowledged = true;
                    trace.record("outcome_ack", mapOf("task_id", task.taskId, "response", ack,
                            "sim_time_ms", CloudSim.clock()));
                } else {
                    trace.record("fallback_no_outcome", mapOf("task_id", task.taskId,
                            "reason", task.failureReason));
                }
                completedCount++;
                if (completedCount == options.taskCount) finishRun();
            } catch (Exception error) {
                failed = true;
                failureReason = "outcome lifecycle failed for " + task.taskId + ": " + error;
                trace.record("failure", mapOf("task_id", task.taskId, "reason", failureReason));
                CloudSim.abruptallyTerminate();
            }
        }

        private void finishRun() throws Exception {
            if (completedCount != options.taskCount || tasksById.size() != options.taskCount)
                throw new IllegalStateException("run completion count does not match configured task set");
            for (TaskRecord task : tasksById.values()) {
                if (!task.terminal || (task.agentDecisionAccepted && !task.outcomeAcknowledged))
                    throw new IllegalStateException("task not reconciled before shutdown: " + task.taskId);
            }
            if ("train".equals(options.pythonMode) && acceptedDecisionCount > 0) {
                JSONObject saved = python.request(mapOf("protocol_version", "2.0", "type", "save"));
                requireType(saved, "saved");
                trace.record("saved", mapOf("response", saved));
            }
            JSONObject shutdown = python.request(mapOf("protocol_version", "2.0", "type", "shutdown"));
            requireType(shutdown, "shutdown_ack");
            if (asLong(shutdown.get("orphaned_tasks")) != 0)
                throw new IllegalStateException("Python shutdown reported orphaned tasks");
            trace.record("shutdown_ack", mapOf("response", shutdown, "completed_count", completedCount));
            runCompleted = true;
            CloudSim.abruptallyTerminate();
        }

        void assertConsistent() {
            if (tasksById.size() != options.taskCount || tasksByTupleId.size() != options.taskCount)
                throw new IllegalStateException("task/tuple registry cardinality mismatch");
            for (TaskRecord task : tasksById.values()) {
                if (task.actualTupleId < 0 || tasksByTupleId.get(task.actualTupleId) != task)
                    throw new IllegalStateException("tuple correlation mismatch for " + task.taskId);
                if (!task.executionObserved || task.executedAction == null || task.executingDevice == null
                        || !task.requestedAction.equals(task.executedAction))
                    throw new IllegalStateException("requested/executed routing mismatch for " + task.taskId);
                if (!task.terminal || (task.agentDecisionAccepted && !task.outcomeAcknowledged))
                    throw new IllegalStateException("incomplete task lifecycle for " + task.taskId);
                if (Double.isNaN(task.latencyMs) || task.latencyMs < 0 || Double.isNaN(task.executingUtilization)
                        || task.executingUtilization < 0 || task.executingUtilization > 1)
                    throw new IllegalStateException("invalid measurements for " + task.taskId);
            }
        }

        Map<String, Object> acceptanceFields() {
            Map<String, Object> fields = mapOf("status", "PASS", "task_count", options.taskCount,
                    "completed_count", completedCount, "accepted_decision_count", acceptedDecisionCount,
                    "task_ids", taskIds());
            if (options.taskCount == 1) {
                TaskRecord task = tasksById.values().iterator().next();
                fields.put("task_id", task.taskId);
                fields.put("requested_action", task.requestedAction);
                fields.put("action_executed", task.executedAction);
                fields.put("executing_device", task.executingDevice);
                fields.put("latency_ms", task.latencyMs);
                fields.put("bandwidth_bytes", task.bandwidthBytes);
                fields.put("deadline_met", task.deadlineMet);
                fields.put("decision_source", task.agentDecisionAccepted ? "agent" : "fallback_error");
            }
            return fields;
        }

        List<String> taskIds() {
            List<String> ids = new ArrayList<String>();
            for (TaskRecord task : tasksById.values()) ids.add(task.taskId);
            return ids;
        }
    }

    private static String actionForModule(String module) {
        if (LOCAL_MODULE.equals(module)) return "LOCAL";
        if (EDGE_MODULE.equals(module)) return "EDGE_FULL";
        if (CLOUD_MODULE.equals(module)) return "CLOUD_FULL";
        throw new IllegalArgumentException("unexpected module " + module);
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
            command.add(options.pythonExe.toString()); command.add("-m"); command.add("rl_model.server_v2");
            command.add("--config"); command.add(options.rlRoot.resolve("config/v2.json").toString());
            command.add("--mode"); command.add(options.pythonMode);
            if ("baseline".equals(options.pythonMode)) { command.add("--policy"); command.add(options.pythonPolicy); }
            command.add("--model-out"); command.add(options.outputDir.resolve("python_model.json").toString());

            ProcessBuilder pb = new ProcessBuilder(command);
            pb.directory(options.rlRoot.toFile());
            pb.environment().put("PYTHONPATH", options.rlRoot.resolve("src").toString());
                    PythonAdapter adapter = new PythonAdapter(pb.start(), trace, options.outputDir.resolve("python_stderr.log"));
            JSONObject hello = adapter.request(mapOf("protocol_version", "2.0", "type", "hello", "run_id", options.runId,
                    "phase", "dev", "sim_seed", 123, "simulator", mapOf("name", "iFogSim2", "experiment", "RlOffloadingV2IntegrationExperiment")));
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
            if (!"2.0".equals(object.get("protocol_version"))) throw new IOException("protocol version mismatch");
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
        Path outputDir;
        Path pythonExe;
        Path rlRoot;
        String runId;
        String pythonMode;
        String pythonPolicy;
        String faultMode;
        double deadlineMs;
        int taskCount = 1;
        double interArrivalMs = 1.0;

        static Options parse(String[] args) {
            Options options = new Options();
            Path cwd = new File(".").toPath().toAbsolutePath().normalize();
            options.outputDir = cwd.resolve("audit_output/integration_prototype/runs/latest");
            options.pythonExe = Path.of("C:/Users/DELL/AppData/Roaming/uv/python/cpython-3.15.0b1-windows-x86_64-none/python.exe");
            options.rlRoot = cwd.resolve("deliverables/08_RL_Model");
            options.runId = "rl-ifogsim-multi-task";
            options.pythonMode = "train";
            options.pythonPolicy = "edge";
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
                else if ("--tasks".equals(key)) options.taskCount = Integer.parseInt(value);
                else if ("--inter-arrival-ms".equals(key)) options.interArrivalMs = Double.parseDouble(value);
                else throw new IllegalArgumentException("unknown option " + key);
            }
            if (!options.pythonMode.equals("train") && !options.pythonMode.equals("baseline"))
                throw new IllegalArgumentException("mode must be train or baseline");
            if (options.faultMode != null && !options.faultMode.equals("timeout")
                    && !options.faultMode.equals("malformed"))
                throw new IllegalArgumentException("fault must be timeout or malformed");
            if (options.taskCount < 1 || options.taskCount > 1000)
                throw new IllegalArgumentException("tasks must be between 1 and 1000");
            if (options.faultMode != null && options.taskCount != 1)
                throw new IllegalArgumentException("fault injection currently requires exactly one task");
            if (Double.isNaN(options.interArrivalMs) || Double.isInfinite(options.interArrivalMs)
                    || options.interArrivalMs <= 0)
                throw new IllegalArgumentException("inter-arrival-ms must be finite and positive");
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
