import unittest

from analyze_v2_policy_comparison import find_recovery_window


def task(sequence, latency, outcome="ON_TIME", terminal_time=None):
    return {
        "sequence": sequence,
        "latency_ms": latency,
        "outcome": outcome,
        "terminal_time_ms": terminal_time if terminal_time is not None else sequence * 100.0,
    }


class AbaRecoveryTests(unittest.TestCase):
    def test_first_qualifying_window_and_elapsed_time(self):
        items = [task(i, 150.0 if i < 4 else 105.0, terminal_time=1000.0 + i * 100.0)
                 for i in range(31, 41)]
        recovered, elapsed = find_recovery_window(0.0, 100.0, items, 900.0)
        self.assertIsNotNone(recovered)
        self.assertEqual(recovered["window_start_sequence"], 31)
        self.assertEqual(recovered["window_end_sequence"], 40)
        self.assertEqual(elapsed, 1100.0)

    def test_no_recovery_when_deadline_burden_exceeds_tolerance(self):
        items = [task(i, 100.0, "LATE" if i == 35 else "ON_TIME") for i in range(31, 41)]
        recovered, elapsed = find_recovery_window(0.0, 100.0, items, 3000.0)
        self.assertIsNone(recovered)
        self.assertIsNone(elapsed)

    def test_no_recovery_when_latency_never_returns_to_baseline(self):
        items = [task(i, 130.0) for i in range(31, 41)]
        recovered, elapsed = find_recovery_window(0.0, 100.0, items, 3000.0)
        self.assertIsNone(recovered)
        self.assertIsNone(elapsed)

    def test_incomplete_window_is_not_recovery(self):
        items = [task(i, None, "UNRESOLVED_AT_HORIZON") for i in range(31, 41)]
        recovered, elapsed = find_recovery_window(0.0, 100.0, items, 3000.0)
        self.assertIsNone(recovered)
        self.assertIsNone(elapsed)

    def test_insufficient_return_phase_is_not_extrapolated(self):
        items = [task(i, 100.0) for i in range(31, 39)]
        recovered, elapsed = find_recovery_window(0.0, 100.0, items, 3000.0)
        self.assertIsNone(recovered)
        self.assertIsNone(elapsed)


if __name__ == "__main__":
    unittest.main()
