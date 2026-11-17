import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("generate_v2_aba_workload.py")
SPEC = importlib.util.spec_from_file_location("aba_generator", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class AbaWorkloadTests(unittest.TestCase):
    def test_three_ordered_regimes_and_boundaries(self):
        rows = MODULE.build(17, 10)
        self.assertEqual(len(rows), 30)
        self.assertEqual([rows[i]["regime_id"] for i in (0, 10, 20)], ["A", "B", "A"])
        self.assertEqual([rows[i]["regime_index"] for i in (0, 10, 20)], [0, 1, 2])
        self.assertEqual([rows[i]["sequence"] for i in (0, 10, 20)], [1, 11, 21])

    def test_return_A_replays_same_exogenous_task_profile(self):
        rows = MODULE.build(17, 12)
        fields = ("task_mi", "input_bytes", "output_bytes", "deadline_ms",
                  "arrival_gap_ms", "urgency_class", "wan_latency_ms")
        for index, (first, returned) in enumerate(zip(rows[:12], rows[24:36])):
            compared = fields if index > 0 else tuple(k for k in fields if k != "arrival_gap_ms")
            self.assertEqual(tuple(first[k] for k in compared), tuple(returned[k] for k in compared))

    def test_B_is_strictly_more_demanding_and_higher_latency(self):
        rows = MODULE.build(17, 10)
        a, b = rows[:10], rows[10:20]
        self.assertTrue(all(x["wan_latency_ms"] == 45.0 for x in a))
        self.assertTrue(all(x["wan_latency_ms"] == 160.0 for x in b))
        self.assertGreater(sum(x["task_mi"] for x in b), sum(x["task_mi"] for x in a))
        self.assertLess(sum(x["arrival_gap_ms"] for x in b[1:]), sum(x["arrival_gap_ms"] for x in a[1:]))

    def test_generation_is_seed_deterministic(self):
        self.assertEqual(MODULE.build(123, 10), MODULE.build(123, 10))
        self.assertNotEqual(MODULE.build(123, 10), MODULE.build(124, 10))


if __name__ == "__main__":
    unittest.main()
