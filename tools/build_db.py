# -*- coding: utf-8 -*-
"""把动作数据表与敌人表装进 SQLite。

这是唯一需要 openpyxl 的一步（读 xlsx）；之后的查询全部走标准库 sqlite3。

用法:
    python tools/build_db.py <动作数据表.xlsx> data/game.db
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "deconstructions"))

from numerics.store import connect, create, insert_actions, insert_enemies  # noqa: E402

ENEMY_SHEET = "敌对属性列表"
C_NAME, C_LV, C_HP, C_DEF = 0, 3, 4, 6


def _num(v):
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        try:
            return float(v.strip())
        except ValueError:
            return None
    return None


def load_enemies(xlsx: str) -> list[dict]:
    from _shared import sheet_rows
    out = []
    for r in sheet_rows(xlsx, ENEMY_SHEET):
        if not r or len(r) <= C_DEF:
            continue
        name = r[C_NAME]
        level = _num(r[C_LV])
        hp = _num(r[C_HP])
        if not name or level is None or hp is None or hp <= 0:
            continue
        out.append({
            "name": str(name).strip(),
            "level": int(level),
            "hp": hp,
            "defense": _num(r[C_DEF]),
        })
    return out


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__.strip())
        return 2
    xlsx, db_path = argv[1], argv[2]

    from _shared import load_actions

    actions = load_actions(xlsx)
    enemies = load_enemies(xlsx)

    if os.path.exists(db_path):
        os.remove(db_path)
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)

    conn = connect(db_path)
    create(conn)
    n_actions = insert_actions(conn, actions)
    n_enemies = insert_enemies(conn, enemies)
    conn.close()

    print("已写入 %s" % db_path)
    print("  actions  %5d 行" % n_actions)
    print("  enemies  %5d 行" % n_enemies)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
