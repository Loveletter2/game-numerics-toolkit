"""energy-data.js 的校验：页面能不能正常加载，取决于这份数据。

这是「工具页面的数据契约」测试：字段齐、数值合法、角色数不为零。
页面本身跑在浏览器里，这里只守住数据这一侧。
"""
import io
import json
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "docs", "tools", "energy-data.js")
PAGE = os.path.join(ROOT, "docs", "tools", "energy-calculator.html")


def load():
    raw = io.open(DATA, encoding="utf-8").read()
    body = raw[raw.index("=") + 1:].strip().rstrip(";")
    return json.loads(body)


class TestEnergyData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load()
        cls.chars = cls.data["characters"]

    def test_page_and_data_exist(self):
        self.assertTrue(os.path.exists(DATA))
        self.assertTrue(os.path.exists(PAGE))

    def test_constants(self):
        self.assertAlmostEqual(self.data["ratio"], 0.5)
        self.assertEqual(self.data["concertoCap"], 100)

    def test_has_characters(self):
        self.assertGreaterEqual(len(self.chars), 30)

    def test_every_character_is_usable(self):
        for c in self.chars:
            with self.subTest(character=c["name"]):
                self.assertTrue(c.get("name"))
                self.assertGreater(c.get("cost", 0), 0)
                self.assertTrue(c.get("skills"), "角色没有可用动作")

    def test_skill_fields_valid(self):
        for c in self.chars:
            for s in c["skills"]:
                with self.subTest(character=c["name"], skill=s.get("name")):
                    self.assertIsInstance(s["concerto"], (int, float))
                    self.assertGreaterEqual(s["concerto"], 0)
                    self.assertIn(s["source"], ("official", "estimate"))
                    self.assertTrue(s["type"])

    def test_has_official_entries(self):
        official = [s for c in self.chars for s in c["skills"]
                    if s["source"] == "official"]
        self.assertGreater(len(official), 100)

    def test_known_character_matches_manual_analysis(self):
        """心：万阙垂天 20 + 两条变奏 10+10 = 40 协奏，这是手算核对过的。"""
        xin = next(c for c in self.chars if c["name"] == "心")
        self.assertEqual(xin["cost"], 125)
        picked = 0.0
        picked += next(s for s in xin["skills"] if "万阙垂天" in s["name"])["concerto"]
        picked += next(s for s in xin["skills"] if "应世相" in s["name"])["concerto"]
        picked += next(s for s in xin["skills"] if "照世相" in s["name"])["concerto"]
        self.assertAlmostEqual(picked, 40.0)
        self.assertAlmostEqual(picked * self.data["ratio"], 20.0)

    def test_suoming_has_the_big_single_grant(self):
        """锁暝的「刻心念」单条 40 点，是他充能的主要来源。"""
        suo = next(c for c in self.chars if c["name"] == "锁暝")
        big = [s for s in suo["skills"] if "刻心念" in s["name"]]
        self.assertTrue(big)
        self.assertAlmostEqual(big[0]["concerto"], 40.0)

    def test_data_is_js_not_json(self):
        raw = io.open(DATA, encoding="utf-8").read()
        self.assertTrue(raw.startswith("window.ENERGY_DATA"))
        self.assertTrue(raw.rstrip().endswith(";"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
