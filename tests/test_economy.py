"""养成经济模块的测试：消耗曲线 → 天数 → 卡点。"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from numerics.economy import (          # noqa: E402
    Progression, build_levels, chokepoints, cumulative_cost, days_to_reach,
    flatten, format_report, income_to_hit, incremental_days, level_gaps,
    report, smoothness,
)


class TestCumulative(unittest.TestCase):
    def test_running_total(self):
        self.assertEqual(cumulative_cost([1, 2, 3]), [1, 3, 6])

    def test_rejects_negative(self):
        with self.assertRaises(ValueError):
            cumulative_cost([1, -1])

    def test_level_gaps_inverts_cumulative(self):
        self.assertEqual(level_gaps([1, 3, 6]), [1, 2, 3])

    def test_empty(self):
        self.assertEqual(cumulative_cost([]), [])


class TestDays(unittest.TestCase):
    def test_days_simple(self):
        self.assertEqual(days_to_reach([100, 300], 100), [1.0, 3.0])

    def test_zero_income_raises(self):
        with self.assertRaises(ValueError):
            days_to_reach([100], 0)

    def test_incremental_days(self):
        self.assertEqual(incremental_days([1.0, 3.0]), [1.0, 2.0])

    def test_income_to_hit(self):
        self.assertAlmostEqual(income_to_hit(10, 1000), 100.0)

    def test_income_to_hit_rejects_zero(self):
        with self.assertRaises(ValueError):
            income_to_hit(0, 1000)


class TestBuildLevels(unittest.TestCase):
    def test_geometric(self):
        lv = build_levels(base=100, growth=2.0, count=3)
        self.assertEqual(lv, [100, 200, 400])

    def test_ascension_multiplier(self):
        lv = build_levels(base=100, growth=1.0, count=3, ascension={2: 5.0})
        self.assertEqual(lv, [100, 500, 100])

    def test_rejects_bad_args(self):
        with self.assertRaises(ValueError):
            build_levels(0, 1.1, 10)
        with self.assertRaises(ValueError):
            build_levels(100, 1.1, 0)


class TestChokepoints(unittest.TestCase):
    def test_detects_a_spike(self):
        levels = [100.0] * 10
        levels[5] = 1000.0
        days = days_to_reach(cumulative_cost(levels), 100)
        hits = chokepoints(days)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["level"], 6)

    def test_flat_curve_has_none(self):
        levels = [100.0] * 10
        days = days_to_reach(cumulative_cost(levels), 100)
        self.assertEqual(chokepoints(days), [])

    def test_sorted_by_severity(self):
        levels = [100.0] * 12
        levels[3] = 500.0
        levels[9] = 2000.0
        days = days_to_reach(cumulative_cost(levels), 100)
        hits = chokepoints(days)
        self.assertGreaterEqual(len(hits), 2)
        self.assertEqual(hits[0]["level"], 10)

    def test_respects_top(self):
        levels = [100.0] * 20
        for i in (2, 6, 10, 14, 18):
            levels[i] = 900.0
        days = days_to_reach(cumulative_cost(levels), 100)
        self.assertLessEqual(len(chokepoints(days, top=2)), 2)

    def test_empty(self):
        self.assertEqual(chokepoints([]), [])


class TestSmoothness(unittest.TestCase):
    def test_constant_is_perfectly_smooth(self):
        days = [float(i) for i in range(1, 11)]
        s = smoothness(days)
        self.assertAlmostEqual(s["cv"], 0.0, places=6)
        self.assertAlmostEqual(s["ratio"], 1.0, places=6)

    def test_spike_raises_cv(self):
        days = [float(i) for i in range(1, 11)]
        spike = list(days)
        spike[5] = 100.0
        self.assertGreater(smoothness(spike)["cv"], smoothness(days)["cv"])

    def test_empty(self):
        self.assertEqual(smoothness([])["n"], 0)


class TestFlatten(unittest.TestCase):
    def test_caps_the_spike(self):
        # 输入是累计天数，所以必须是单调递增的
        days = [1.0, 3.0, 53.0, 57.0]      # 每级增量 = 1, 2, 50, 4
        out = flatten(days, cap=5.0)       # 增量被削成 1, 2, 5, 4
        self.assertAlmostEqual(out[2], 8.0)    # 1 + 2 + 5
        self.assertAlmostEqual(out[-1], 12.0)  # + 4

    def test_no_change_when_under_cap(self):
        days = [1.0, 3.0, 6.0]
        self.assertEqual(flatten(days, cap=10.0), days)


class TestProgression(unittest.TestCase):
    def test_total_cost(self):
        p = Progression(levels=[10, 20, 30], daily_income=10)
        self.assertEqual(p.total_cost, 60)

    def test_days(self):
        p = Progression(levels=[10, 20, 30], daily_income=10)
        self.assertEqual(p.days(), [1.0, 3.0, 6.0])

    def test_rejects_negative_income(self):
        with self.assertRaises(ValueError):
            Progression(levels=[1], daily_income=-1)

    def test_report_shape(self):
        p = Progression("t", [10, 20, 30], 10)
        rep = report(p)
        self.assertEqual(rep["levels"], 3)
        self.assertAlmostEqual(rep["days_to_max"], 6.0)
        self.assertIn("smoothness", rep)
        self.assertIn("chokepoints", rep)

    def test_format_report_runs(self):
        text = format_report(report(Progression("t", [10, 20], 10)))
        self.assertIn("养成节奏", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
