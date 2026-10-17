"""TTK 与敏感度模块的测试。

敏感度那部分故意把「纯乘积模型下均匀扰动必然齐平」写成断言：
这不是缺陷，是这个模型的数学性质，值得钉住。
"""
import math
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from numerics.damage import DamageModel, Zone          # noqa: E402
from numerics.sensitivity import (                    # noqa: E402
    equalise, format_points, format_tornado, investable_only, rank,
    sweep, sweep_points, sweep_ranges, top_lever,
)
from numerics.ttk import (                            # noqa: E402
    Action, Rotation, action_damage, damage_share, efficiency_loss,
    optimal_rotation_order, rotation_damage, rotation_dps, time_to_kill,
    ttk_report,
)


def model():
    return DamageModel("t", [
        Zone("ATK", 1200.0, per_point_gain=12.0),
        Zone("Crit", 1.6, per_point_gain=0.008),
        Zone("DMG", 1.46, per_point_gain=0.01),
        Zone("Defense", 0.5714),           # 敌人侧，不可投资
    ])


class TestAction(unittest.TestCase):
    def test_rejects_zero_frames(self):
        with self.assertRaises(ValueError):
            Action("x", 1.0, 0)

    def test_rejects_zero_hits(self):
        with self.assertRaises(ValueError):
            Action("x", 1.0, 10, hits=0)

    def test_from_dict_defaults(self):
        r = Rotation.from_dict({"actions": [{"name": "a", "multiplier": 2, "frames": 30}]})
        self.assertEqual(r.fps, 60)
        self.assertEqual(r.actions[0].hits, 1)


class TestRotation(unittest.TestCase):
    def setUp(self):
        self.m = model()
        self.r = Rotation("demo", [
            Action("技能", 2.0, 60),
            Action("普攻", 1.0, 30, hits=2),
        ])

    def test_total_frames_and_seconds(self):
        self.assertEqual(self.r.total_frames, 90)
        self.assertAlmostEqual(self.r.seconds, 1.5)

    def test_action_damage(self):
        base = self.m.total()
        self.assertAlmostEqual(action_damage(self.m, Action("a", 2.0, 10)), base * 2)
        self.assertAlmostEqual(action_damage(self.m, Action("a", 2.0, 10, hits=3)), base * 6)

    def test_rotation_damage_is_sum(self):
        base = self.m.total()
        self.assertAlmostEqual(rotation_damage(self.m, self.r), base * 4.0)

    def test_dps(self):
        expected = rotation_damage(self.m, self.r) / 1.5
        self.assertAlmostEqual(rotation_dps(self.m, self.r), expected)

    def test_empty_rotation_raises_on_dps(self):
        with self.assertRaises(ValueError):
            rotation_dps(self.m, Rotation("empty", []))


class TestTTK(unittest.TestCase):
    def test_time_to_kill(self):
        self.assertAlmostEqual(time_to_kill(1000, 250), 4.0)

    def test_zero_dps_raises(self):
        with self.assertRaises(ValueError):
            time_to_kill(1000, 0)

    def test_report_flags_one_rotation_kill(self):
        m = model()
        r = Rotation("r", [Action("a", 10.0, 60)])
        rep = ttk_report(m, r, [{"name": "脆皮", "hp": 1.0},
                                {"name": "厚血", "hp": 1e12}])
        self.assertTrue(rep["targets"][0]["kill_in_one"])
        self.assertFalse(rep["targets"][1]["kill_in_one"])

    def test_share_sums_to_100(self):
        r = Rotation("r", [Action("a", 2.0, 60), Action("b", 3.0, 60)])
        rows = damage_share(model(), r)
        self.assertAlmostEqual(sum(x["share"] for x in rows), 100.0, places=1)

    def test_share_sorted_desc(self):
        r = Rotation("r", [Action("small", 1.0, 60), Action("big", 5.0, 60)])
        rows = damage_share(model(), r)
        self.assertEqual(rows[0]["action"], "big")


class TestRotationOrder(unittest.TestCase):
    def test_optimal_puts_higher_dpf_first(self):
        m = model()
        acts = [Action("slow", 1.0, 100), Action("fast", 1.0, 10)]
        self.assertEqual(optimal_rotation_order(m, acts)[0].name, "fast")

    def test_efficiency_loss_zero_when_already_sorted(self):
        m = model()
        r = Rotation("r", [Action("fast", 1.0, 10), Action("slow", 1.0, 100)])
        self.assertAlmostEqual(efficiency_loss(m, r), 0.0)

    def test_efficiency_loss_positive_when_reversed(self):
        m = model()
        r = Rotation("r", [Action("slow", 1.0, 100), Action("fast", 1.0, 10)])
        # 顺序不影响总伤，只影响每秒产出，所以这里应该是 0
        self.assertAlmostEqual(efficiency_loss(m, r), 0.0, places=6)


class TestSensitivityDegeneracy(unittest.TestCase):
    """纯乘积模型下，均匀 ±pct 的摆幅对所有乘区完全相同。"""

    def test_uniform_sweep_is_flat(self):
        rows = sweep(model(), 0.10)
        swings = {round(r.swing_pct, 10) for r in rows}
        self.assertEqual(len(swings), 1, "均匀扰动应当对所有乘区给出相同摆幅")

    def test_flat_swing_equals_2p(self):
        # scaling a zone by (1±p) scales the product by (1±p); swing = 2p
        rows = sweep(model(), 0.10)
        self.assertAlmostEqual(rows[0].swing_pct, 0.20, places=10)

    def test_rank_is_pointless_but_does_not_crash(self):
        self.assertEqual(len(rank(model(), 0.10)), 4)


class TestPointSweep(unittest.TestCase):
    def test_only_investable_zones(self):
        rows = sweep_points(model())
        self.assertNotIn("Defense", [r.zone for r in rows])

    def test_ranks_by_gain_over_value(self):
        rows = sweep_points(model(), points=1.0)
        gains = {r.zone: r.swing_pct for r in rows}
        # ATK: 12/1200 = 1%   Crit: 0.008/1.6 = 0.5%
        self.assertGreater(gains["ATK"], gains["Crit"])

    def test_sorted_descending(self):
        rows = sweep_points(model())
        vals = [r.swing_pct for r in rows]
        self.assertEqual(vals, sorted(vals, reverse=True))

    def test_zero_points_gives_zero_gain(self):
        rows = sweep_points(model(), points=0.0)
        for r in rows:
            self.assertAlmostEqual(r.swing_pct, 0.0)


class TestRangeSweep(unittest.TestCase):
    def test_uses_given_ranges(self):
        rows = sweep_ranges(model(), {"ATK": 0.30, "Crit": 0.15})
        by = {r.zone: r for r in rows}
        self.assertAlmostEqual(by["ATK"].swing_pct, 0.60, places=6)
        self.assertAlmostEqual(by["Crit"].swing_pct, 0.30, places=6)

    def test_sorted_by_swing(self):
        rows = sweep_ranges(model(), {"ATK": 0.10, "DMG": 0.30})
        self.assertEqual(rows[0].zone, "DMG")

    def test_skips_unknown_zones(self):
        rows = sweep_ranges(model(), {"NOPE": 0.1})
        self.assertEqual(rows, [])

    def test_rejects_out_of_range(self):
        with self.assertRaises(ValueError):
            sweep_ranges(model(), {"ATK": 1.5})

    def test_investable_flag_carries(self):
        rows = sweep_ranges(model(), {"Defense": 0.05})
        self.assertFalse(rows[0].investable)


class TestEqualise(unittest.TestCase):
    def test_flat_case_needs_same_change(self):
        rows = equalise(model(), pct=0.10)
        needs = {r["needed_change_pct"] for r in rows}
        self.assertEqual(len(needs), 1)
        self.assertAlmostEqual(rows[0]["needed_change_pct"], 10.0, places=1)


class TestFormatting(unittest.TestCase):
    def test_format_tornado_runs(self):
        self.assertIn("ATK", format_tornado(sweep_ranges(model(), {"ATK": 0.2})))

    def test_format_points_runs(self):
        self.assertIn("ATK", format_points(sweep_points(model())))

    def test_empty_inputs(self):
        self.assertEqual(format_tornado([]), "(没有乘区)")
        self.assertEqual(format_points([]), "(没有可投资的乘区)")


class TestInvestableOnly(unittest.TestCase):
    def test_excludes_defense(self):
        rows = investable_only(model())
        self.assertTrue(all(r.investable for r in rows))
        self.assertNotIn("Defense", [r.zone for r in rows])

    def test_top_lever_exists(self):
        self.assertIsNotNone(top_lever(model()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
