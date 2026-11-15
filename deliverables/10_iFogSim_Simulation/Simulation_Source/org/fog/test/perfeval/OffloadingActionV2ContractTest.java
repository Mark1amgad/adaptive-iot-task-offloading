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
                "DATA_PARALLEL_DIVISIBLE", "frames-v1", true, true, false);
        check(divisible.equals(Arrays.asList(0, 1, 2, 3, 4)), "divisible Edge mask");

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

        System.out.println("OffloadingActionV2ContractTest: PASS (7 checks)");
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
