package org.fog.test.perfeval;

import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
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
 * Isolated proof-of-concept for one divisible task split across Local and Edge.
 *
 * This is an experiment-owned source file. It does not modify iFogSim core.
 * The merge stage is a real CloudSim Cloudlet submitted to a Local FogDevice module.
 */
public final class PartialOffloadingFeasibilitySpike {
    private static final String APP_ID = "partial-offload-spike";
    private static final String LOCAL_MODULE = "local_worker";
    private static final String EDGE_MODULE = "edge_worker";
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
    private static final double TASK_EMIT_TIME_MS = 5.0;
    private static final double LOCAL_MIPS = 1000.0;
    private static final double EDGE_MIPS = 2800.0;
    private static final double LOCAL_EDGE_LATENCY_MS = 45.0;

    private enum SpikeEvents implements CloudSimTags { EMIT_TASK, BRANCH_RESULT, MERGE_RESULT }

    private PartialOffloadingFeasibilitySpike() { }

    public static void main(String[] args) {
        Path output = args.length > 0 ? Path.of(args[0]).toAbsolutePath()
                : Path.of("deliverables/10_iFogSim_Simulation/partial_offloading_spike/results/latest")
                        .toAbsolutePath();
        try {
            Files.createDirectories(output);
            try (Trace trace = new Trace(output.resolve("spike_trace.csv"))) {
                run(trace, output);
            }
        } catch (Throwable error) {
            error.printStackTrace(System.err);
            System.exit(2);
        }
    }

    private static void run(Trace trace, Path output) throws Exception {
        Log.disable();
        CloudSim.init(1, Calendar.getInstance(), false);

        FogBroker broker = new FogBroker("partial-spike-broker");
        TaskRegistry registry = new TaskRegistry(trace, output, broker.getId());

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

        TaskCoordinator coordinator = new TaskCoordinator("partial-task-coordinator", registry, local);
        BranchResultEndpoint branchEndpoint = new BranchResultEndpoint("partial-branch-endpoint",
                broker.getId(), APP_ID, local.getId(), 1.0, coordinator);
        FinalResultEndpoint finalEndpoint = new FinalResultEndpoint("partial-final-endpoint",
                broker.getId(), APP_ID, local.getId(), 1.0, coordinator);
        List<Actuator> actuators = new ArrayList<Actuator>();
        actuators.add(branchEndpoint);
        actuators.add(finalEndpoint);

        Application app = createApplication(broker.getId());
        ModuleMapping mapping = ModuleMapping.createModuleMapping();
        mapping.addModuleToDevice(LOCAL_MODULE, "local");
        mapping.addModuleToDevice(EDGE_MODULE, "edge");
        mapping.addModuleToDevice(MERGE_MODULE, "local");

        Controller controller = new Controller("partial-spike-controller", devices,
                Collections.emptyList(), actuators);
        controller.submitApplication(app, new ModulePlacementMapping(devices, app, mapping));

        trace.record("configuration", "task_mi=" + TASK_MI + ";input_bytes=" + INPUT_BYTES
                + ";output_bytes=" + OUTPUT_BYTES + ";local_share=" + LOCAL_SHARE
                + ";edge_share=" + EDGE_SHARE + ";merge_mi=" + MERGE_MI
                + ";merge_output_bytes=" + MERGE_OUTPUT_BYTES
                + ";local_mips=" + LOCAL_MIPS + ";edge_mips=" + EDGE_MIPS
                + ";local_edge_latency_ms=" + LOCAL_EDGE_LATENCY_MS
                + ";merge_model=CloudSim_Cloudlet_on_Local_merge_worker");

        new TaskEmitter("partial-task-emitter", local, registry);
        CloudSim.startSimulation();
        CloudSim.stopSimulation();

        if (!registry.completed) {
            throw new IllegalStateException("simulation ended before the two-branch merge completed");
        }
        registry.assertConsistent();
        System.out.println("PARTIAL_SPIKE_STATUS=PASS");
        System.out.println("SUMMARY=" + output.resolve("summary.txt"));
        System.out.println("TRACE=" + output.resolve("spike_trace.csv"));
    }

    private static Application createApplication(int userId) {
        Application app = Application.createApplication(APP_ID, userId);
        app.addAppModule(LOCAL_MODULE, 64, 1000, 10000);
        app.addAppModule(EDGE_MODULE, 64, 1000, 10000);
        app.addAppModule(MERGE_MODULE, 64, 1000, 10000);

        app.addAppEdge(LOCAL_MODULE, BRANCH_ENDPOINT, 1, (double) (OUTPUT_BYTES * LOCAL_SHARE),
                "LOCAL_RESULT", Tuple.DOWN, AppEdge.ACTUATOR);
        app.addTupleMapping(LOCAL_MODULE, "LOCAL_INPUT", "LOCAL_RESULT", new FractionalSelectivity(1.0));

        app.addAppEdge(EDGE_MODULE, BRANCH_ENDPOINT, 1, (double) (OUTPUT_BYTES * EDGE_SHARE),
                "EDGE_RESULT", Tuple.DOWN, AppEdge.ACTUATOR);
        app.addTupleMapping(EDGE_MODULE, "EDGE_INPUT", "EDGE_RESULT", new FractionalSelectivity(1.0));

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

        TaskEmitter(String name, InstrumentedFogDevice local, TaskRegistry registry) {
            super(name);
            this.local = local;
            this.registry = registry;
        }

        @Override public void startEntity() {
            send(getId(), TASK_EMIT_TIME_MS, SpikeEvents.EMIT_TASK);
        }

        @Override public void processEvent(SimEvent event) {
            if (event.getTag() == FogEvents.TUPLE_ACK) return;
            if (event.getTag() != SpikeEvents.EMIT_TASK)
                throw new IllegalStateException("unexpected emitter event " + event.getTag());

            registry.create(CloudSim.clock());
            long localMi = Math.round(TASK_MI * LOCAL_SHARE);
            long edgeMi = TASK_MI - localMi;
            long localInput = Math.round(INPUT_BYTES * LOCAL_SHARE);
            long edgeInput = INPUT_BYTES - localInput;
            long localOutput = Math.round(OUTPUT_BYTES * LOCAL_SHARE);
            long edgeOutput = OUTPUT_BYTES - localOutput;

            emitBranch("local", LOCAL_MODULE, "LOCAL_INPUT", localMi, localInput, localOutput);
            emitBranch("edge", EDGE_MODULE, "EDGE_INPUT", edgeMi, edgeInput, edgeOutput);
        }

        private void emitBranch(String branch, String module, String tupleType,
                long mi, long inputBytes, long outputBytes) {
            Tuple tuple = new Tuple(APP_ID, FogUtils.generateTupleId(), Tuple.UP,
                    mi, 1, inputBytes, outputBytes,
                    new UtilizationModelFull(), new UtilizationModelFull(), new UtilizationModelFull());
            tuple.setUserId(registry.userId);
            tuple.setTupleType(tupleType);
            tuple.setSrcModuleName("TASK_SOURCE");
            tuple.setDestModuleName(module);
            tuple.setActualTupleId(tuple.getCloudletId());
            registry.registerBranch(branch, tuple, mi, inputBytes, outputBytes);
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
            if (event.getTag() == FogEvents.TUPLE_ARRIVAL)
                coordinator.acceptBranch((Tuple) event.getData());
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
            if (event.getTag() == FogEvents.TUPLE_ARRIVAL)
                coordinator.acceptMerge((Tuple) event.getData());
            super.processEvent(event);
        }
    }

    private static final class TaskCoordinator extends SimEntity {
        private final TaskRegistry registry;
        private final InstrumentedFogDevice local;

        TaskCoordinator(String name, TaskRegistry registry, InstrumentedFogDevice local) {
            super(name);
            this.registry = registry;
            this.local = local;
        }

        @Override public void startEntity() { }

        public void acceptBranch(Tuple tuple) {
            sendNow(getId(), SpikeEvents.BRANCH_RESULT, tuple);
        }

        public void acceptMerge(Tuple tuple) {
            sendNow(getId(), SpikeEvents.MERGE_RESULT, tuple);
        }

        @Override public void processEvent(SimEvent event) {
            if (event.getTag() == FogEvents.TUPLE_ACK) return;
            if (event.getTag() == SpikeEvents.BRANCH_RESULT) {
                if (registry.branchResult((Tuple) event.getData())) {
                    Tuple mergeTuple = registry.beginMerge();
                    sendNow(local.getId(), FogEvents.TUPLE_ARRIVAL, mergeTuple);
                }
            } else if (event.getTag() == SpikeEvents.MERGE_RESULT) {
                registry.complete((Tuple) event.getData());
                CloudSim.abruptallyTerminate();
            } else {
                throw new IllegalStateException("unexpected coordinator event " + event.getTag());
            }
        }

        @Override public void shutdownEntity() { }
    }

    private static final class Branch {
        final String name;
        final int actualTupleId;
        final long mi;
        final long inputBytes;
        final long outputBytes;
        String executingNode;
        String executingModule;
        double executionStartMs = Double.NaN;
        double resultArrivalMs = Double.NaN;

        Branch(String name, int actualTupleId, long mi, long inputBytes, long outputBytes) {
            this.name = name;
            this.actualTupleId = actualTupleId;
            this.mi = mi;
            this.inputBytes = inputBytes;
            this.outputBytes = outputBytes;
        }
    }

    private static final class TaskRegistry {
        final int userId;
        private final Trace trace;
        private final Path output;
        private final Map<Integer, Branch> branches = new LinkedHashMap<Integer, Branch>();
        private double creationTimeMs;
        private long bandwidthBytes;
        private int transferCount;
        private boolean completed;
        private double mergeStartMs = Double.NaN;
        private double mergeEndMs = Double.NaN;

        TaskRegistry(Trace trace, Path output, int userId) {
            this.trace = trace;
            this.output = output;
            this.userId = userId;
        }

        void create(double now) {
            creationTimeMs = now;
            trace.record("task_created", "task_id=spike-task-001;creation_time_ms=" + now
                    + ";total_mi=" + TASK_MI + ";branch_count=2");
        }

        void registerBranch(String name, Tuple tuple, long mi, long inputBytes, long outputBytes) {
            Branch branch = new Branch(name, tuple.getActualTupleId(), mi, inputBytes, outputBytes);
            if (branches.put(branch.actualTupleId, branch) != null)
                throw new IllegalStateException("duplicate branch correlation id " + branch.actualTupleId);
            trace.record("branch_created", "task_id=spike-task-001;branch=" + name
                    + ";actual_tuple_id=" + branch.actualTupleId + ";mi=" + mi
                    + ";input_bytes=" + inputBytes + ";output_bytes=" + outputBytes
                    + ";sim_time_ms=" + CloudSim.clock());
        }

        void execution(Tuple tuple, String node, String module, double now) {
            Branch branch = branchFor(tuple);
            if (branch == null) return;
            if (branch.executingNode != null)
                throw new IllegalStateException("branch executed more than once: " + branch.name);
            branch.executingNode = node;
            branch.executingModule = module;
            branch.executionStartMs = now;
            String eventName = "merge".equals(branch.name) ? "merge_execution_start" : "branch_execution_start";
            trace.record(eventName, "task_id=spike-task-001;branch=" + branch.name
                    + ";node=" + node + ";module=" + module + ";mi=" + branch.mi
                    + ";sim_time_ms=" + now);
        }

        void transfer(Tuple tuple, String node, String direction, long bytes) {
            Branch branch = branchFor(tuple);
            if (branch == null) return;
            bandwidthBytes += bytes;
            transferCount++;
            trace.record("branch_transfer", "task_id=spike-task-001;branch=" + branch.name
                    + ";node=" + node + ";direction=" + direction + ";bytes=" + bytes
                    + ";actual_tuple_id=" + branch.actualTupleId + ";sim_time_ms=" + CloudSim.clock());
        }

        boolean branchResult(Tuple tuple) {
            Branch branch = branchFor(tuple);
            if (branch == null || "merge".equals(branch.name))
                throw new IllegalStateException("unmatched split-branch result " + tuple.getActualTupleId());
            if (!BRANCH_ENDPOINT.equals(tuple.getDestModuleName())
                    || !("LOCAL_RESULT".equals(tuple.getTupleType()) || "EDGE_RESULT".equals(tuple.getTupleType())))
                throw new IllegalStateException("unexpected branch result endpoint/type");
            if (branch.executingNode == null)
                throw new IllegalStateException("result arrived without recorded execution for " + branch.name);
            if (!Double.isNaN(branch.resultArrivalMs))
                throw new IllegalStateException("duplicate result for branch " + branch.name);
            branch.resultArrivalMs = CloudSim.clock();
            trace.record("branch_result_arrival", "task_id=spike-task-001;branch=" + branch.name
                    + ";actual_tuple_id=" + branch.actualTupleId + ";sim_time_ms=" + branch.resultArrivalMs);
            long arrived = branches.values().stream()
                    .filter(b -> !"merge".equals(b.name) && !Double.isNaN(b.resultArrivalMs)).count();
            if (arrived == 2) {
                if (!Double.isNaN(mergeStartMs)) throw new IllegalStateException("merge barrier fired twice");
                mergeStartMs = CloudSim.clock();
                trace.record("merge_barrier_satisfied", "task_id=spike-task-001;sim_time_ms=" + mergeStartMs
                        + ";reason=both_branch_results_arrived");
                return true;
            }
            return false;
        }

        Tuple beginMerge() {
            if (Double.isNaN(mergeStartMs)
                    || branches.values().stream().anyMatch(b -> "merge".equals(b.name)))
                throw new IllegalStateException("merge cannot start in current task state");
            Tuple tuple = new Tuple(APP_ID, FogUtils.generateTupleId(), Tuple.UP,
                    MERGE_MI, 1, OUTPUT_BYTES, MERGE_OUTPUT_BYTES,
                    new UtilizationModelFull(), new UtilizationModelFull(), new UtilizationModelFull());
            tuple.setUserId(userId);
            tuple.setTupleType("MERGE_INPUT");
            tuple.setSrcModuleName("branch_coordinator");
            tuple.setDestModuleName(MERGE_MODULE);
            tuple.setActualTupleId(tuple.getCloudletId());
            Branch merge = new Branch("merge", tuple.getActualTupleId(), MERGE_MI,
                    OUTPUT_BYTES, MERGE_OUTPUT_BYTES);
            if (branches.put(merge.actualTupleId, merge) != null)
                throw new IllegalStateException("duplicate merge correlation id");
            trace.record("merge_task_created", "task_id=spike-task-001;actual_tuple_id="
                    + merge.actualTupleId + ";module=" + MERGE_MODULE + ";mi=" + MERGE_MI
                    + ";input_bytes=" + OUTPUT_BYTES + ";output_bytes=" + MERGE_OUTPUT_BYTES
                    + ";sim_time_ms=" + CloudSim.clock());
            return tuple;
        }

        void complete(Tuple resultTuple) {
            if (completed) throw new IllegalStateException("duplicate task terminal event");
            Branch merge = branchFor(resultTuple);
            if (merge == null || !"merge".equals(merge.name))
                throw new IllegalStateException("terminal result is not correlated to merge task");
            if (!FINAL_ENDPOINT.equals(resultTuple.getDestModuleName())
                    || !"MERGED_RESULT".equals(resultTuple.getTupleType()))
                throw new IllegalStateException("unexpected final merge result endpoint/type");
            if (merge.executingNode == null)
                throw new IllegalStateException("merged result arrived without merge-module execution");
            if (!Double.isNaN(merge.resultArrivalMs))
                throw new IllegalStateException("duplicate merged result");
            merge.resultArrivalMs = CloudSim.clock();
            completed = true;
            mergeEndMs = CloudSim.clock();

            Branch local = branches.values().stream().filter(b -> b.name.equals("local")).findFirst().orElseThrow();
            Branch edge = branches.values().stream().filter(b -> b.name.equals("edge")).findFirst().orElseThrow();
            double branchMin = Math.min(local.resultArrivalMs, edge.resultArrivalMs);
            double branchMax = Math.max(local.resultArrivalMs, edge.resultArrivalMs);
            double latency = mergeEndMs - creationTimeMs;
            double mergeModuleToEndpointMs = merge.resultArrivalMs - merge.executionStartMs;

            String summary = "status=PASS\ntask_id=spike-task-001\n"
                    + "task_mi=" + TASK_MI + "\n"
                    + "local_mi=" + local.mi + "\n"
                    + "edge_mi=" + edge.mi + "\n"
                    + "split_mi_conservation=" + (local.mi + edge.mi) + "\n"
                    + "local_input_bytes=" + local.inputBytes + "\n"
                    + "edge_input_bytes=" + edge.inputBytes + "\n"
                    + "split_input_conservation=" + (local.inputBytes + edge.inputBytes) + "\n"
                    + "local_output_bytes=" + local.outputBytes + "\n"
                    + "edge_output_bytes=" + edge.outputBytes + "\n"
                    + "split_output_conservation=" + (local.outputBytes + edge.outputBytes) + "\n"
                    + "split_branch_count=2\n"
                    + "branch_result_count=2\n"
                    + "branch_result_skew_ms=" + (branchMax - branchMin) + "\n"
                    + "merge_module=" + MERGE_MODULE + "\n"
                    + "merge_mi=" + merge.mi + "\n"
                    + "merge_execution_start_ms=" + merge.executionStartMs + "\n"
                    + "merge_result_arrival_ms=" + merge.resultArrivalMs + "\n"
                    + "merge_module_to_endpoint_ms=" + mergeModuleToEndpointMs + "\n"
                    + "merge_result_received=true\n"
                    + "end_to_end_latency_ms=" + latency + "\n"
                    + "counted_transfer_bytes=" + bandwidthBytes + "\n"
                    + "transfer_count=" + transferCount + "\n"
                    + "merge_model=CloudSim_Cloudlet_on_Local_merge_worker\n";
            try {
                Files.writeString(output.resolve("summary.txt"), summary, StandardCharsets.UTF_8);
            } catch (IOException error) {
                throw new IllegalStateException("cannot write summary", error);
            }
            trace.record("merge_result_arrival", "task_id=spike-task-001;actual_tuple_id="
                    + merge.actualTupleId + ";sim_time_ms=" + merge.resultArrivalMs);
            trace.record("task_completed", "task_id=spike-task-001;status=completed;latency_ms=" + latency
                    + ";merge_module=" + MERGE_MODULE + ";merge_mi=" + MERGE_MI
                    + ";bandwidth_bytes=" + bandwidthBytes
                    + ";branch_result_skew_ms=" + (branchMax - branchMin));
        }

        void assertConsistent() {
            if (!completed || branches.size() != 3) throw new IllegalStateException("incomplete task registry");
            Branch local = branches.values().stream().filter(b -> b.name.equals("local")).findFirst().orElseThrow();
            Branch edge = branches.values().stream().filter(b -> b.name.equals("edge")).findFirst().orElseThrow();
            Branch merge = branches.values().stream().filter(b -> b.name.equals("merge")).findFirst().orElseThrow();

            long splitMi = local.mi + edge.mi;
            long splitInput = local.inputBytes + edge.inputBytes;
            long splitOutput = local.outputBytes + edge.outputBytes;
            if (splitMi != TASK_MI) throw new IllegalStateException("MI conservation failed: " + splitMi);
            if (splitInput != INPUT_BYTES) throw new IllegalStateException("input-byte partition failed: " + splitInput);
            if (splitOutput != OUTPUT_BYTES) throw new IllegalStateException("output-byte partition failed: " + splitOutput);

            for (Branch branch : new Branch[] { local, edge, merge }) {
                if (branch.executingNode == null || Double.isNaN(branch.resultArrivalMs))
                    throw new IllegalStateException("module lifecycle incomplete: " + branch.name);
                if (branch.resultArrivalMs < branch.executionStartMs)
                    throw new IllegalStateException("module result predates execution: " + branch.name);
            }
            if (merge.mi != MERGE_MI || merge.inputBytes != OUTPUT_BYTES
                    || merge.outputBytes != MERGE_OUTPUT_BYTES)
                throw new IllegalStateException("merge tuple contract mismatch");
            if (Double.isNaN(mergeStartMs) || merge.executionStartMs < mergeStartMs
                    || mergeEndMs < merge.executionStartMs)
                throw new IllegalStateException("invalid merge execution ordering");
            if (bandwidthBytes != 7800L || transferCount != 2)
                throw new IllegalStateException("unexpected transfer accounting: bytes=" + bandwidthBytes
                        + ", hops=" + transferCount);
        }

        private Branch branchFor(Tuple tuple) {
            return branches.get(tuple.getActualTupleId());
        }
    }

    private static final class Trace implements AutoCloseable {
        private final BufferedWriter writer;

        Trace(Path path) throws IOException {
            writer = Files.newBufferedWriter(path, StandardCharsets.UTF_8);
            writer.write("event,detail");
            writer.newLine();
        }

        synchronized void record(String event, String detail) {
            try {
                writer.write(csv(event) + "," + csv(detail));
                writer.newLine();
                writer.flush();
                System.out.println("SPIKE_EVENT " + event + " " + detail);
            } catch (IOException error) {
                throw new IllegalStateException("trace write failed", error);
            }
        }

        private static String csv(String value) {
            return "\"" + value.replace("\"", "\"\"") + "\"";
        }

        @Override public void close() throws IOException { writer.close(); }
    }
}
