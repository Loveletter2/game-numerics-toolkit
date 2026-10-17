"""拆解模块的单元测试：``python -m unittest discover -s tests -t .``

这些测试只碰纯函数（分类、解析、聚合），不需要真的读数据表，
所以跑得很快，也不会因为数据更新而失效。
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "deconstructions"))

import changelog      # noqa: E402
import energy         # noqa: E402
import energy_budget  # noqa: E402
import hitbox         # noqa: E402
import poise          # noqa: E402
import toughness      # noqa: E402


class TestHitboxParse(unittest.TestCase):
    def test_rect(self):
        self.assertEqual(hitbox.parse("矩形(100,200,300)"),
                         {"shape": "矩形", "dims": [100.0, 200.0, 300.0]})

    def test_cylinder(self):
        self.assertEqual(hitbox.parse("圆柱(1500,0,1200)"),
                         {"shape": "圆柱", "dims": [1500.0, 0.0, 1200.0]})

    def test_sphere_with_offsets(self):
        # 实际数据里球形后面常跟两个 0
        self.assertEqual(hitbox.parse("球形(5000,0,0)"),
                         {"shape": "球形", "dims": [5000.0, 0.0, 0.0]})

    def test_empty_and_unknown(self):
        self.assertIsNone(hitbox.parse(None))
        self.assertIsNone(hitbox.parse(""))
        self.assertIsNone(hitbox.parse("随便什么东西"))

    def test_no_numbers(self):
        self.assertEqual(hitbox.parse("指定目标"), {"shape": "指定目标", "dims": []})


class TestPoiseCategory(unittest.TestCase):
    def test_basic_labels(self):
        self.assertEqual(poise.category_of("大招-伤害"), "共鸣解放")
        self.assertEqual(poise.category_of("普攻第一段伤害"), "普攻")
        self.assertEqual(poise.category_of("重击-爆裂"), "重击")
        self.assertEqual(poise.category_of("闪避反击"), "闪避/反击")

    def test_unknown_falls_back(self):
        self.assertEqual(poise.category_of("某种没见过的动作"), "其他")


class TestEnergyBuckets(unittest.TestCase):
    def test_bucket_boundaries(self):
        self.assertEqual(energy.bucket_of(-5), "≤0（消耗）")
        self.assertEqual(energy.bucket_of(0.5), "0～1")
        self.assertEqual(energy.bucket_of(1.0), "0～1")   # 左开右闭
        self.assertEqual(energy.bucket_of(1.5), "1～2")
        self.assertEqual(energy.bucket_of(10), "5～10")
        self.assertEqual(energy.bucket_of(20), "10～20")
        self.assertEqual(energy.bucket_of(100), ">50")


class TestChangelogKind(unittest.TestCase):
    def test_priority_order(self):
        # 含「弹刀」的条目应该先命中弹刀类，而不是被判成别的
        self.assertEqual(changelog.kind_of("声骸技能.无冠者.A1 不可弹刀 → 可弹刀"),
                         "弹刀/格挡")
        self.assertEqual(changelog.kind_of("闪避无敌 0.3s → 0.35s"), "无敌与闪避")
        self.assertEqual(changelog.kind_of("伤痕.7塔中1.基础生命值 7123 → 5888"),
                         "敌人数值")
        self.assertEqual(changelog.kind_of("今汐.子弹初始大小.E4-1 (400,400,250) → (700,500,450)"),
                         "判定与子弹")

    def test_time_keywords(self):
        self.assertEqual(changelog.kind_of("某动作.发生帧 10 → 12"), "时间与帧")

    def test_unknown(self):
        self.assertEqual(changelog.kind_of("完全看不懂的一条"), "其他")


class TestEnergyBudget(unittest.TestCase):
    def test_grouping_and_coverage(self):
        rows = [
            {"name": "a", "cost": 125.0, "concerto": 60.0},
            {"name": "b", "cost": 125.0, "concerto": 80.0},
            {"name": "c", "cost": 100.0, "concerto": 90.0},
        ]
        res = energy_budget.analyse(rows)
        by = {r["cost"]: r for r in res["by_cost"]}
        self.assertEqual(by[125.0]["count"], 2)
        self.assertAlmostEqual(by[125.0]["median_concerto"], 70.0)
        # 70 * 0.5 / 125 = 28%
        self.assertAlmostEqual(by[125.0]["coverage"], 28.0)
        self.assertAlmostEqual(by[100.0]["coverage"], 45.0)


class TestToughness(unittest.TestCase):
    def _rows(self):
        return [{"level": 90, "toughness": 800, "recover": 20},
                {"level": 90, "toughness": 800, "recover": 20},
                {"level": 100, "toughness": 40, "recover": 1},
                {"level": 100, "toughness": 9999, "recover": 0}]

    def test_tier_counts(self):
        res = toughness.analyse(self._rows())
        self.assertEqual(res["rows"], 4)
        self.assertEqual(res["toughness_values"][800], 2)

    def test_break_cost_uses_ult_poise(self):
        res = toughness.analyse(self._rows())
        costs = {c["toughness"]: c for c in res["cost"]}
        self.assertIn(800, costs)
        # 800 / 400 = 2 个大招
        self.assertAlmostEqual(costs[800]["ults"], 2.0)

    def test_sentinel_excluded_from_cost(self):
        res = toughness.analyse(self._rows())
        self.assertNotIn(9999, [c["toughness"] for c in res["cost"]])


if __name__ == "__main__":
    unittest.main(verbosity=2)
