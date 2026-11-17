package org.fog.test.perfeval;

import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;

import org.cloudbus.cloudsim.Host;
import org.cloudbus.cloudsim.Log;
import org.cloudbus.cloudsim.Pe;
import org.cloudbus.cloudsim.Storage;
import org.cloudbus.cloudsim.UtilizationModelFull;
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

/**
 * Experiment-owned mixed full/partial multi-task lifecycle fixture.
 * Full tasks execute on one selected tier; partial tasks own Local and Edge
 * branches, an independent two-result barrier, and a real merge Cloudlet.
 */
public final class MixedMultiTaskOffloadingSpike {
    private static final String APP_ID = "mixed-full-partial-offload";
    private static final String LOCAL_MODULE = "local_worker";
    private static final String EDGE_MODULE = "edge_worker";
    private static final String CLOUD_MODULE = "cloud_worker";
    private static final String MERGE_MODULE = "merge_worker";
    private static final String BRANCH_ENDPOINT = "branch_result_endpoint";
    private static final String FINAL_ENDPOINT = "final_result_endpoint";

    private static final long TASK_MI = 10000L;
    private static final long INPUT_BYTES = 12000L;
    private static final long OUTPUT_BYTES = 1000L;
    private static final long MERGE_MI = 1200L;
    private static final long MERGE_OUTPUT_BYTES = 100L;
    private static final double LOCAL_SHARE = 0.40;
    private static final double EDGE_SHARE = 0.60;
    private static final double LOCAL_MIPS = 1000.0;
    private static final double EDGE_MIPS = 2800.0;
    private static final double LOCAL_EDGE_LATENCY_MS = 45.0;

    private enum Events implements CloudSimTags { EMIT_TASK, BRANCH_RESULT, MERGE_RESULT }

    private MixedMultiTaskOffloadingSpike() { }

    public static void main(String[] args) {
        Path output = args.length > 0 ? Path.of(args[0]).toAbsolutePath()
                : Path.of("audit_output/mixed_full_partial_latest").toAbsolutePath();
        int taskCount = args.length > 1 ? Integer.parseInt(args[1]) : 4;
        double interArrivalMs = args.length > 2 ? Double.parseDouble(args[2]) : 1.0;
        try {
            if (taskCount < 1 || taskCount > 100 || !Double.isFinite(interArrivalMs) || interArrivalMs <= 0)
                throw new IllegalArgumentException("tasks must be 1..100 and inter-arrival must be finite/positive");
            Files.createDirectories(output);
            try (Trace trace = new Trace(output.resolve("mixed_trace.csv"))) {
                run(trace, output, taskCount, interArrivalMs);
            }
        } catch (Throwable error) {
            error.printStackTrace(System.err);
            System.exit(2);
        }
    }

    private static void run(Trace trace, Path output, int taskCount, double interArrivalMs) throws Exception {
        Log.disable();
        CloudSim.init(1, Calendar.getInstance(), false);

        FogBroker broker = new FogBroker("mixed-offload-broker");
        TaskRegistry registry = new TaskRegistry(trace, output, broker.getId(), taskCount);

        InstrumentedFogDevice cloud = createDevice("cloud", 44800, 40000,
                100000, 100000, 0, 16 * 103, 16 * 83.25, registry);
        cloud.setParentId(-1);

        InstrumentedFogDevice edge = createDevice("edge", (long) EDGE_MIPS, 4000,
                10000, 10000, 1, 107.339, 83.4333, registry);
        edge.setParentId(cloud.getId());
        edge.setUplinkLatency(1.0);

        InstrumentedFogDevice local = createDevice("local", (long) LOCAL_MIPS, 2000,
                10000, 10000, 2, 87.53, 82.44, registry);
        local.setParentId(edge.getId());
        local.setUplinkLatency(LOCAL_EDGE_LATENCY_MS);

        List<FogDevice> devices = new ArrayList<FogDevice>();
        devices.add(cloud);
        devices.add(edge);
        devices.add(local);

        TaskCoordinator coordinator = new TaskCoordinator("mixed-offload-coordinator", registry, local);
        BranchResultEndpoint branchEndpoint = new BranchResultEndpoint("mixed-branch-endpoint",
                broker.getId(), APP_ID, local.getId(), 1.0, coordinator);
        FinalResultEndpoint finalEndpoint = new FinalResultEndpoint("mixed-final-endpoint",
                broker.getId(), APP_ID, local.getId(), 1.0, coordinator);
        List<Actuator> actuators = new ArrayList<Actuator>();
        actuators.add(branchEndpoint);
        actuators.add(finalEndpoint);

        Application app = createApplication(broker.getId());
        ModuleMapping mapping = ModuleMapping.createModuleMapping();
        mapping.addModuleToDevice(LOCAL_MODULE, "local");
        mapping.addModuleToDevice(EDGE_MODULE, "edge");
        mapping.addModuleToDevice(CLOUD_MODULE, "cloud");
        mapping.addModuleToDevice(MERGE_MODULE, "local");

        Controller controller = new Controller("mixed-offload-controller", devices,
                Collections.emptyList(), actuators);
        controller.submitApplication(app, new ModulePlacementMapping(devices, app, mapping));

        trace.record("configuration", "run", "", -1, 0.0, "tasks=" + taskCount + ";inter_arrival_ms=" + interArrivalMs
                + ";pattern=odd_full_Local_Edge_Cloud_even_partial_Local_Edge"
                + ";task_mi=" + TASK_MI + ";input_bytes=" + INPUT_BYTES + ";output_bytes=" + OUTPUT_BYTES
                + ";local_share=" + LOCAL_SHARE + ";edge_share=" + EDGE_SHARE
                + ";merge_mi=" + MERGE_MI + ";merge_output_bytes=" + MERGE_OUTPUT_BYTES
                + ";merge_model=CloudSim_Cloudlet_on_Local_merge_worker");

        new TaskEmitter("mixed-offload-emitter", local, registry, taskCount, interArrivalMs);
        CloudSim.startSimulation();
        CloudSim.stopSimulation();

        if (registry.completedCount != taskCount || registry.failed)
            throw new IllegalStateException("simulation ended before all mixed task terminals: "
                    + registry.completedCount + "/" + taskCount + "; " + registry.failureReason);
        registry.assertConsistent();
        registry.writeSummary();
        System.out.println("MIXED_FULL_PARTIAL_STATUS=PASS");
        System.out.println("TASKS=" + taskCount);
        System.out.println("SUMMARY=" + output.resolve("mixed_summary.csv"));
        System.out.println("TRACE=" + output.resolve("mixed_trace.csv"));
    }

    private static Application createApplication(int userId) {
        Application app = Application.createApplication(APP_ID, userId);
        app.addAppModule(LOCAL_MODULE, 64, 1000, 10000);
        app.addAppModule(EDGE_MODULE, 64, 1000, 10000);
        app.addAppModule(CLOUD_MODULE, 64, 1000, 10000);
        app.addAppModule(MERGE_MODULE, 64, 1000, 10000);

        app.addAppEdge(LOCAL_MODULE, BRANCH_ENDPOINT, 1, (double) (OUTPUT_BYTES * LOCAL_SHARE),
                "LOCAL_RESULT", Tuple.DOWN, AppEdge.ACTUATOR);
        app.addTupleMapping(LOCAL_MODULE, "LOCAL_INPUT", "LOCAL_RESULT", new FractionalSelectivity(1.0));
        app.addAppEdge(EDGE_MODULE, BRANCH_ENDPOINT, 1, (double) (OUTPUT_BYTES * EDGE_SHARE),
                "EDGE_RESULT", Tuple.DOWN, AppEdge.ACTUATOR);
        app.addTupleMapping(EDGE_MODULE, "EDGE_INPUT", "EDGE_RESULT", new FractionalSelectivity(1.0));
        app.addAppEdge(CLOUD_MODULE, BRANCH_ENDPOINT, 1, (double) OUTPUT_BYTES,
                "CLOUD_RESULT", Tuple.DOWN, AppEdge.ACTUATOR);
        app.addTupleMapping(CLOUD_MODULE, "CLOUD_INPUT", "CLOUD_RESULT", new FractionalSelectivity(1.0));
        app.addAppEdge(MERGE_MODULE, FINAL_ENDPOINT, 1, (double) MERGE_OUTPUT_BYTES,
                "MERGED_RESULT", Tuple.DOWN, AppEdge.ACTUATOR);
        app.addTupleMapping(MERGE_MODULE, "MERGE_INPUT", "MERGED_RESULT", new FractionalSelectivity(1.0));
        return app;
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
                10, upBw, downBw, 0, 0.0, registry);
        device.setLevel(level);
        return device;
    }

    private static final class TaskEmitter extends SimEntity {
        private final InstrumentedFogDevice local;
        private final TaskRegistry registry;
        private final int taskCount;
        private final double interArrivalMs;
        private int emitted;

        TaskEmitter(String name, InstrumentedFogDevice local, TaskRegistry registry,
                int taskCount, double interArrivalMs) {
            super(name);
            this.local = local;
            this.registry = registry;
            this.taskCount = taskCount;
            this.interArrivalMs = interArrivalMs;
        }

        @Override public void startEntity() { send(getId(), 5.0, Events.EMIT_TASK); }

        @Override public void processEvent(SimEvent event) {
            if (event.getTag() == FogEvents.TUPLE_ACK) return;
            if (event.getTag() != Events.EMIT_TASK)
                throw new IllegalStateException("unexpected emitter event " + event.getTag());
            if (emitted >= taskCount) throw new IllegalStateException("too many task emissions");
            int sequence = ++emitted;
            String taskId = "mixed-task-" + String.format("%03d", sequence);
            boolean partial = sequence % 2 == 0;
            String fullAction = partial ? "" : new String[] {"Local", "Edge", "Cloud"}[((sequence - 1) / 2) % 3];
            TaskRecord task = registry.create(taskId, CloudSim.clock(), partial, fullAction);
            if (partial) {
                long localMi = Math.round(TASK_MI * LOCAL_SHARE);
                long edgeMi = TASK_MI - localMi;
                long localInput = Math.round(INPUT_BYTES * LOCAL_SHARE);
                long edgeInput = INPUT_BYTES - localInput;
                long localOutput = Math.round(OUTPUT_BYTES * LOCAL_SHARE);
                long edgeOutput = OUTPUT_BYTES - localOutput;
                emitBranch(task, "local", LOCAL_MODULE, "LOCAL_INPUT", localMi, localInput, localOutput);
                emitBranch(task, "edge", EDGE_MODULE, "EDGE_INPUT", edgeMi, edgeInput, edgeOutput);
            } else {
                String module = "Local".equals(fullAction) ? LOCAL_MODULE
                        : "Edge".equals(fullAction) ? EDGE_MODULE : CLOUD_MODULE;
                String tupleType = "Local".equals(fullAction) ? "LOCAL_INPUT"
                        : "Edge".equals(fullAction) ? "EDGE_INPUT" : "CLOUD_INPUT";
                emitBranch(task, "full", module, tupleType, TASK_MI, INPUT_BYTES, OUTPUT_BYTES);
            }
            if (emitted < taskCount) send(getId(), interArrivalMs, Events.EMIT_TASK);
        }

        private void emitBranch(TaskRecord task, String name, String module, String tupleType,
                long mi, long inputBytes, long outputBytes) {
            Tuple tuple = new Tuple(APP_ID, FogUtils.generateTupleId(), Tuple.UP,
                    mi, 1, inputBytes, outputBytes,
                    new UtilizationModelFull(), new UtilizationModelFull(), new UtilizationModelFull());
            tuple.setUserId(registry.userId);
            tuple.setTupleType(tupleType);
            tuple.setSrcModuleName("TASK_SOURCE");
            tuple.setDestModuleName(module);
            tuple.setActualTupleId(tuple.getCloudletId());
            registry.registerBranch(task, name, tuple, mi, inputBytes, outputBytes);
            sendNow(local.getId(), FogEvents.TUPLE_ARRIVAL, tuple);
        }

        @Override public void shutdownEntity() { }
    }

    private static final class InstrumentedFogDevice extends FogDevice {
        private final TaskRegistry registry;
        InstrumentedFogDevice(String name, FogDeviceCharacteristics characteristics,
                AppModuleAllocationPolicy policy, List<Storage> storage,
                double interval, long up, long down, double uplinkLatency,
                double rate, TaskRegistry registry) throws Exception {
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
            registry.execution((Tuple) event.getData(), getName(), moduleName, CloudSim.clock());
            super.executeTuple(event, moduleName);
        }
    }

    private static final class BranchResultEndpoint extends Actuator {
        private final TaskCoordinator coordinator;
        BranchResultEndpoint(String name, int userId, String appId, int gatewayId,
                double latency, TaskCoordinator coordinator) {
            super(name, userId, appId, gatewayId, latency, null, BRANCH_ENDPOINT, "");
            this.coordinator = coordinator;
        }
        @Override public void processEvent(SimEvent event) {
            if (event.getTag() == FogEvents.TUPLE_ARRIVAL) coordinator.acceptBranch((Tuple) event.getData());
            super.processEvent(event);
        }
    }

    private static final class FinalResultEndpoint extends Actuator {
        private final TaskCoordinator coordinator;
        FinalResultEndpoint(String name, int userId, String appId, int gatewayId,
                double latency, TaskCoordinator coordinator) {
            super(name, userId, appId, gatewayId, latency, null, FINAL_ENDPOINT, "");
            this.coordinator = coordinator;
        }
        @Override public void processEvent(SimEvent event) {
            if (event.getTag() == FogEvents.TUPLE_ARRIVAL) coordinator.acceptMerge((Tuple) event.getData());
            super.processEvent(event);
        }
    }

    private static final class TaskCoordinator extends SimEntity {
        private final TaskRegistry registry;
        private final InstrumentedFogDevice local;
        TaskCoordinator(String name, TaskRegistry registry, InstrumentedFogDevice local) {
            super(name); this.registry = registry; this.local = local;
        }
        @Override public void startEntity() { }
        void acceptBranch(Tuple tuple) { sendNow(getId(), Events.BRANCH_RESULT, tuple); }
        void acceptMerge(Tuple tuple) { sendNow(getId(), Events.MERGE_RESULT, tuple); }
        @Override public void processEvent(SimEvent event) {
            if (event.getTag() == FogEvents.TUPLE_ACK) return;
            if (event.getTag() == Events.BRANCH_RESULT) {
                TaskRecord task = registry.acceptBranchResult((Tuple) event.getData());
                if (task != null) {
                    Tuple mergeTuple = registry.beginMerge(task);
                    sendNow(local.getId(), FogEvents.TUPLE_ARRIVAL, mergeTuple);
                }
                if (registry.completedCount == registry.expectedTasks) CloudSim.abruptallyTerminate();
            } else if (event.getTag() == Events.MERGE_RESULT) {
                registry.complete((Tuple) event.getData());
                if (registry.completedCount == registry.expectedTasks) CloudSim.abruptallyTerminate();
            } else throw new IllegalStateException("unexpected coordinator event " + event.getTag());
        }
        @Override public void shutdownEntity() { }
    }

    private static final class Branch {
        final String name;
        final int actualTupleId;
        final long mi, inputBytes, outputBytes;
        String executingNode, executingModule;
        double executionStartMs = Double.NaN, resultArrivalMs = Double.NaN;
        Branch(String name, int actualTupleId, long mi, long inputBytes, long outputBytes) {
            this.name = name; this.actualTupleId = actualTupleId;
            this.mi = mi; this.inputBytes = inputBytes; this.outputBytes = outputBytes;
        }
    }

    private static final class BranchRef {
        final TaskRecord task;
        final Branch branch;
        BranchRef(TaskRecord task, Branch branch) { this.task = task; this.branch = branch; }
    }

    private static final class TaskRecord {
        final String taskId;
        final double creationTimeMs;
        final boolean partial;
        final String fullAction;
        final Map<String, Branch> branches = new LinkedHashMap<String, Branch>();
        long bandwidthBytes;
        int transferCount;
        boolean mergeStarted, completed;
        double mergeEndMs = Double.NaN;
        TaskRecord(String taskId, double creationTimeMs, boolean partial, String fullAction) {
            this.taskId = taskId; this.creationTimeMs = creationTimeMs;
            this.partial = partial; this.fullAction = fullAction;
        }
    }

    private static final class TaskRegistry {
        final int userId;
        final int expectedTasks;
        private final Trace trace;
        private final Path output;
        private final Map<String, TaskRecord> tasksById = new LinkedHashMap<String, TaskRecord>();
        private final Map<Integer, BranchRef> branchesByTupleId = new LinkedHashMap<Integer, BranchRef>();
        int completedCount;
        boolean failed;
        String failureReason = "";

        TaskRegistry(Trace trace, Path output, int userId, int expectedTasks) {
            this.trace = trace; this.output = output; this.userId = userId; this.expectedTasks = expectedTasks;
        }

        TaskRecord create(String taskId, double now, boolean partial, String fullAction) {
            if (partial && !fullAction.isEmpty()) throw new IllegalArgumentException("partial task cannot carry a full action");
            if (!partial && !("Local".equals(fullAction) || "Edge".equals(fullAction) || "Cloud".equals(fullAction)))
                throw new IllegalArgumentException("full task requires Local, Edge, or Cloud action");
            TaskRecord task = new TaskRecord(taskId, now, partial, fullAction);
            if (tasksById.putIfAbsent(taskId, task) != null)
                throw new IllegalStateException("duplicate task ID " + taskId);
            trace.record("task_created", taskId, "", -1, now,
                    "mode=" + (partial ? "partial" : "full") + ";full_action=" + fullAction
                    + ";branch_count=" + (partial ? 2 : 1));
            return task;
        }

        void registerBranch(TaskRecord task, String name, Tuple tuple,
                long mi, long inputBytes, long outputBytes) {
            if (task.partial && !("local".equals(name) || "edge".equals(name)))
                throw new IllegalArgumentException("partial task branch must be local or edge");
            if (!task.partial && !"full".equals(name))
                throw new IllegalArgumentException("full task must have exactly one full branch");
            if (task.branches.containsKey(name)) throw new IllegalStateException("duplicate branch " + task.taskId + "/" + name);
            Branch branch = new Branch(name, tuple.getActualTupleId(), mi, inputBytes, outputBytes);
            if (branchesByTupleId.putIfAbsent(branch.actualTupleId, new BranchRef(task, branch)) != null)
                throw new IllegalStateException("duplicate branch tuple ID " + branch.actualTupleId);
            task.branches.put(name, branch);
            trace.record("branch_created", task.taskId, name, branch.actualTupleId, CloudSim.clock(),
                    "mi=" + mi + ";input_bytes=" + inputBytes + ";output_bytes=" + outputBytes);
        }

        private BranchRef resolve(Tuple tuple) {
            BranchRef ref = branchesByTupleId.get(tuple.getActualTupleId());
            if (ref == null) throw new IllegalStateException("unknown tuple correlation " + tuple.getActualTupleId());
            return ref;
        }

        void execution(Tuple tuple, String node, String module, double now) {
            BranchRef ref = branchesByTupleId.get(tuple.getActualTupleId());
            if (ref == null) return;
            Branch branch = ref.branch;
            if (branch.executingNode != null) throw new IllegalStateException("duplicate execution " + ref.task.taskId + "/" + branch.name);
            branch.executingNode = node; branch.executingModule = module; branch.executionStartMs = now;
            trace.record("execution_start", ref.task.taskId, branch.name, branch.actualTupleId, now,
                    "node=" + node + ";module=" + module + ";mi=" + branch.mi);
        }

        void transfer(Tuple tuple, String node, String direction, long bytes) {
            BranchRef ref = branchesByTupleId.get(tuple.getActualTupleId());
            if (ref == null) return;
            if (bytes < 0) throw new IllegalStateException("negative transfer size");
            ref.task.bandwidthBytes += bytes; ref.task.transferCount++;
            trace.record("transfer", ref.task.taskId, ref.branch.name, ref.branch.actualTupleId, CloudSim.clock(),
                    "node=" + node + ";direction=" + direction + ";bytes=" + bytes);
        }

        TaskRecord acceptBranchResult(Tuple tuple) {
            BranchRef ref = resolve(tuple);
            TaskRecord task = ref.task;
            Branch branch = ref.branch;
            if ("merge".equals(branch.name)) throw new IllegalStateException("merge tuple reached branch endpoint");
            String expectedType;
            if (!task.partial) {
                if (!"full".equals(branch.name)) throw new IllegalStateException("full task received non-full branch");
                expectedType = "Local".equals(task.fullAction) ? "LOCAL_RESULT"
                        : "Edge".equals(task.fullAction) ? "EDGE_RESULT" : "CLOUD_RESULT";
            } else {
                expectedType = "local".equals(branch.name) ? "LOCAL_RESULT" : "EDGE_RESULT";
            }
            if (!BRANCH_ENDPOINT.equals(tuple.getDestModuleName()) || !expectedType.equals(tuple.getTupleType()))
                throw new IllegalStateException("branch result endpoint/type mismatch for " + task.taskId);
            if (branch.executingNode == null) throw new IllegalStateException("branch result without execution");
            if (!Double.isNaN(branch.resultArrivalMs)) throw new IllegalStateException("duplicate branch result " + task.taskId + "/" + branch.name);
            branch.resultArrivalMs = CloudSim.clock();
            trace.record("branch_result", task.taskId, branch.name, branch.actualTupleId, branch.resultArrivalMs, "");
            if (!task.partial) {
                if (task.completed) throw new IllegalStateException("duplicate full-task terminal " + task.taskId);
                task.completed = true;
                task.mergeEndMs = CloudSim.clock();
                completedCount++;
                trace.record("task_completed", task.taskId, "full", branch.actualTupleId, task.mergeEndMs,
                        "mode=full;full_action=" + task.fullAction + ";latency_ms="
                        + (task.mergeEndMs - task.creationTimeMs) + ";bandwidth_bytes=" + task.bandwidthBytes
                        + ";transfer_count=" + task.transferCount + ";completed_count=" + completedCount);
                return null;
            }
            long arrived = task.branches.values().stream().filter(b -> !Double.isNaN(b.resultArrivalMs)).count();
            if (arrived == 2) {
                if (task.mergeStarted) throw new IllegalStateException("merge barrier fired twice for " + task.taskId);
                task.mergeStarted = true;
                trace.record("merge_barrier", task.taskId, "", -1, CloudSim.clock(), "both_branch_results_arrived");
                return task;
            }
            return null;
        }

        Tuple beginMerge(TaskRecord task) {
            if (!task.partial || !task.mergeStarted || task.branches.containsKey("merge"))
                throw new IllegalStateException("merge requested before barrier or twice for " + task.taskId);
            Tuple tuple = new Tuple(APP_ID, FogUtils.generateTupleId(), Tuple.UP,
                    MERGE_MI, 1, OUTPUT_BYTES, MERGE_OUTPUT_BYTES,
                    new UtilizationModelFull(), new UtilizationModelFull(), new UtilizationModelFull());
            tuple.setUserId(userId); tuple.setTupleType("MERGE_INPUT");
            tuple.setSrcModuleName("branch_coordinator"); tuple.setDestModuleName(MERGE_MODULE);
            tuple.setActualTupleId(tuple.getCloudletId());
            Branch merge = new Branch("merge", tuple.getActualTupleId(), MERGE_MI, OUTPUT_BYTES, MERGE_OUTPUT_BYTES);
            if (branchesByTupleId.putIfAbsent(merge.actualTupleId, new BranchRef(task, merge)) != null)
                throw new IllegalStateException("duplicate merge tuple ID " + merge.actualTupleId);
            task.branches.put("merge", merge);
            trace.record("merge_created", task.taskId, "merge", merge.actualTupleId, CloudSim.clock(),
                    "mi=" + MERGE_MI + ";input_bytes=" + OUTPUT_BYTES + ";output_bytes=" + MERGE_OUTPUT_BYTES);
            return tuple;
        }

        void complete(Tuple resultTuple) {
            BranchRef ref = resolve(resultTuple);
            TaskRecord task = ref.task;
            Branch merge = ref.branch;
            if (!task.partial || !"merge".equals(merge.name) || !FINAL_ENDPOINT.equals(resultTuple.getDestModuleName())
                    || !"MERGED_RESULT".equals(resultTuple.getTupleType()))
                throw new IllegalStateException("final result endpoint/type does not match its merge tuple");
            if (task.completed) throw new IllegalStateException("duplicate task terminal " + task.taskId);
            if (merge.executingNode == null || !Double.isNaN(merge.resultArrivalMs))
                throw new IllegalStateException("merge result missing execution or duplicated");
            merge.resultArrivalMs = CloudSim.clock();
            task.mergeEndMs = CloudSim.clock();
            task.completed = true;
            completedCount++;
            double localResult = task.branches.get("local").resultArrivalMs;
            double edgeResult = task.branches.get("edge").resultArrivalMs;
            double skew = Math.abs(localResult - edgeResult);
            double latency = task.mergeEndMs - task.creationTimeMs;
            trace.record("task_completed", task.taskId, "merge", merge.actualTupleId, task.mergeEndMs,
                    "mode=partial;latency_ms=" + latency + ";branch_skew_ms=" + skew
                    + ";bandwidth_bytes=" + task.bandwidthBytes + ";transfer_count=" + task.transferCount
                    + ";completed_count=" + completedCount);
        }

        void assertConsistent() {
            int expectedTupleCount = 0;
            for (TaskRecord task : tasksById.values()) expectedTupleCount += task.partial ? 3 : 1;
            if (tasksById.size() != expectedTasks || completedCount != expectedTasks
                    || branchesByTupleId.size() != expectedTupleCount)
                throw new IllegalStateException("run registry cardinality mismatch");
            for (TaskRecord task : tasksById.values()) {
                if (!task.completed) throw new IllegalStateException("task lifecycle incomplete: " + task.taskId);
                if (task.partial) {
                    if (!task.mergeStarted || task.branches.size() != 3)
                        throw new IllegalStateException("partial task missing branches/merge: " + task.taskId);
                    Branch local = task.branches.get("local"), edge = task.branches.get("edge"), merge = task.branches.get("merge");
                    if (local == null || edge == null || merge == null) throw new IllegalStateException("missing partial branch");
                    if (local.mi + edge.mi != TASK_MI || local.inputBytes + edge.inputBytes != INPUT_BYTES
                            || local.outputBytes + edge.outputBytes != OUTPUT_BYTES)
                        throw new IllegalStateException("partition conservation failed: " + task.taskId);
                    if (task.mergeEndMs < Math.max(local.resultArrivalMs, edge.resultArrivalMs))
                        throw new IllegalStateException("merge preceded both branch results: " + task.taskId);
                    if (merge.mi != MERGE_MI || merge.inputBytes != OUTPUT_BYTES || merge.outputBytes != MERGE_OUTPUT_BYTES)
                        throw new IllegalStateException("merge input contract mismatch: " + task.taskId);
                } else if (task.mergeStarted || task.branches.size() != 1 || !task.branches.containsKey("full")) {
                    throw new IllegalStateException("full task must have one branch and no merge: " + task.taskId);
                }
                for (Branch branch : task.branches.values()) {
                    if (branch.executingNode == null || Double.isNaN(branch.executionStartMs)
                            || Double.isNaN(branch.resultArrivalMs) || branch.resultArrivalMs < branch.executionStartMs)
                        throw new IllegalStateException("branch lifecycle incomplete: " + task.taskId + "/" + branch.name);
                    BranchRef owner = branchesByTupleId.get(branch.actualTupleId);
                    if (owner == null || owner.task != task || owner.branch != branch)
                        throw new IllegalStateException("tuple mapped to wrong task: " + branch.actualTupleId);
                }
            }
        }

        void writeSummary() throws IOException {
            Path path = output.resolve("mixed_summary.csv");
            try (BufferedWriter writer = Files.newBufferedWriter(path, StandardCharsets.UTF_8)) {
                writer.write("task_id,mode,full_action,creation_ms,local_result_ms,edge_result_ms,full_result_ms,merge_start_ms,merge_end_ms,latency_ms,branch_skew_ms,bandwidth_bytes,transfer_count,full_tuple_id,local_tuple_id,edge_tuple_id,merge_tuple_id");
                writer.newLine();
                for (TaskRecord task : tasksById.values()) {
                    Branch full = task.branches.get("full"), local = task.branches.get("local");
                    Branch edge = task.branches.get("edge"), merge = task.branches.get("merge");
                    String fullResult = full == null ? "" : Double.toString(full.resultArrivalMs);
                    String localResult = local == null ? "" : Double.toString(local.resultArrivalMs);
                    String edgeResult = edge == null ? "" : Double.toString(edge.resultArrivalMs);
                    String mergeStart = merge == null ? "" : Double.toString(merge.executionStartMs);
                    String mergeEnd = Double.toString(task.mergeEndMs);
                    String latency = Double.toString(task.mergeEndMs - task.creationTimeMs);
                    String skew = task.partial ? Double.toString(Math.abs(local.resultArrivalMs - edge.resultArrivalMs)) : "";
                    writer.write(csv(task.taskId) + "," + (task.partial ? "partial" : "full") + ","
                            + csv(task.fullAction) + "," + task.creationTimeMs + "," + localResult + ","
                            + edgeResult + "," + fullResult + "," + mergeStart + "," + mergeEnd + ","
                            + latency + "," + skew + "," + task.bandwidthBytes + "," + task.transferCount + ","
                            + (full == null ? "" : Integer.toString(full.actualTupleId)) + ","
                            + (local == null ? "" : Integer.toString(local.actualTupleId)) + ","
                            + (edge == null ? "" : Integer.toString(edge.actualTupleId)) + ","
                            + (merge == null ? "" : Integer.toString(merge.actualTupleId)));
                    writer.newLine();
                }
            }
        }
    }

    private static final class Trace implements AutoCloseable {
        private final BufferedWriter writer;
        Trace(Path path) throws IOException {
            writer = Files.newBufferedWriter(path, StandardCharsets.UTF_8);
            writer.write("event,task_id,branch,actual_tuple_id,sim_time_ms,detail");
            writer.newLine();
        }
        synchronized void record(String event, String taskId, String branch, int tupleId, double time, String detail) {
            try {
                writer.write(csv(event) + "," + csv(taskId) + "," + csv(branch) + "," + tupleId + "," + time + "," + csv(detail));
                writer.newLine(); writer.flush();
            } catch (IOException error) { throw new IllegalStateException("trace write failed", error); }
        }
        @Override public void close() throws IOException { writer.close(); }
    }

    private static String csv(String value) { return "\"" + value.replace("\"", "\"\"") + "\""; }
}
