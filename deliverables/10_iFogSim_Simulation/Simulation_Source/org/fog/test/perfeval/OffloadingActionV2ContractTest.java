package org.fog.test.perfeval;

import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Standalone acceptance checks for the Java side of the protocol-v2 action contract. */
public final class OffloadingActionV2ContractTest {
    private OffloadingActionV2ContractTest() { }

    public static void main(String[] args) {
        List<Integer> divisible = OffloadingActionV2.legalActionIds(
                "DATA_PARALLEL_DIVISIBLE", "frames-v1", true, true, true);
        check(divisible.equals(Arrays.asList(0, 1, 2, 3, 4, 5, 6, 7, 8)), "nine-action divisible mask");

        List<Integer> indivisible = OffloadingActionV2.legalActionIds(
                "INDIVISIBLE", null, true, true, true);
        check(indivisible.equals(Arrays.asList(0, 4, 8)), "indivisible mask");

        Map<String, Object> wire = new LinkedHashMap<String, Object>();
        wire.put("protocol_version", "2.0");
        wire.put("type", "action");
        wire.put("task_id", "task-7");
        wire.put("action_id", 2L);
        wire.put("action", "EDGE_PARTIAL_50");
        wire.put("remote_tier", "EDGE");
        wire.put("remote_fraction", 0.5);
        wire.put("local_fraction", 0.5);
        wire.put("model_version", "q2-test-u0");
        OffloadingActionV2.Action decoded = OffloadingActionV2.validateResponse(wire, "task-7", divisible);
        check(decoded == OffloadingActionV2.Action.EDGE_PARTIAL_50, "compound action decoding");

        expectFailure(() -> OffloadingActionV2.validateResponse(wire, "other-task", divisible),
                "task correlation");
        expectFailure(() -> OffloadingActionV2.validateResponse(wire, "task-7", Arrays.asList(0, 4)),
                "mask enforcement");
        wire.put("local_fraction", 0.9);
        expectFailure(() -> OffloadingActionV2.validateResponse(wire, "task-7", divisible),
                "fraction integrity");
        expectFailure(() -> OffloadingActionV2.legalActionIds(
                "DATA_PARALLEL_DIVISIBLE", null, true, true, true),
                "partition model requirement");

        int checkedPlans = 0;
        for (OffloadingActionV2.Action action : OffloadingActionV2.Action.values()) {
            OffloadingActionV2ExecutionPlan plan = OffloadingActionV2ExecutionPlan.create(
                    action, 10003L, 12001L, 1001L, 1200L);
            if (action.isPartial()) {
                check(plan.branches.size() == 2 && plan.requiresMerge, action.wireName + " branch count");
                check(plan.branches.get(0).name.equals("local"), action.wireName + " local branch");
                check(plan.branches.get(1).tier.equals(action.remoteTier.name()), action.wireName + " remote tier");
                check(plan.branches.get(0).mi + plan.branches.get(1).mi == 10003L,
                        action.wireName + " MI conservation");
                check(plan.branches.get(0).inputBytes + plan.branches.get(1).inputBytes == 12001L,
                        action.wireName + " input-byte conservation");
                check(plan.branches.get(0).outputBytes + plan.branches.get(1).outputBytes == 1001L,
                        action.wireName + " output-byte conservation");
                check(plan.mergeMi == 1200L && plan.mergeInputBytes == 1001L,
                        action.wireName + " merge contract");
            } else {
                check(plan.branches.size() == 1 && !plan.requiresMerge, action.wireName + " full branch count");
                check(plan.branches.get(0).mi == 10003L, action.wireName + " full MI");
            }
            checkedPlans++;
        }
        check(checkedPlans == 9, "all nine action execution plans");

        System.out.println("OffloadingActionV2ContractTest: PASS (42 checks; 9 execution plans)");
    }

    private static void check(boolean condition, String label) {
        if (!condition) throw new AssertionError("failed: " + label);
    }

    private static void expectFailure(Runnable action, String label) {
        try {
            action.run();
            throw new AssertionError("expected failure: " + label);
        } catch (IllegalArgumentException expected) {
            // expected rejection
        }
    }
}
