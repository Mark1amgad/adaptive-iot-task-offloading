package org.fog.test.perfeval;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;

/**
 * Pure-JDK protocol-v2 action contract. This class validates the compound
 * action returned by Python before any iFogSim execution is scheduled.
 */
public final class OffloadingActionV2 {
    public enum Tier { EDGE, CLOUD }

    public enum Action {
        LOCAL(0, "LOCAL", null, 0.00),
        EDGE_PARTIAL_25(1, "EDGE_PARTIAL_25", Tier.EDGE, 0.25),
        EDGE_PARTIAL_50(2, "EDGE_PARTIAL_50", Tier.EDGE, 0.50),
        EDGE_PARTIAL_75(3, "EDGE_PARTIAL_75", Tier.EDGE, 0.75),
        EDGE_FULL(4, "EDGE_FULL", Tier.EDGE, 1.00),
        CLOUD_PARTIAL_25(5, "CLOUD_PARTIAL_25", Tier.CLOUD, 0.25),
        CLOUD_PARTIAL_50(6, "CLOUD_PARTIAL_50", Tier.CLOUD, 0.50),
        CLOUD_PARTIAL_75(7, "CLOUD_PARTIAL_75", Tier.CLOUD, 0.75),
        CLOUD_FULL(8, "CLOUD_FULL", Tier.CLOUD, 1.00);

        public final int id;
        public final String wireName;
        public final Tier remoteTier;
        public final double remoteFraction;

        Action(int id, String wireName, Tier remoteTier, double remoteFraction) {
            this.id = id;
            this.wireName = wireName;
            this.remoteTier = remoteTier;
            this.remoteFraction = remoteFraction;
        }

        public double localFraction() { return 1.0 - remoteFraction; }
        public boolean isPartial() { return remoteFraction > 0.0 && remoteFraction < 1.0; }

        public static Action fromId(int id) {
            for (Action action : values()) if (action.id == id) return action;
            throw new IllegalArgumentException("unknown v2 action_id: " + id);
        }

        public static Action fromName(String name) {
            for (Action action : values()) if (action.wireName.equals(name)) return action;
            throw new IllegalArgumentException("unknown v2 action: " + name);
        }
    }

    private OffloadingActionV2() { }

    public static List<Integer> legalActionIds(String splittability, String partitionModelId,
            boolean localAvailable, boolean edgeAvailable, boolean cloudAvailable) {
        boolean divisible = "DATA_PARALLEL_DIVISIBLE".equals(splittability);
        if (!divisible && !"INDIVISIBLE".equals(splittability))
            throw new IllegalArgumentException("unsupported splittability: " + splittability);
        if (divisible && (partitionModelId == null || partitionModelId.trim().isEmpty()))
            throw new IllegalArgumentException("divisible task requires partition_model_id");

        List<Integer> ids = new ArrayList<Integer>();
        if (localAvailable) ids.add(0);
        boolean partialAllowed = divisible && localAvailable;
        if (edgeAvailable) {
            if (partialAllowed) { ids.add(1); ids.add(2); ids.add(3); }
            ids.add(4);
        }
        if (cloudAvailable) {
            if (partialAllowed) { ids.add(5); ids.add(6); ids.add(7); }
            ids.add(8);
        }
        if (ids.isEmpty()) throw new IllegalArgumentException("no feasible offloading action");
        return Collections.unmodifiableList(ids);
    }

    public static Action validateResponse(Map<?, ?> response, String expectedTaskId,
            List<Integer> allowedActionIds) {
        if (!"2.0".equals(response.get("protocol_version")))
            throw new IllegalArgumentException("protocol version must be 2.0");
        if (!"action".equals(response.get("type")))
            throw new IllegalArgumentException("response type must be action");
        if (!expectedTaskId.equals(response.get("task_id")))
            throw new IllegalArgumentException("task_id correlation mismatch");

        int id = exactInteger(response.get("action_id"), "action_id");
        Action action = Action.fromId(id);
        if (!action.wireName.equals(response.get("action")))
            throw new IllegalArgumentException("action name/action_id mismatch");
        if (allowedActionIds == null || !allowedActionIds.contains(id))
            throw new IllegalArgumentException("selected action is not in the task feasibility mask");

        Object tier = response.get("remote_tier");
        String expectedTier = action.remoteTier == null ? null : action.remoteTier.name();
        if (expectedTier == null ? tier != null : !expectedTier.equals(tier))
            throw new IllegalArgumentException("remote_tier disagrees with action");
        requireFraction(response.get("remote_fraction"), action.remoteFraction, "remote_fraction");
        requireFraction(response.get("local_fraction"), action.localFraction(), "local_fraction");
        Object version = response.get("model_version");
        if (!(version instanceof String) || ((String) version).trim().isEmpty())
            throw new IllegalArgumentException("model_version must be non-empty");
        return action;
    }

    private static int exactInteger(Object value, String name) {
        if (!(value instanceof Number)) throw new IllegalArgumentException(name + " must be numeric");
        double number = ((Number) value).doubleValue();
        if (!Double.isFinite(number) || number != Math.rint(number))
            throw new IllegalArgumentException(name + " must be an exact integer");
        return (int) number;
    }

    private static void requireFraction(Object value, double expected, String name) {
        if (!(value instanceof Number)) throw new IllegalArgumentException(name + " must be numeric");
        double number = ((Number) value).doubleValue();
        if (!Double.isFinite(number) || Math.abs(number - expected) > 1e-9)
            throw new IllegalArgumentException(name + " disagrees with action catalogue");
    }
}
