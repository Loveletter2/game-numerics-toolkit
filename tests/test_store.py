"""SQL 数据层的测试：``python -m unittest discover -s tests -t .``

全部跑在内存数据库上，不读任何文件，也不依赖 openpyxl。
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from numerics.store import (          # noqa: E402
    PRESETS, connect, create, format_table, insert_actions, insert_enemies, query,
)


def sample_actions():
    # 故意用 _shared 的原始字段名，验证别名映射
    return [
        {"sheet": "角色-女", "group": "通用-中", "action": "大招-伤害",
         "startup": 30.0, "duration": 10.0, "hitstop_self": 3.0,
         "iframe_start": 1.0, "iframe_dur": 0.0, "end": 220.0,
         "poise": 400.0, "ult": 0.0, "concerto": 20.0},
        {"sheet": "角色-女", "group": "通用-中", "action": "普攻-1",
         "startup": 8.0, "duration": 4.0, "hitstop_self": 2.0,
         "iframe_start": None, "iframe_dur": 0.0, "end": 40.0,
         "poise": 26.7, "ult": 0.5, "concerto": 1.0},
        {"sheet": "角色-男", "group": "通用-大", "action": "闪避",
         "startup": 1.0, "duration": 20.0, "hitstop_self": None,
         "iframe_start": 1.0, "iframe_dur": 21.0, "end": 46.0,
         "poise": None, "ult": None, "concerto": 0.0},
    ]


class TestSchemaAndInsert(unittest.TestCase):
    def setUp(self):
        self.conn = connect(":memory:")
        create(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_insert_returns_count(self):
        self.assertEqual(insert_actions(self.conn, sample_actions()), 3)

    def test_aliases_are_mapped(self):
        """group/end/hitstop_self/iframe_dur 要落到表字段上，不能是 NULL。"""
        insert_actions(self.conn, sample_actions())
        row = query(self.conn, "SELECT * FROM actions WHERE action = '大招-伤害'")[0]
        self.assertEqual(row["grp"], "通用-中")
        self.assertEqual(row["end_frame"], 220.0)
        self.assertEqual(row["hitstop"], 3.0)

        dodge = query(self.conn, "SELECT * FROM actions WHERE action = '闪避'")[0]
        self.assertEqual(dodge["iframe_frames"], 21.0)

    def test_create_is_idempotent(self):
        create(self.conn)
        create(self.conn)
        self.assertEqual(query(self.conn, "SELECT COUNT(*) AS n FROM actions")[0]["n"], 0)


class TestQuery(unittest.TestCase):
    def setUp(self):
        self.conn = connect(":memory:")
        create(self.conn)
        insert_actions(self.conn, sample_actions())
        insert_enemies(self.conn, [
            {"name": "甲", "level": 90, "hp": 800.0, "defense": 1512.0},
            {"name": "乙", "level": 90, "hp": 800.0, "defense": 1512.0},
            {"name": "丙", "level": 100, "hp": 88014.0, "defense": 1600.0},
        ])

    def tearDown(self):
        self.conn.close()

    def test_returns_dicts(self):
        rows = query(self.conn, "SELECT action, poise FROM actions ORDER BY poise")
        self.assertIsInstance(rows[0], dict)
        self.assertIn("action", rows[0])

    def test_params_are_parameterised(self):
        rows = query(self.conn, "SELECT action FROM actions WHERE poise > ?", (100,))
        self.assertEqual([r["action"] for r in rows], ["大招-伤害"])

    def test_enemy_grouping(self):
        rows = query(self.conn, """
            SELECT level, COUNT(*) AS n FROM enemies GROUP BY level ORDER BY level
        """)
        self.assertEqual([(r["level"], r["n"]) for r in rows], [(90, 2), (100, 1)])


class TestPresets(unittest.TestCase):
    """每个预设都必须能在小数据集上跑通，不能有语法错。"""

    def setUp(self):
        self.conn = connect(":memory:")
        create(self.conn)
        insert_actions(self.conn, sample_actions())
        insert_enemies(self.conn, [
            {"name": "甲", "level": 90, "hp": 800.0, "defense": 1512.0},
        ])

    def tearDown(self):
        self.conn.close()

    def test_all_presets_run(self):
        for name, spec in PRESETS.items():
            with self.subTest(preset=name):
                rows = query(self.conn, spec["sql"])
                self.assertIsInstance(rows, list)

    def test_preset_has_title(self):
        for name, spec in PRESETS.items():
            with self.subTest(preset=name):
                self.assertTrue(spec["title"])

    def test_poise_top_excludes_sentinels(self):
        insert_actions(self.conn, [{
            "action": "哨兵", "poise": 99999.0, "concerto": 0.0, "ult": 0.0,
        }])
        rows = query(self.conn, PRESETS["poise_top"]["sql"])
        self.assertNotIn("哨兵", [r["action"] for r in rows])


class TestFormatTable(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(format_table([]), "(无结果)")

    def test_truncates_and_notes_remainder(self):
        rows = [{"n": i} for i in range(30)]
        text = format_table(rows, limit=5)
        self.assertIn("共 30 行", text)
        self.assertEqual(len(text.splitlines()), 2 + 5 + 1)

    def test_none_becomes_dash(self):
        self.assertIn("-", format_table([{"x": None}]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
