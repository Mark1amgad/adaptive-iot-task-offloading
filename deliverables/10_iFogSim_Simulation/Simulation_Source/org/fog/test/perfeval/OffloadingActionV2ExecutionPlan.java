package org.fog.test.perfeval;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Deterministic execution plan for translating a validated v2 action into
 * iFogSim branch Cloudlets. This is a planning/validation layer; it does not
 * itself submit tuples or claim simulator execution.
 */
public final class OffloadingActionV2ExecutionPlan {
    public static final String LOCAL_FULL_MODULE = "local_executor";
    public static final String EDGE_FULL_MODULE = "edge_executor";
    public static final String CLOUD_FULL_MODULE = "cloud_executor";
    public static final String MERGE_MODULE = "merge_executor";

    public static final class Branch {
        public final String name;
        public final String module;
        public final String tupleType;
        public final long mi;
        public final long inputBytes;
        public final long outputBytes;
        public final String tier;

        private Branch(String name, String module, String tupleType, long mi,
                long inputBytes, long outputBytes, String tier) {
            this.name = name; this.module = module; this.tupleType = tupleType;
            this.mi = mi; this.inputBytes = inputBytes; this.outputBytes = outputBytes;
            this.tier = tier;
        }
    }

    public final OffloadingActionV2.Action action;
    public final List<Branch> branches;
    public final boolean requiresMerge;
    public final long mergeMi;
    public final long mergeInputBytes;

    private OffloadingActionV2ExecutionPlan(OffloadingActionV2.Action action,
            List<Branch> branches, boolean requiresMerge, long mergeMi, long mergeInputBytes) {
        this.action = action;
        this.branches = Collections.unmodifiableList(branches);
        this.requiresMerge = requiresMerge;
        this.mergeMi = mergeMi;
        this.mergeInputBytes = mergeInputBytes;
    }

    public static OffloadingActionV2ExecutionPlan create(OffloadingActionV2.Action action,
            long taskMi, long inputBytes, long outputBytes, long mergeMi) {
        if (action == null) throw new IllegalArgumentException("action is required");
        if (taskMi <= 0 || inputBytes < 0 || outputBytes < 0 || mergeMi < 0)
            throw new IllegalArgumentException("invalid task/merge workload sizes");

        List<Branch> branches = new ArrayList<Branch>();
        if (!action.isPartial()) {
            String module = action == OffloadingActionV2.Action.LOCAL ? LOCAL_FULL_MODULE
                    : action.remoteTier == OffloadingActionV2.Tier.EDGE ? EDGE_FULL_MODULE : CLOUD_FULL_MODULE;
            String tier = action == OffloadingActionV2.Action.LOCAL ? "LOCAL" : action.remoteTier.name();
            branches.add(new Branch("full", module, "TASK_INPUT", taskMi,
                    inputBytes, outputBytes, tier));
            return new OffloadingActionV2ExecutionPlan(action, branches, false, 0, 0);
        }

        int percent = (int) Math.round(action.remoteFraction * 100.0);
        String suffix = Integer.toString(percent);
        String remote = action.remoteTier.name().toLowerCase();
        long remoteMi = Math.round(taskMi * action.remoteFraction);
        long localMi = taskMi - remoteMi;
        long remoteInput = Math.round(inputBytes * action.remoteFraction);
        long localInput = inputBytes - remoteInput;
        long remoteOutput = Math.round(outputBytes * action.remoteFraction);
        long localOutput = outputBytes - remoteOutput;

        branches.add(new Branch("local", "local_partial_" + suffix, "LOCAL_PARTIAL_INPUT",
                localMi, localInput, localOutput, "LOCAL"));
        branches.add(new Branch(remote, remote + "_partial_" + suffix,
                remote.toUpperCase() + "_PARTIAL_INPUT", remoteMi, remoteInput,
                remoteOutput, action.remoteTier.name()));

        long sumMi = 0, sumInput = 0, sumOutput = 0;
        for (Branch branch : branches) {
            sumMi += branch.mi; sumInput += branch.inputBytes; sumOutput += branch.outputBytes;
        }
        if (sumMi != taskMi || sumInput != inputBytes || sumOutput != outputBytes)
            throw new IllegalStateException("partial branch conservation invariant failed");
        return new OffloadingActionV2ExecutionPlan(action, branches, true, mergeMi, outputBytes);
    }

    private OffloadingActionV2ExecutionPlan() { throw new AssertionError(); }
}
