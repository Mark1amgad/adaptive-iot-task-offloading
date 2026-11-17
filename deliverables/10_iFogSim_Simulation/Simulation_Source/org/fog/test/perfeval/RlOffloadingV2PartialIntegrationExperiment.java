package org.fog.test.perfeval;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
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

import org.cloudbus.cloudsim.Cloudlet;
import org.cloudbus.cloudsim.CloudletScheduler;
import org.cloudbus.cloudsim.Host;
import org.cloudbus.cloudsim.Log;
import org.cloudbus.cloudsim.Pe;
import org.cloudbus.cloudsim.Storage;
import org.cloudbus.cloudsim.UtilizationModelFull;
import org.cloudbus.cloudsim.Vm;
import org.cloudbus.cloudsim.core.CloudSim;
import org.cloudbus.cloudsim.core.CloudSimTags;
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
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;

/**
 * Protocol-v2 partial/full execution integration. Each invocation pins the
 * Python baseline to one catalogue action; the Java side still obtains and
 * validates the decision over the live JSONL protocol before emitting tuples.
 */
public final class RlOffloadingV2PartialIntegrationExperiment {
    private static final String APP_ID = "rl-offload-v2-partial";
    private static final String BRANCH_ENDPOINT = "BRANCH_RESULT_ENDPOINT";
    private static final String FINAL_ENDPOINT = "FINAL_RESULT_ENDPOINT";
    private static final long TASK_MI = 10003L;
    private static final long INPUT_BYTES = 12001L;
    private static final long OUTPUT_BYTES = 1001L;
    private static final long MERGE_MI = 1200L;
    private static final long MERGE_OUTPUT_BYTES = 64L;
    private static final long[] OUTPUT_PROFILES = new long[] {512L, 1001L, 2048L, 8192L};
    // Per-process experiment parameters are loaded from CLI options before simulation.
    // The runner launches one JVM per run, so these values cannot leak between scenarios.
    private static double DEADLINE_MS = 1000.0;
    private static double PARTITION_OVERHEAD_MS = 3.0;
    private static double MERGE_OVERHEAD_MS = 2.0;
    private static double WAN_LATENCY_MS = 45.0;

    // CloudSim time is seconds; protocol, workload and trace time fields are milliseconds.
    private static double simulationTimeMs() { return CloudSim.clock() * 1000.0; }
    private static final long AGENT_TIMEOUT_MS = 2000L;
    private static final String LOCAL_FULL = OffloadingActionV2ExecutionPlan.LOCAL_FULL_MODULE;
    private static final String EDGE_FULL = OffloadingActionV2ExecutionPlan.EDGE_FULL_MODULE;
    private static final String CLOUD_FULL = OffloadingActionV2ExecutionPlan.CLOUD_FULL_MODULE;
    private static final String MERGE_MODULE = OffloadingActionV2ExecutionPlan.MERGE_MODULE;

    private enum Events implements CloudSimTags { EMIT, DISPATCH_BRANCHES, BRANCH_RESULT, START_MERGE, MERGE_RESULT, WATCHDOG }

    private RlOffloadingV2PartialIntegrationExperiment() { }

    public static void main(String[] args) {
        try {
            Options options = Options.parse(args);
            DEADLINE_MS = options.deadlineMs;
            PARTITION_OVERHEAD_MS = options.partitionOverheadMs;
            MERGE_OVERHEAD_MS = options.mergeOverheadMs;
            WAN_LATENCY_MS = options.wanLatencyMs;
            Files.createDirectories(options.output);
            try (Trace trace = new Trace(options.output.resolve("partial_trace.jsonl"));
                 PythonAdapter python = PythonAdapter.start(options, trace)) {
                run(options, trace, python);
            }
        } catch (Throwable error) {
            error.printStackTrace(System.err);
            System.exit(2);
        }
    }

    private static void run(Options options, Trace trace, PythonAdapter python) throws Exception {
        Log.disable();
        CloudSim.init(1, Calendar.getInstance(), false);
        FogBroker broker = new FogBroker("v2-partial-broker");
        TaskRegistry registry = new TaskRegistry(options, trace, python, broker.getId());

        InstrumentedFogDevice cloud = createDevice("cloud", 44800, 40000, 100000, 100000,
                0, 16 * 103, 16 * 83.25, registry);
        cloud.setParentId(-1);
        InstrumentedFogDevice edge = createDevice("edge", 2800, 4000, 10000, 10000,
                1, 107.339, 83.4333, registry);
        edge.setParentId(cloud.getId());
        edge.setUplinkLatency(WAN_LATENCY_MS / 1000.0);
        InstrumentedFogDevice local = createDevice("local", 1000, 2000, 10000, 10000,
                2, 87.53, 82.44, registry);
        local.setParentId(edge.getId());
        local.setUplinkLatency(2.0 / 1000.0);

        List<FogDevice> devices = Arrays.<FogDevice>asList(cloud, edge, local);
        TaskCoordinator coordinator = new TaskCoordinator("v2-partial-coordinator", registry, local);
        BranchEndpoint branchEndpoint = new BranchEndpoint("v2-branch-endpoint", broker.getId(),
                APP_ID, local.getId(), coordinator);
        FinalEndpoint finalEndpoint = new FinalEndpoint("v2-final-endpoint", broker.getId(),
                APP_ID, local.getId(), coordinator);
        List<Actuator> actuators = Arrays.<Actuator>asList(branchEndpoint, finalEndpoint);

        Application app = createApplication(broker.getId());
        ModuleMapping mapping = ModuleMapping.createModuleMapping();
        mapModules(mapping);
        Controller controller = new Controller("v2-partial-controller", devices,
                Collections.emptyList(), actuators);
        controller.submitApplication(app, new ModulePlacementMapping(devices, app, mapping));

        trace.record("config", mapOf("run_id", options.runId,
                "task_count", options.tasks, "mode", options.mode,
                "action_policy", options.action != null ? options.action.wireName : (options.policy != null ? options.policy : ("train".equals(options.mode) ? "learned_train" : "learned_eval")),
                "workload_file", options.workloadFile == null ? "legacy_constant_profile" : options.workloadFile.toString(),
                "inter_arrival_mode", options.workloadFile == null ? "fixed" : "per_task_seeded",
                "partition_overhead_ms", PARTITION_OVERHEAD_MS, "merge_overhead_ms", MERGE_OVERHEAD_MS,
                "deadline_default_ms", DEADLINE_MS, "watchdog_ms", options.watchdogMs,
                "wan_latency_ms", WAN_LATENCY_MS, "output_profiles_bytes", Arrays.toString(OUTPUT_PROFILES),
                "created_at", Instant.now().toString()));
        new TaskEmitter("v2-partial-emitter", local, edge, cloud, registry);
        CloudSim.startSimulation();
        CloudSim.stopSimulation();

        if (!registry.runCompleted || registry.failed
                || (!options.evaluationMode && registry.failedTaskCount > 0)
                || registry.completedCount != options.tasks)
            throw new IllegalStateException("v2 partial run did not reconcile all tasks: "
                    + registry.completedCount + "/" + options.tasks + "; failed_tasks="
                    + registry.failedTaskCount + "; " + registry.failureReason);
        registry.assertConsistent();
        trace.record("acceptance", registry.acceptanceFields());
        System.out.println(options.evaluationMode
                ? "V2_EVALUATION_STATUS=PASS" : "V2_PARTIAL_STATUS=PASS");
        System.out.println("MODE=" + options.mode);
        if (options.action != null) System.out.println("ACTION=" + options.action.wireName);
        System.out.println("TASKS=" + registry.completedCount);
        System.out.println("TRACE=" + options.output.resolve("partial_trace.jsonl"));
    }

    private static Application createApplication(int userId) {
        Application app = Application.createApplication(APP_ID, userId);
        addWorker(app, LOCAL_FULL, "TASK_INPUT", "LOCAL_FULL_RESULT", -1, true);
        addWorker(app, EDGE_FULL, "TASK_INPUT", "EDGE_FULL_RESULT", -1, true);
        addWorker(app, CLOUD_FULL, "TASK_INPUT", "CLOUD_FULL_RESULT", -1, true);
        for (int percent : new int[] {25, 50, 75}) {
            String suffix = Integer.toString(percent);
            addWorker(app, "local_partial_" + suffix, "LOCAL_PARTIAL_INPUT",
                    "LOCAL_PARTIAL_RESULT_" + suffix, percent, true);
            addWorker(app, "edge_partial_" + suffix, "EDGE_PARTIAL_INPUT",
                    "EDGE_PARTIAL_RESULT_" + suffix, percent, false);
            addWorker(app, "cloud_partial_" + suffix, "CLOUD_PARTIAL_INPUT",
                    "CLOUD_PARTIAL_RESULT_" + suffix, percent, false);
        }
        app.addAppModule(MERGE_MODULE, 64, 1000, 10000);
        app.addAppEdge(MERGE_MODULE, FINAL_ENDPOINT, 1, MERGE_OUTPUT_BYTES,
                "MERGED_RESULT", Tuple.DOWN, AppEdge.ACTUATOR);
        app.addTupleMapping(MERGE_MODULE, "MERGE_INPUT", "MERGED_RESULT",
                new FractionalSelectivity(1.0));
        return app;
    }

    /** One module per tier/action; distinct typed edges carry each payload-size profile. */
    private static void addWorker(Application app, String module, String inputType,
            String outputType, int remotePercent, boolean localBranch) {
        app.addAppModule(module, 64, 1000, 10000);
        for (long totalOutput : OUTPUT_PROFILES) {
            long branchOutput;
            if (remotePercent < 0) branchOutput = totalOutput;
            else {
                long remoteOutput = Math.round(totalOutput * remotePercent / 100.0);
                branchOutput = localBranch ? totalOutput - remoteOutput : remoteOutput;
            }
            String profile = tupleProfileSuffix(totalOutput);
            String typedInput = inputType + profile;
            String typedOutput = outputType + profile;
            app.addAppEdge(module, BRANCH_ENDPOINT, 1, branchOutput,
                    typedOutput, Tuple.DOWN, AppEdge.ACTUATOR);
            app.addTupleMapping(module, typedInput, typedOutput, new FractionalSelectivity(1.0));
        }
    }

    private static void mapModules(ModuleMapping mapping) {
        mapping.addModuleToDevice(LOCAL_FULL, "local");
        mapping.addModuleToDevice(EDGE_FULL, "edge");
        mapping.addModuleToDevice(CLOUD_FULL, "cloud");
        mapping.addModuleToDevice(MERGE_MODULE, "local");
        for (int percent : new int[] {25, 50, 75}) {
            String suffix = Integer.toString(percent);
            mapping.addModuleToDevice("local_partial_" + suffix, "local");
            mapping.addModuleToDevice("edge_partial_" + suffix, "edge");
            mapping.addModuleToDevice("cloud_partial_" + suffix, "cloud");
        }
    }

    private static String tupleProfileSuffix(long bytes) {
        return bytes == OUTPUT_BYTES ? "" : "_O" + bytes;
    }

    private static String outputProfile(long bytes) {
        return bytes == OUTPUT_BYTES ? "" : "o" + bytes;
    }

    private static InstrumentedFogDevice createDevice(String name, long mips, int ram,
            long upBw, long downBw, int level, double busyPower, double idlePower,
            TaskRegistry registry) throws Exception {
        List<Pe> pes = new ArrayList<Pe>();
        pes.add(new Pe(0, new PeProvisionerOverbooking(mips)));
        PowerHost host = new PowerHost(FogUtils.generateEntityId(),
                new RamProvisionerSimple(ram), new BwProvisionerOverbooking(10000),
                1000000, pes, new StreamOperatorScheduler(pes),
                new FogLinearPowerModel(busyPower, idlePower));
        List<Host> hosts = new ArrayList<Host>();
        hosts.add(host);
        FogDeviceCharacteristics characteristics = new FogDeviceCharacteristics(
                "x86", "Linux", "Xen", host, 10.0, 3.0, 0.05, 0.001, 0.0);
        InstrumentedFogDevice device = new InstrumentedFogDevice(name, characteristics,
                new AppModuleAllocationPolicy(hosts), new LinkedList<Storage>(),
                0.01, upBw, downBw, 0, 0.0, registry);
        device.setLevel(level);
        return device;
    }

    private static final class TaskEmitter extends SimEntity {
        private final InstrumentedFogDevice local, edge, cloud;
        private final TaskRegistry registry;
        private int emitted;
        private String lastRegimeId;
        private int lastRegimeIndex = -1;
        TaskEmitter(String name, InstrumentedFogDevice local, InstrumentedFogDevice edge,
                InstrumentedFogDevice cloud, TaskRegistry registry) {
            super(name); this.local = local; this.edge = edge; this.cloud = cloud; this.registry = registry;
        }
        @Override public void startEntity() { send(getId(), 5.0, Events.EMIT); }
        @Override public void processEvent(SimEvent event) {
            if (event.getTag() == FogEvents.TUPLE_ACK) return;
            if (event.getTag() == Events.DISPATCH_BRANCHES) {
                dispatchBranches((TaskRecord) event.getData());
                return;
            }
            if (event.getTag() != Events.EMIT) throw new IllegalStateException("unexpected emitter event");
            if (emitted >= registry.options.tasks) throw new IllegalStateException("excess task emission");
            int sequence = ++emitted;
            WorkloadTask workload = registry.options.workload.get(sequence - 1);
            edge.setUplinkLatency(workload.wanLatencyMs / 1000.0);
            if (!workload.regimeId.equals(lastRegimeId) || workload.regimeIndex != lastRegimeIndex) {
                registry.trace.record("regime_transition", mapOf("task_sequence", sequence,
                        "regime_id", workload.regimeId, "regime_index", workload.regimeIndex,
                        "wan_latency_ms", workload.wanLatencyMs, "sim_time_ms", simulationTimeMs()));
                lastRegimeId = workload.regimeId;
                lastRegimeIndex = workload.regimeIndex;
            }
            TaskRecord task = registry.decide(sequence, local.getObservedUtilization(),
                    edge.getObservedUtilization(), cloud.getObservedUtilization(), workload);
            if (task.action.isPartial()) {
                registry.trace.record("partition_overhead_started", mapOf("task_id", task.taskId,
                        "duration_ms", PARTITION_OVERHEAD_MS, "sim_time_ms", simulationTimeMs()));
                send(getId(), PARTITION_OVERHEAD_MS / 1000.0, Events.DISPATCH_BRANCHES, task);
            } else {
                dispatchBranches(task);
            }
            if (emitted < registry.options.tasks) {
                double nextGap = registry.options.workload.get(emitted).arrivalGapMs;
                send(getId(), nextGap / 1000.0, Events.EMIT);
            }
        }
        private void dispatchBranches(TaskRecord task) {
            if (task.action.isPartial())
                registry.trace.record("partition_overhead_completed", mapOf("task_id", task.taskId,
                        "sim_time_ms", simulationTimeMs()));
            for (OffloadingActionV2ExecutionPlan.Branch branch : task.plan.branches) {
                Tuple tuple = new Tuple(APP_ID, FogUtils.generateTupleId(), Tuple.UP,
                        branch.mi, 1, branch.inputBytes, branch.outputBytes,
                        new UtilizationModelFull(), new UtilizationModelFull(), new UtilizationModelFull());
                tuple.setUserId(registry.userId);
                tuple.setTupleType(branch.tupleType);
                tuple.setSrcModuleName("TASK_SOURCE");
                tuple.setDestModuleName(branch.module);
                tuple.setActualTupleId(tuple.getCloudletId());
                registry.registerBranch(task, branch, tuple);
                if (task.sequence == 1 && branch.name.equals(registry.options.dropBranch)) {
                    registry.trace.record("fault_injection", mapOf("task_id", task.taskId,
                            "branch", branch.name, "fault", "drop_branch_before_tuple_arrival"));
                } else {
                    sendNow(local.getId(), FogEvents.TUPLE_ARRIVAL, tuple);
                }
            }
        }
        @Override public void shutdownEntity() { }
    }

    private static final class InstrumentedFogDevice extends FogDevice {
        private final TaskRegistry registry;
        InstrumentedFogDevice(String name, FogDeviceCharacteristics characteristics,
                AppModuleAllocationPolicy policy, List<Storage> storage,
                double interval, long up, long down, double uplinkLatency, double rate,
                TaskRegistry registry) throws Exception {
            super(name, characteristics, policy, storage, interval, up, down, uplinkLatency, rate);
            this.registry = registry;
        }
        @Override protected void sendUpFreeLink(Tuple tuple) {
            registry.transfer(tuple, getName(), "uplink", tuple.getCloudletFileSize());
            super.sendUpFreeLink(tuple);
        }
        @Override protected void sendDownFreeLink(Tuple tuple, int childId) {
            registry.transfer(tuple, getName(), "downlink", tuple.getCloudletFileSize());
            super.sendDownFreeLink(tuple, childId);
        }
        @Override protected void executeTuple(SimEvent event, String moduleName) {
            registry.execution((Tuple) event.getData(), getName(), moduleName, getObservedUtilization());
            super.executeTuple(event, moduleName);
        }

        /**
         * Current workload demand as a fraction of device MIPS. FogDevice.lastUtilization
         * is an allocated-MIPS/VM-reservation ratio, not instantaneous CPU demand; it can
         * equal 1.0 while no task Cloudlet is running. Build the snapshot from active
         * Cloudlets and their currently allocated MIPS instead.
         */
        double getObservedUtilization() {
            double activeMips = 0.0;
            double now = CloudSim.clock();
            for (Vm vm : getHost().getVmList()) {
                CloudletScheduler scheduler = vm.getCloudletScheduler();
                for (Cloudlet cloudlet : scheduler.<Cloudlet>getCloudletExecList()) {
                    double utilization = cloudlet.getUtilizationOfCpu(now);
                    double allocatedMips = scheduler.getTotalCurrentAllocatedMipsForCloudlet(cloudlet, now);
                    activeMips += Math.max(0.0, allocatedMips) * Math.max(0.0, utilization);
                }
            }
            double totalMips = getHost().getTotalMips();
            if (totalMips <= 0.0) return 1.0;
            return Math.max(0.0, Math.min(1.0, activeMips / totalMips));
        }
    }

    private static final class BranchEndpoint extends Actuator {
        private final TaskCoordinator coordinator;
        BranchEndpoint(String name, int userId, String appId, int gatewayId,
                TaskCoordinator coordinator) {
            super(name, userId, appId, gatewayId, 1.0, null, BRANCH_ENDPOINT, "");
            this.coordinator = coordinator;
        }
        @Override public void processEvent(SimEvent event) {
            if (event.getTag() == FogEvents.TUPLE_ARRIVAL)
                coordinator.acceptBranch((Tuple) event.getData());
            super.processEvent(event);
        }
    }

    private static final class FinalEndpoint extends Actuator {
        private final TaskCoordinator coordinator;
        FinalEndpoint(String name, int userId, String appId, int gatewayId,
                TaskCoordinator coordinator) {
            super(name, userId, appId, gatewayId, 1.0, null, FINAL_ENDPOINT, "");
            this.coordinator = coordinator;
        }
        @Override public void processEvent(SimEvent event) {
            if (event.getTag() == FogEvents.TUPLE_ARRIVAL)
                coordinator.acceptMerge((Tuple) event.getData());
            super.processEvent(event);
        }
    }

    private static final class TaskCoordinator extends SimEntity {
        private final TaskRegistry registry;
        private final InstrumentedFogDevice local;
        TaskCoordinator(String name, TaskRegistry registry, InstrumentedFogDevice local) {
            super(name); this.registry = registry; this.local = local;
        }
        @Override public void startEntity() {
            double arrivalSpanMs = 0.0;
            for (int i = 1; i < registry.options.workload.size(); i++)
                arrivalSpanMs += registry.options.workload.get(i).arrivalGapMs;
            // First task is intentionally emitted after a 5-second simulator warm-up.
            double horizonSeconds = 5.0 + (arrivalSpanMs + registry.options.watchdogMs) / 1000.0;
            registry.trace.record("watchdog_scheduled",
                    mapOf("horizon_sim_time_ms", horizonSeconds * 1000.0));
            send(getId(), horizonSeconds, Events.WATCHDOG);
        }
        void acceptBranch(Tuple tuple) { sendNow(getId(), Events.BRANCH_RESULT, tuple); }
        void acceptMerge(Tuple tuple) { sendNow(getId(), Events.MERGE_RESULT, tuple); }
        @Override public void processEvent(SimEvent event) {
            if (event.getTag() == FogEvents.TUPLE_ACK) return;
            if (event.getTag() == Events.BRANCH_RESULT) {
                TaskRecord task = registry.acceptBranchResult((Tuple) event.getData());
                if (task != null) {
                    registry.trace.record("merge_overhead_started", mapOf("task_id", task.taskId,
                            "duration_ms", MERGE_OVERHEAD_MS, "sim_time_ms", simulationTimeMs()));
                    send(getId(), MERGE_OVERHEAD_MS / 1000.0, Events.START_MERGE, task);
                }
                if (registry.completedCount == registry.options.tasks) registry.finishRun();
            } else if (event.getTag() == Events.START_MERGE) {
                TaskRecord task = (TaskRecord) event.getData();
                registry.trace.record("merge_overhead_completed", mapOf("task_id", task.taskId,
                        "sim_time_ms", simulationTimeMs()));
                Tuple merge = registry.beginMerge(task);
                sendNow(local.getId(), FogEvents.TUPLE_ARRIVAL, merge);
            } else if (event.getTag() == Events.MERGE_RESULT) {
                registry.completeMerge((Tuple) event.getData());
                if (registry.completedCount == registry.options.tasks) registry.finishRun();
            } else if (event.getTag() == Events.WATCHDOG) {
                registry.trace.record("watchdog_fired", mapOf("sim_time_ms", simulationTimeMs()));
                registry.failOutstanding("execution_horizon_exceeded");
                if (registry.completedCount == registry.options.tasks) registry.finishRun();
            } else throw new IllegalStateException("unexpected coordinator event " + event.getTag());
        }
        @Override public void shutdownEntity() { }
    }

    private static final class Branch {
        final String name, module, tier;
        final int tupleId;
        final long mi, inputBytes, outputBytes;
        double executionStart = Double.NaN, resultArrival = Double.NaN, utilization = Double.NaN;
        String executingNode;
        Branch(String name, String module, String tier, int tupleId,
                long mi, long inputBytes, long outputBytes) {
            this.name = name; this.module = module; this.tier = tier; this.tupleId = tupleId;
            this.mi = mi; this.inputBytes = inputBytes; this.outputBytes = outputBytes;
        }
    }

    private static final class BranchRef {
        final TaskRecord task;
        final Branch branch;
        BranchRef(TaskRecord task, Branch branch) { this.task = task; this.branch = branch; }
    }

    private static final class WorkloadTask {
        final int sequence;
        final long taskMi, inputBytes, outputBytes, mergeMi, mergeOutputBytes;
        final double deadlineMs, arrivalGapMs;
        final String urgencyClass, splittability, partitionModelId, regimeId;
        final double wanLatencyMs;
        final int regimeIndex;
        WorkloadTask(int sequence, long taskMi, long inputBytes, long outputBytes,
                long mergeMi, long mergeOutputBytes, double deadlineMs, double arrivalGapMs,
                String urgencyClass, String splittability, String partitionModelId) {
            this(sequence, taskMi, inputBytes, outputBytes, mergeMi, mergeOutputBytes,
                    deadlineMs, arrivalGapMs, urgencyClass, splittability, partitionModelId,
                    "stable", 0, WAN_LATENCY_MS);
        }
        WorkloadTask(int sequence, long taskMi, long inputBytes, long outputBytes,
                long mergeMi, long mergeOutputBytes, double deadlineMs, double arrivalGapMs,
                String urgencyClass, String splittability, String partitionModelId,
                String regimeId, int regimeIndex, double wanLatencyMs) {
            this.sequence = sequence; this.taskMi = taskMi; this.inputBytes = inputBytes;
            this.outputBytes = outputBytes; this.mergeMi = mergeMi; this.mergeOutputBytes = mergeOutputBytes;
            this.deadlineMs = deadlineMs; this.arrivalGapMs = arrivalGapMs;
            this.urgencyClass = urgencyClass; this.splittability = splittability;
            this.partitionModelId = partitionModelId; this.regimeId = regimeId;
            this.regimeIndex = regimeIndex; this.wanLatencyMs = wanLatencyMs;
        }
        boolean divisible() { return "DATA_PARALLEL_DIVISIBLE".equals(splittability); }
        String outputProfile() { return outputBytes == OUTPUT_BYTES ? null : "o" + outputBytes; }
        static WorkloadTask parse(String line, int expectedSequence) throws Exception {
            Object parsed = new JSONParser().parse(line);
            if (!(parsed instanceof JSONObject)) throw new IllegalArgumentException("workload row must be a JSON object");
            JSONObject row = (JSONObject) parsed;
            int sequence = (int) number(row.get("sequence"));
            long taskMi = number(row.get("task_mi"));
            long inputBytes = number(row.get("input_bytes"));
            long outputBytes = number(row.get("output_bytes"));
            long mergeMi = number(row.get("merge_mi"));
            long mergeOutputBytes = number(row.get("merge_output_bytes"));
            double deadline = decimal(row.get("deadline_ms"));
            double gap = decimal(row.get("arrival_gap_ms"));
            String urgency = String.valueOf(row.get("urgency_class"));
            String split = String.valueOf(row.get("splittability"));
            Object partitionValue = row.get("partition_model_id");
            String partition = partitionValue == null ? null : String.valueOf(partitionValue);
            String regimeId = row.get("regime_id") == null ? "stable" : String.valueOf(row.get("regime_id"));
            int regimeIndex = row.get("regime_index") == null ? 0 : (int) number(row.get("regime_index"));
            double wanLatency = row.get("wan_latency_ms") == null ? WAN_LATENCY_MS : decimal(row.get("wan_latency_ms"));
            if (sequence != expectedSequence || taskMi <= 0 || inputBytes <= 0 || deadline <= 0
                    || gap < 0 || mergeOutputBytes <= 0 || !Double.isFinite(deadline) || !Double.isFinite(gap)
                    || regimeId.trim().isEmpty() || regimeIndex < 0 || !Double.isFinite(wanLatency) || wanLatency < 0)
                throw new IllegalArgumentException("invalid workload values at sequence " + expectedSequence);
            if (outputBytes != 512 && outputBytes != OUTPUT_BYTES && outputBytes != 2048 && outputBytes != 8192)
                throw new IllegalArgumentException("unsupported output_bytes at sequence " + sequence);
            if (outputBytes != OUTPUT_BYTES && !("o" + outputBytes).equals(String.valueOf(row.get("output_profile"))))
                throw new IllegalArgumentException("output_profile does not match output_bytes at sequence " + sequence);
            if (!("critical".equals(urgency) || "high".equals(urgency) || "normal".equals(urgency)))
                throw new IllegalArgumentException("invalid urgency_class at sequence " + sequence);
            if (!("INDIVISIBLE".equals(split) || "DATA_PARALLEL_DIVISIBLE".equals(split)))
                throw new IllegalArgumentException("invalid splittability at sequence " + sequence);
            if ("INDIVISIBLE".equals(split) && (partition != null || mergeMi != 0))
                throw new IllegalArgumentException("indivisible task must not declare partition/merge work");
            if ("DATA_PARALLEL_DIVISIBLE".equals(split) && (partition == null || partition.isEmpty() || mergeMi <= 0))
                throw new IllegalArgumentException("divisible task requires partition model and positive merge MI");
            return new WorkloadTask(sequence, taskMi, inputBytes, outputBytes, mergeMi,
                    mergeOutputBytes, deadline, gap, urgency, split, partition,
                    regimeId, regimeIndex, wanLatency);
        }
    }

    private static double decimal(Object value) {
        if (!(value instanceof Number)) throw new IllegalArgumentException("expected numeric workload value: " + value);
        return ((Number) value).doubleValue();
    }

    private static final class TaskRecord {
        final String taskId;
        final int sequence;
        final double creationTime;
        final OffloadingActionV2.Action action;
        final OffloadingActionV2ExecutionPlan plan;
        final WorkloadTask workload;
        final Map<String, Branch> branches = new LinkedHashMap<String, Branch>();
        int resultBranches;
        long bandwidthBytes;
        int transferCount;
        boolean mergeStarted, terminal, outcomeAck;
        double terminalTime = Double.NaN, latency = Double.NaN;
        String failureReason;
        TaskRecord(String taskId, int sequence, double creationTime,
                OffloadingActionV2.Action action, OffloadingActionV2ExecutionPlan plan, WorkloadTask workload) {
            this.taskId = taskId; this.sequence = sequence; this.creationTime = creationTime;
            this.action = action; this.plan = plan; this.workload = workload;
        }
    }

    private static final class TaskRegistry {
        final Options options;
        final Trace trace;
        final PythonAdapter python;
        final int userId;
        final Map<String, TaskRecord> tasks = new LinkedHashMap<String, TaskRecord>();
        final Map<Integer, BranchRef> tupleOwners = new LinkedHashMap<Integer, BranchRef>();
        int completedCount, acceptedDecisions, failedTaskCount;
        boolean failed, runCompleted;
        String failureReason = "";
        TaskRegistry(Options options, Trace trace, PythonAdapter python, int userId) {
            this.options = options; this.trace = trace; this.python = python; this.userId = userId;
        }

        TaskRecord decide(int sequence, double localUtil, double edgeUtil, double cloudUtil, WorkloadTask workload) {
            String taskId = options.runId + ":task:" + sequence;
            OffloadingActionV2ExecutionPlan plan = null;
            TaskRecord task;
            try {
                Map<String, Object> features = mapOf("task_mi", workload.taskMi,
                        "input_bytes", workload.inputBytes, "output_bytes", workload.outputBytes,
                        "wan_latency_ms", workload.wanLatencyMs, "local_utilization", localUtil,
                        "edge_utilization", edgeUtil, "cloud_utilization", cloudUtil,
                        "deadline_ms", workload.deadlineMs,
                        "splittability", workload.divisible() ? 1 : 0);
                List<Integer> mask = OffloadingActionV2.legalActionIds(
                        workload.splittability, workload.partitionModelId, true, true, true);
                Map<String, Object> constraints = mapOf("splittability", workload.splittability,
                        "local_available", true, "edge_available", true, "cloud_available", true,
                        "urgency_class", workload.urgencyClass);
                if (workload.divisible()) {
                    constraints.put("partition_model_id", workload.partitionModelId);
                    constraints.put("partition_overhead_ms", PARTITION_OVERHEAD_MS);
                    constraints.put("merge_overhead_ms", MERGE_OVERHEAD_MS);
                }
                List<Map<String, Object>> localEdgePath = Arrays.asList(
                        mapOf("bandwidth_bytes_per_second", 10000.0, "latency_ms", 2.0));
                List<Map<String, Object>> cloudUplinkPath = Arrays.asList(
                        mapOf("bandwidth_bytes_per_second", 10000.0, "latency_ms", 2.0),
                        mapOf("bandwidth_bytes_per_second", 10000.0, "latency_ms", workload.wanLatencyMs));
                List<Map<String, Object>> cloudDownlinkPath = Arrays.asList(
                        mapOf("bandwidth_bytes_per_second", 100000.0, "latency_ms", workload.wanLatencyMs),
                        mapOf("bandwidth_bytes_per_second", 10000.0, "latency_ms", 2.0));
                Map<String, Object> riskContext = mapOf(
                        "remaining_deadline_ms", workload.deadlineMs,
                        "partition_overhead_ms", workload.divisible() ? PARTITION_OVERHEAD_MS : 0.0,
                        "merge_overhead_ms", workload.divisible() ? MERGE_OVERHEAD_MS : 0.0,
                        "merge_compute_mi", workload.mergeMi,
                        "merge_queue_wait_ms", 0.0,
                        "queue_wait_basis", "zero_predecision_queue_estimate; residual calibration captures subsequent queueing and contention",
                        "resources", mapOf(
                                "LOCAL", mapOf("compute_mips", 1000.0, "utilization", localUtil,
                                        "queue_wait_ms", 0.0),
                                "EDGE", mapOf("compute_mips", 2800.0, "utilization", edgeUtil,
                                        "queue_wait_ms", 0.0, "uplink_path", localEdgePath,
                                        "downlink_path", localEdgePath),
                                "CLOUD", mapOf("compute_mips", 44800.0, "utilization", cloudUtil,
                                        "queue_wait_ms", 0.0, "uplink_path", cloudUplinkPath,
                                        "downlink_path", cloudDownlinkPath)));
                Map<String, Object> observation = mapOf("protocol_version", "2.0", "type", "observation",
                        "task_id", taskId, "features", features, "available_actions", mask,
                        "task_constraints", constraints, "sim_time_ms", simulationTimeMs());
                if (options.riskFilter) observation.put("risk_context", riskContext);
                JSONObject response = python.request(observation);
                requireType(response, "action");
                OffloadingActionV2.Action action = OffloadingActionV2.validateResponse(
                        (Map<?, ?>) response, taskId, mask);
                if (options.action != null && action != options.action)
                    throw new IllegalStateException("Python fixed-action baseline selected "
                            + action.wireName + " but this run requires " + options.action.wireName);
                plan = OffloadingActionV2ExecutionPlan.create(action, workload.taskMi,
                        workload.inputBytes, workload.outputBytes, workload.mergeMi, workload.outputProfile());
                task = new TaskRecord(taskId, sequence, CloudSim.clock(), action, plan, workload);
                if (tasks.putIfAbsent(taskId, task) != null) throw new IllegalStateException("duplicate task id");
                acceptedDecisions++;
                trace.record("decision", mapOf("task_id", taskId, "action", action.wireName,
                        "action_id", action.id, "model_version", response.get("model_version"),
                        "mode", response.get("mode"), "risk", response.get("risk"),
                        "task_mi", workload.taskMi,
                        "input_bytes", workload.inputBytes, "output_bytes", workload.outputBytes,
                        "local_utilization", localUtil, "edge_utilization", edgeUtil,
                        "cloud_utilization", cloudUtil, "deadline_ms", workload.deadlineMs,
                        "urgency_class", workload.urgencyClass,
                        "splittability", workload.splittability, "arrival_gap_ms", workload.arrivalGapMs,
                        "regime_id", workload.regimeId, "regime_index", workload.regimeIndex,
                        "wan_latency_ms", workload.wanLatencyMs, "sim_time_ms", simulationTimeMs()));
                return task;
            } catch (Exception error) {
                failed = true;
                failureReason = "decision failed for " + taskId + ": " + error;
                throw new IllegalStateException(failureReason, error);
            }
        }

        void registerBranch(TaskRecord task, OffloadingActionV2ExecutionPlan.Branch spec, Tuple tuple) {
            String name = spec.name;
            Branch branch = new Branch(name, spec.module, spec.tier, tuple.getActualTupleId(),
                    spec.mi, spec.inputBytes, spec.outputBytes);
            if (task.branches.putIfAbsent(name, branch) != null)
                throw new IllegalStateException("duplicate branch " + task.taskId + "/" + name);
            if (tupleOwners.putIfAbsent(branch.tupleId, new BranchRef(task, branch)) != null)
                throw new IllegalStateException("duplicate tuple correlation " + branch.tupleId);
            trace.record("branch_created", mapOf("task_id", task.taskId, "branch", name,
                    "tuple_id", branch.tupleId, "tier", branch.tier, "module", branch.module,
                    "tuple_type", spec.tupleType, "mi", branch.mi, "input_bytes", branch.inputBytes,
                    "output_bytes", branch.outputBytes,
                    "sim_time_ms", simulationTimeMs()));
        }

        private BranchRef resolve(Tuple tuple) {
            BranchRef ref = tupleOwners.get(tuple.getActualTupleId());
            if (ref == null) throw new IllegalStateException("unknown tuple correlation " + tuple.getActualTupleId());
            return ref;
        }

        void execution(Tuple tuple, String node, String module, double utilization) {
            BranchRef ref = tupleOwners.get(tuple.getActualTupleId());
            if (ref == null) return;
            Branch branch = ref.branch;
            if (branch.executingNode != null)
                throw new IllegalStateException("duplicate branch execution " + ref.task.taskId + "/" + branch.name);
            branch.executingNode = node;
            branch.executionStart = CloudSim.clock();
            branch.utilization = utilization;
            if (!branch.module.equals(module))
                throw new IllegalStateException("branch executed in wrong module: " + module + " expected " + branch.module);
            trace.record("execution", mapOf("task_id", ref.task.taskId, "branch", branch.name,
                    "tuple_id", branch.tupleId, "node", node, "module", module,
                    "utilization", utilization, "sim_time_ms", simulationTimeMs()));
        }

        void transfer(Tuple tuple, String node, String direction, long bytes) {
            BranchRef ref = tupleOwners.get(tuple.getActualTupleId());
            if (ref == null) return;
            if (bytes < 0) throw new IllegalStateException("negative transfer bytes");
            ref.task.bandwidthBytes += bytes;
            ref.task.transferCount++;
            trace.record("transfer", mapOf("task_id", ref.task.taskId, "branch", ref.branch.name,
                    "tuple_id", ref.branch.tupleId, "node", node, "direction", direction,
                    "bytes", bytes, "sim_time_ms", simulationTimeMs()));
        }

        TaskRecord acceptBranchResult(Tuple tuple) {
            BranchRef ref = resolve(tuple);
            TaskRecord task = ref.task;
            Branch branch = ref.branch;
            if ("merge".equals(branch.name) || task.terminal)
                throw new IllegalStateException("unexpected branch result for " + task.taskId);
            if (branch.executingNode == null || !Double.isNaN(branch.resultArrival))
                throw new IllegalStateException("branch result without execution or duplicated");
            String expectedType = outputType(branch.module, task.workload.outputBytes);
            if (!BRANCH_ENDPOINT.equals(tuple.getDestModuleName()) || !expectedType.equals(tuple.getTupleType()))
                throw new IllegalStateException("branch result type/endpoint mismatch: " + tuple.getTupleType());
            branch.resultArrival = CloudSim.clock();
            task.resultBranches++;
            trace.record("branch_result", mapOf("task_id", task.taskId, "branch", branch.name,
                    "tuple_id", branch.tupleId, "sim_time_ms", simulationTimeMs()));
            if (!task.action.isPartial()) {
                if (task.resultBranches != 1 || task.branches.size() != 1)
                    throw new IllegalStateException("full task branch cardinality mismatch");
                terminal(task);
                return null;
            }
            if (task.resultBranches == 2) {
                if (task.mergeStarted) throw new IllegalStateException("partial barrier fired twice");
                task.mergeStarted = true;
                trace.record("merge_barrier", mapOf("task_id", task.taskId,
                        "both_branches_arrived", true, "sim_time_ms", simulationTimeMs()));
                return task;
            }
            if (task.resultBranches > 2) throw new IllegalStateException("too many branch results");
            return null;
        }

        Tuple beginMerge(TaskRecord task) {
            if (!task.action.isPartial() || !task.mergeStarted || task.branches.containsKey("merge"))
                throw new IllegalStateException("merge requested before barrier or twice");
            Tuple tuple = new Tuple(APP_ID, FogUtils.generateTupleId(), Tuple.UP,
                    task.workload.mergeMi, 1, task.workload.outputBytes, task.workload.mergeOutputBytes,
                    new UtilizationModelFull(), new UtilizationModelFull(), new UtilizationModelFull());
            tuple.setUserId(userId);
            tuple.setTupleType("MERGE_INPUT");
            tuple.setSrcModuleName("branch_coordinator");
            tuple.setDestModuleName(MERGE_MODULE);
            tuple.setActualTupleId(tuple.getCloudletId());
            Branch merge = new Branch("merge", MERGE_MODULE, "LOCAL", tuple.getActualTupleId(),
                    task.workload.mergeMi, task.workload.outputBytes, task.workload.mergeOutputBytes);
            task.branches.put("merge", merge);
            if (tupleOwners.putIfAbsent(merge.tupleId, new BranchRef(task, merge)) != null)
                throw new IllegalStateException("duplicate merge tuple id");
            trace.record("merge_created", mapOf("task_id", task.taskId, "tuple_id", merge.tupleId,
                    "mi", task.workload.mergeMi, "input_bytes", task.workload.outputBytes,
                    "output_bytes", task.workload.mergeOutputBytes,
                    "sim_time_ms", simulationTimeMs()));
            return tuple;
        }

        void completeMerge(Tuple tuple) {
            BranchRef ref = resolve(tuple);
            TaskRecord task = ref.task;
            Branch merge = ref.branch;
            if (!task.action.isPartial() || !"merge".equals(merge.name) || task.terminal
                    || !FINAL_ENDPOINT.equals(tuple.getDestModuleName())
                    || !"MERGED_RESULT".equals(tuple.getTupleType()))
                throw new IllegalStateException("invalid final merge result");
            if (merge.executingNode == null || !Double.isNaN(merge.resultArrival))
                throw new IllegalStateException("merge result without execution or duplicated");
            merge.resultArrival = CloudSim.clock();
            trace.record("merge_result", mapOf("task_id", task.taskId, "tuple_id", merge.tupleId,
                    "sim_time_ms", simulationTimeMs()));
            double latestBranch = Math.max(task.branches.get("local").resultArrival,
                    task.branches.get(task.action.remoteTier.name().toLowerCase()).resultArrival);
            if (CloudSim.clock() < latestBranch) throw new IllegalStateException("merge completed before branch barrier");
            terminal(task);
        }

        private void terminal(TaskRecord task) {
            if (task.terminal) throw new IllegalStateException("duplicate task terminal " + task.taskId);
            task.terminal = true;
            task.terminalTime = CloudSim.clock();
            task.latency = (task.terminalTime - task.creationTime) * 1000.0;
            boolean deadlineMet = task.latency <= task.workload.deadlineMs;
            double utilSum = 0.0;
            int utilCount = 0;
            for (Branch branch : task.branches.values()) {
                if (!Double.isNaN(branch.utilization)) { utilSum += branch.utilization; utilCount++; }
            }
            double meanUtil = utilCount == 0 ? 0.0 : utilSum / utilCount;
            String outcomeClass = deadlineMet ? "ON_TIME" : "LATE";
            trace.record("task_terminal", mapOf("task_id", task.taskId, "action", task.action.wireName,
                    "latency_ms", task.latency, "deadline_ms", task.workload.deadlineMs,
                    "urgency_class", task.workload.urgencyClass, "deadline_met", deadlineMet,
                    "bandwidth_bytes", task.bandwidthBytes, "transfer_count", task.transferCount,
                    "sim_time_ms", task.terminalTime * 1000.0));
            trace.record("task_outcome", mapOf("task_id", task.taskId, "outcome", outcomeClass,
                    "latency_ms", task.latency, "deadline_ms", task.workload.deadlineMs,
                    "bandwidth_bytes", task.bandwidthBytes, "sim_time_ms", task.terminalTime * 1000.0));
            try {
                JSONObject ack = python.request(mapOf("protocol_version", "2.0", "type", "outcome",
                        "task_id", task.taskId, "action_executed", task.action.id,
                        "status", "completed", "latency_ms", task.latency,
                        "deadline_met", deadlineMet, "sim_time_ms", task.terminalTime * 1000.0,
                        "resource_metrics", mapOf("bandwidth_bytes", task.bandwidthBytes,
                                "energy_joules", null, "executing_node_utilization", meanUtil)));
                requireType(ack, "outcome_ack");
                if (!task.taskId.equals(ack.get("task_id")))
                    throw new IllegalStateException("outcome acknowledgement task mismatch");
                task.outcomeAck = true;
                completedCount++;
                trace.record("outcome_ack", mapOf("task_id", task.taskId,
                        "updated", ack.get("updated"), "reward", ack.get("reward"),
                        "update_count", ack.get("update_count"),
                        "risk_calibration_updated", ack.get("risk_calibration_updated"),
                        "risk_calibration_updates", ack.get("risk_calibration_updates"),
                        "risk_residual_ms", ack.get("risk_residual_ms")));
            } catch (Exception error) {
                failed = true;
                failureReason = "outcome failed for " + task.taskId + ": " + error;
                throw new IllegalStateException(failureReason, error);
            }
        }

        void failOutstanding(String reason) {
            for (TaskRecord task : tasks.values()) {
                if (task.terminal) continue;
                List<String> missing = new ArrayList<String>();
                for (Branch branch : task.branches.values()) {
                    if (Double.isNaN(branch.resultArrival)) missing.add(branch.name);
                }
                terminalFailure(task, reason + "; missing_results=" + missing);
            }
        }

        private void terminalFailure(TaskRecord task, String reason) {
            if (task.terminal) return;
            task.terminal = true;
            task.failureReason = reason;
            task.terminalTime = CloudSim.clock();
            failedTaskCount++;
            completedCount++;
            String outcomeClass = reason.startsWith("execution_horizon_exceeded")
                    ? "UNRESOLVED_AT_HORIZON" : "FAILED";
            trace.record("task_failed", mapOf("task_id", task.taskId, "action", task.action.wireName,
                    "reason", reason, "deadline_met", false, "sim_time_ms", task.terminalTime * 1000.0));
            trace.record("task_outcome", mapOf("task_id", task.taskId, "outcome", outcomeClass,
                    "reason", reason, "deadline_ms", task.workload.deadlineMs,
                    "bandwidth_bytes", task.bandwidthBytes, "sim_time_ms", task.terminalTime * 1000.0));
            try {
                JSONObject ack = python.request(mapOf("protocol_version", "2.0", "type", "outcome",
                        "task_id", task.taskId, "action_executed", task.action.id,
                        "status", "failed", "deadline_met", false, "failure_reason", reason,
                        "sim_time_ms", task.terminalTime * 1000.0,
                        "resource_metrics", mapOf("bandwidth_bytes", task.bandwidthBytes,
                                "executing_node_utilization", 0.0)));
                requireType(ack, "outcome_ack");
                if (!task.taskId.equals(ack.get("task_id")))
                    throw new IllegalStateException("failure acknowledgement task mismatch");
                task.outcomeAck = true;
                trace.record("outcome_ack", mapOf("task_id", task.taskId,
                        "updated", ack.get("updated"), "reward", ack.get("reward"),
                        "update_count", ack.get("update_count"),
                        "risk_calibration_updated", ack.get("risk_calibration_updated"),
                        "risk_calibration_updates", ack.get("risk_calibration_updates"),
                        "risk_residual_ms", ack.get("risk_residual_ms")));
            } catch (Exception error) {
                failed = true;
                failureReason = "failure outcome could not be reconciled for " + task.taskId + ": " + error;
                throw new IllegalStateException(failureReason, error);
            }
        }

        void finishRun() {
            if (runCompleted) return;
            try {
                if (completedCount != options.tasks || tasks.size() != options.tasks)
                    throw new IllegalStateException("run completion cardinality mismatch");
                for (TaskRecord task : tasks.values()) {
                    if (!task.terminal || !task.outcomeAck)
                        throw new IllegalStateException("task lacks terminal/outcome ack: " + task.taskId);
                }
                if ("train".equals(options.mode)) {
                    JSONObject saved = python.request(mapOf("protocol_version", "2.0", "type", "save"));
                    requireType(saved, "saved");
                    trace.record("model_saved", mapOf("model_path", saved.get("model_path"),
                            "model_version", saved.get("model_version")));
                }
                JSONObject ack = python.request(mapOf("protocol_version", "2.0", "type", "shutdown"));
                requireType(ack, "shutdown_ack");
                if (number(ack.get("orphaned_tasks")) != 0)
                    throw new IllegalStateException("Python reports orphaned pending tasks");
                if (number(ack.get("tasks_reported")) != options.tasks)
                    throw new IllegalStateException("Python outcome count mismatch");
                runCompleted = true;
                trace.record("shutdown_ack", mapOf("orphaned_tasks", ack.get("orphaned_tasks"),
                        "tasks_reported", ack.get("tasks_reported")));
                CloudSim.abruptallyTerminate();
            } catch (Exception error) {
                failed = true; failureReason = "shutdown reconciliation failed: " + error;
                CloudSim.abruptallyTerminate();
            }
        }

        void assertConsistent() {
            if (tasks.size() != options.tasks || completedCount != options.tasks)
                throw new IllegalStateException("task count mismatch");
            for (TaskRecord task : tasks.values()) {
                if (!task.terminal || !task.outcomeAck) throw new IllegalStateException("unreconciled task");
                int expectedBranches = task.action.isPartial() ? 3 : 1;
                if (task.failureReason == null && task.branches.size() != expectedBranches)
                    throw new IllegalStateException("branch count mismatch for " + task.taskId);
                if (task.failureReason != null && task.branches.size() > expectedBranches)
                    throw new IllegalStateException("failed task has excess branches " + task.taskId);
                long mi = 0, in = 0, out = 0;
                for (Branch branch : task.branches.values()) {
                    if (task.failureReason == null) {
                        if (branch.executingNode == null || Double.isNaN(branch.executionStart)
                                || Double.isNaN(branch.resultArrival) || branch.resultArrival < branch.executionStart)
                            throw new IllegalStateException("incomplete branch lifecycle " + task.taskId + "/" + branch.name);
                    }
                    BranchRef owner = tupleOwners.get(branch.tupleId);
                    if (owner == null || owner.task != task || owner.branch != branch)
                        throw new IllegalStateException("tuple attribution error " + branch.tupleId);
                    if (!"merge".equals(branch.name)) { mi += branch.mi; in += branch.inputBytes; out += branch.outputBytes; }
                }
                int expectedComputeBranches = task.action.isPartial() ? 2 : 1;
                if (task.branches.size() >= expectedComputeBranches
                        && (mi != task.workload.taskMi || in != task.workload.inputBytes || out != task.workload.outputBytes))
                    throw new IllegalStateException("partition conservation failed for " + task.taskId);
                if (task.action.isPartial() && task.failureReason == null) {
                    Branch local = task.branches.get("local");
                    Branch remote = task.branches.get(task.action.remoteTier.name().toLowerCase());
                    Branch merge = task.branches.get("merge");
                    if (local == null || remote == null || merge == null || !task.mergeStarted)
                        throw new IllegalStateException("partial merge lifecycle missing");
                    if (merge.executionStart + 1e-9 < Math.max(local.resultArrival, remote.resultArrival) + MERGE_OVERHEAD_MS / 1000.0)
                        throw new IllegalStateException("merge started before both branch results");
                }
            }
            if (tupleOwners.size() != tasks.values().stream().mapToInt(t -> t.branches.size()).sum())
                throw new IllegalStateException("tuple registry size mismatch");
        }

        Map<String, Object> acceptanceFields() {
            Map<String, Integer> counts = new LinkedHashMap<String, Integer>();
            for (TaskRecord task : tasks.values())
                counts.put(task.action.wireName, counts.getOrDefault(task.action.wireName, 0) + 1);
            return mapOf("status", failedTaskCount == 0 ? "PASS" : "RECONCILED_WITH_TASK_OUTCOMES",
                    "run_id", options.runId, "mode", options.mode, "action_counts", counts, "tasks", completedCount,
                    "failed_tasks", failedTaskCount, "evaluation_mode", options.evaluationMode,
                    "accepted_decisions", acceptedDecisions, "tuple_count", tupleOwners.size());
        }
    }

    private static String outputType(String module, long outputBytes) {
        String profile = tupleProfileSuffix(outputBytes);
        if (LOCAL_FULL.equals(module)) return "LOCAL_FULL_RESULT" + profile;
        if (EDGE_FULL.equals(module)) return "EDGE_FULL_RESULT" + profile;
        if (CLOUD_FULL.equals(module)) return "CLOUD_FULL_RESULT" + profile;
        if (module.startsWith("local_partial_")) return "LOCAL_PARTIAL_RESULT_" + module.substring("local_partial_".length()) + profile;
        if (module.startsWith("edge_partial_")) return "EDGE_PARTIAL_RESULT_" + module.substring("edge_partial_".length()) + profile;
        if (module.startsWith("cloud_partial_")) return "CLOUD_PARTIAL_RESULT_" + module.substring("cloud_partial_".length()) + profile;
        throw new IllegalArgumentException("unknown worker module " + module);
    }

    private static void requireType(JSONObject object, String type) {
        if (!type.equals(object.get("type"))) throw new IllegalStateException("expected " + type + ", got " + object);
    }
    private static long number(Object value) {
        if (!(value instanceof Number)) throw new IllegalStateException("expected numeric value: " + value);
        return ((Number) value).longValue();
    }
    private static Map<String, Object> mapOf(Object... pairs) {
        if (pairs.length % 2 != 0) throw new IllegalArgumentException("key/value pairs expected");
        Map<String, Object> map = new LinkedHashMap<String, Object>();
        for (int i = 0; i < pairs.length; i += 2) map.put((String) pairs[i], pairs[i + 1]);
        return map;
    }

    private static final class PythonAdapter implements AutoCloseable {
        private static final String EOF = "__EOF__";
        private final Process process;
        private final BufferedWriter stdin;
        private final BlockingQueue<String> stdout = new LinkedBlockingQueue<String>();
        private final Trace trace;
        private final Path stderrPath;
        private volatile boolean shutdown;
        private PythonAdapter(Process process, Trace trace, Path stderrPath) throws IOException {
            this.process = process; this.trace = trace; this.stderrPath = stderrPath;
            stdin = new BufferedWriter(new OutputStreamWriter(process.getOutputStream(), StandardCharsets.UTF_8));
            Thread out = new Thread(() -> drainStdout(), "v2-partial-python-stdout");
            out.setDaemon(true); out.start();
            Thread err = new Thread(() -> drainStderr(), "v2-partial-python-stderr");
            err.setDaemon(true); err.start();
        }
        static PythonAdapter start(Options options, Trace trace) throws Exception {
            List<String> command = new ArrayList<String>();
            command.add(options.python.toString()); command.add("-m"); command.add("rl_model.server_v2");
            command.add("--config"); command.add(options.rlRoot.resolve("config/v2.json").toString());
            command.add("--mode"); command.add(options.mode);
            if ("baseline".equals(options.mode)) {
                command.add("--policy");
                command.add(options.action != null ? options.action.wireName.toLowerCase() : options.policy);
            }
            if ("eval".equals(options.mode)) {
                command.add("--model-in"); command.add(options.modelIn.toString());
            }
            if (options.riskStateIn != null) {
                command.add("--risk-state-in"); command.add(options.riskStateIn.toString());
            }
            command.add("--model-out"); command.add(options.output.resolve("python_model.json").toString());
            ProcessBuilder pb = new ProcessBuilder(command);
            pb.directory(options.rlRoot.toFile());
            pb.environment().put("PYTHONPATH", options.rlRoot.resolve("src").toString());
            PythonAdapter adapter = new PythonAdapter(pb.start(), trace, options.output.resolve("python_stderr.log"));
            JSONObject hello = adapter.request(mapOf("protocol_version", "2.0", "type", "hello",
                    "run_id", options.runId, "phase", "train".equals(options.mode) ? "train" : "test", "sim_seed", 13,
                    "simulator", mapOf("name", "iFogSim2", "experiment", "RlOffloadingV2PartialIntegrationExperiment")));
            requireType(hello, "hello_ack");
            trace.record("hello_ack", mapOf("mode", hello.get("mode"), "policy", hello.get("policy"),
                    "actions", hello.get("actions")));
            return adapter;
        }
        synchronized JSONObject request(Map<String, Object> message) throws Exception {
            if (!process.isAlive()) throw new IOException("Python server exited " + process.exitValue());
            stdin.write(JSONObject.toJSONString(message)); stdin.newLine(); stdin.flush();
            trace.record("python_send", mapOf("type", message.get("type"), "task_id", message.get("task_id"),
                    "action_executed", message.get("action_executed"), "status", message.get("status"),
                    "failure_reason", message.get("failure_reason")));
            String line = stdout.poll(AGENT_TIMEOUT_MS, TimeUnit.MILLISECONDS);
            if (line == null) throw new IOException("Python response timeout");
            if (EOF.equals(line)) throw new IOException("Python stdout EOF");
            Object parsed = new JSONParser().parse(line);
            if (!(parsed instanceof JSONObject)) throw new IOException("Python response is not JSON object");
            JSONObject object = (JSONObject) parsed;
            if (!"2.0".equals(object.get("protocol_version"))) throw new IOException("Python protocol version mismatch");
            if ("error".equals(object.get("type"))) throw new IOException("Python protocol error: " + object);
            trace.record("python_receive", mapOf("type", object.get("type"),
                    "task_id", object.get("task_id"), "action", object.get("action")));
            if ("shutdown".equals(message.get("type")) && "shutdown_ack".equals(object.get("type"))) shutdown = true;
            return object;
        }
        private void drainStdout() {
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(
                    process.getInputStream(), StandardCharsets.UTF_8))) {
                String line; while ((line = reader.readLine()) != null) stdout.put(line);
            } catch (Exception ignored) { } finally { stdout.offer(EOF); }
        }
        private void drainStderr() {
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(
                    process.getErrorStream(), StandardCharsets.UTF_8));
                 BufferedWriter writer = Files.newBufferedWriter(stderrPath, StandardCharsets.UTF_8)) {
                String line; while ((line = reader.readLine()) != null) {
                    writer.write(line); writer.newLine(); writer.flush();
                }
            } catch (Exception ignored) { }
        }
        @Override public void close() throws Exception {
            try { stdin.close(); } catch (IOException ignored) { }
            if (!shutdown && process.isAlive()) process.destroy();
            process.waitFor(2, TimeUnit.SECONDS);
            if (process.isAlive()) process.destroyForcibly();
            trace.record("python_exit", mapOf("shutdown_ack", shutdown,
                    "exit_code", process.isAlive() ? null : process.exitValue()));
        }
    }

    private static final class Trace implements AutoCloseable {
        private final BufferedWriter writer;
        Trace(Path path) throws IOException { writer = Files.newBufferedWriter(path, StandardCharsets.UTF_8); }
        synchronized void record(String type, Map<String, Object> fields) {
            try {
                Map<String, Object> row = new LinkedHashMap<String, Object>();
                row.put("record", type); row.putAll(fields);
                writer.write(JSONObject.toJSONString(row)); writer.newLine(); writer.flush();
            } catch (IOException error) { throw new IllegalStateException("trace write failed", error); }
        }
        @Override public void close() throws IOException { writer.close(); }
    }

    private static final class Options {
        Path output, python, rlRoot, workloadFile, modelIn, riskStateIn;
        boolean riskFilter, evaluationMode;
        List<WorkloadTask> workload = new ArrayList<WorkloadTask>();
        boolean tasksExplicit;
        String runId;
        String mode = "baseline";
        String policy;
        String dropBranch;
        OffloadingActionV2.Action action;
        int tasks = 2;
        double interArrivalMs = 1.0;
        double deadlineMs = 1000.0;
        double partitionOverheadMs = 3.0;
        double mergeOverheadMs = 2.0;
        double wanLatencyMs = 45.0;
        double watchdogMs = 60000.0;

        static Options parse(String[] args) throws Exception {
            Options o = new Options();
            Path cwd = new File(".").toPath().toAbsolutePath().normalize();
            o.output = cwd.resolve("audit_output/v2_partial/latest");
            o.python = Path.of("C:/Users/DELL/AppData/Roaming/uv/python/cpython-3.15.0b1-windows-x86_64-none/python.exe");
            o.rlRoot = cwd.resolve("deliverables/08_RL_Model");
            o.runId = "v2-partial";
            o.action = null;
            for (int i = 0; i < args.length;) {
                String key = args[i++];
                if ("--risk-filter".equals(key)) { o.riskFilter = true; continue; }
                if ("--evaluation-mode".equals(key)) { o.evaluationMode = true; continue; }
                if (i >= args.length) throw new IllegalArgumentException("missing value for " + key);
                String value = args[i++];
                if ("--output".equals(key)) o.output = Path.of(value).toAbsolutePath();
                else if ("--python".equals(key)) o.python = Path.of(value).toAbsolutePath();
                else if ("--rl-root".equals(key)) o.rlRoot = Path.of(value).toAbsolutePath();
                else if ("--run-id".equals(key)) o.runId = value;
                else if ("--mode".equals(key)) o.mode = value;
                else if ("--action".equals(key)) o.action = OffloadingActionV2.Action.fromName(value);
                else if ("--policy".equals(key)) o.policy = value.toLowerCase();
                else if ("--model-in".equals(key)) o.modelIn = Path.of(value).toAbsolutePath();
                else if ("--risk-state-in".equals(key)) o.riskStateIn = Path.of(value).toAbsolutePath();
                else if ("--drop-branch".equals(key)) o.dropBranch = value;
                else if ("--tasks".equals(key)) { o.tasks = Integer.parseInt(value); o.tasksExplicit = true; }
                else if ("--workload".equals(key)) o.workloadFile = Path.of(value).toAbsolutePath();
                else if ("--inter-arrival-ms".equals(key)) o.interArrivalMs = Double.parseDouble(value);
                else if ("--deadline-ms".equals(key)) o.deadlineMs = Double.parseDouble(value);
                else if ("--partition-overhead-ms".equals(key)) o.partitionOverheadMs = Double.parseDouble(value);
                else if ("--merge-overhead-ms".equals(key)) o.mergeOverheadMs = Double.parseDouble(value);
                else if ("--wan-latency-ms".equals(key)) o.wanLatencyMs = Double.parseDouble(value);
                else if ("--watchdog-ms".equals(key)) o.watchdogMs = Double.parseDouble(value);
                else throw new IllegalArgumentException("unknown option " + key);
            }
            if (!"baseline".equals(o.mode) && !"train".equals(o.mode) && !"eval".equals(o.mode))
                throw new IllegalArgumentException("mode must be baseline, train, or eval");
            if ("baseline".equals(o.mode) && o.action == null && o.policy == null)
                throw new IllegalArgumentException("baseline mode requires --action or --policy");
            if ("baseline".equals(o.mode) && o.action != null && o.policy != null)
                throw new IllegalArgumentException("choose either --action or --policy, not both");
            if ("train".equals(o.mode) && (o.action != null || o.policy != null || o.modelIn != null))
                throw new IllegalArgumentException("train mode selects actions from the learned policy; omit action/policy/model-in");
            if ("eval".equals(o.mode) && (o.modelIn == null || o.action != null || o.policy != null))
                throw new IllegalArgumentException("eval mode requires --model-in and no fixed action/policy");
            if (o.policy != null && !Arrays.asList("local", "edge", "cloud", "random").contains(o.policy))
                throw new IllegalArgumentException("--policy must be local, edge, cloud, or random");
            if (o.tasks < 1 || o.tasks > 10000 || !Double.isFinite(o.interArrivalMs) || o.interArrivalMs <= 0)
                throw new IllegalArgumentException("tasks must be 1..10000 and inter-arrival finite/positive");
            if (!Double.isFinite(o.deadlineMs) || o.deadlineMs <= 0
                    || !Double.isFinite(o.partitionOverheadMs) || o.partitionOverheadMs < 0
                    || !Double.isFinite(o.mergeOverheadMs) || o.mergeOverheadMs < 0
                    || !Double.isFinite(o.wanLatencyMs) || o.wanLatencyMs < 0
                    || !Double.isFinite(o.watchdogMs) || o.watchdogMs <= 0)
                throw new IllegalArgumentException("deadline/watchdog must be positive; overheads/WAN latency must be finite and non-negative");
            if (o.workloadFile != null) {
                List<String> lines = Files.readAllLines(o.workloadFile, StandardCharsets.UTF_8);
                int sequence = 1;
                for (String line : lines) if (!line.trim().isEmpty()) o.workload.add(WorkloadTask.parse(line, sequence++));
                if (o.workload.isEmpty()) throw new IllegalArgumentException("workload file is empty");
                if (o.tasksExplicit && o.tasks != o.workload.size())
                    throw new IllegalArgumentException("--tasks must match the number of workload rows");
                o.tasks = o.workload.size();
            } else {
                for (int sequence = 1; sequence <= o.tasks; sequence++)
                    o.workload.add(new WorkloadTask(sequence, TASK_MI, INPUT_BYTES, OUTPUT_BYTES,
                            MERGE_MI, MERGE_OUTPUT_BYTES, o.deadlineMs,
                            sequence == 1 ? 0.0 : o.interArrivalMs, "normal",
                            "DATA_PARALLEL_DIVISIBLE", "data-parallel-v1"));
            }
            return o;
        }
    }
}
