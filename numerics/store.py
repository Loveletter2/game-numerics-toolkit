# -*- coding: utf-8 -*-
"""把游戏数据装进 SQLite，用 SQL 直接查。

为什么要有这一层：拆解脚本是为「一次回答一个问题」写的，每换一个问题就要改
Python。装进数据库之后，新问题基本就是一句 SQL 的事，不用碰代码。

只依赖标准库 ``sqlite3``，不引入任何第三方包。

用法:
    from numerics.store import connect, create, insert_actions, query, PRESETS

    conn = connect("data/actions.db")
    create(conn)
    insert_actions(conn, rows)          # rows 来自 deconstructions/_shared
    for r in query(conn, PRESETS["poise_top"]["sql"]):
        print(r["action"], r["poise"])
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable, Mapping, Sequence

SCHEMA = """
CREATE TABLE IF NOT EXISTS actions (
    id           INTEGER PRIMARY KEY,
    sheet        TEXT,
    grp          TEXT,      -- 体型骨架，不是角色名
    action       TEXT NOT NULL,
    startup      REAL,      -- 发生帧
    duration     REAL,      -- 持续帧
    hitstop      REAL,      -- 顿帧
    iframe_start REAL,
    iframe_frames REAL,     -- 无敌帧数
    end_frame    REAL,      -- 动作结束帧
    poise        REAL,      -- 削韧值
    ult          REAL,      -- 大招回收（共鸣能量）
    concerto     REAL       -- 协奏回收（协奏能量）
);

CREATE INDEX IF NOT EXISTS idx_actions_poise    ON actions(poise);
CREATE INDEX IF NOT EXISTS idx_actions_concerto ON actions(concerto);

CREATE TABLE IF NOT EXISTS enemies (
    id      INTEGER PRIMARY KEY,
    name    TEXT,
    level   INTEGER,
    hp      REAL,
    defense REAL
);

CREATE INDEX IF NOT EXISTS idx_enemies_level ON enemies(level);
"""

ACTION_COLUMNS = ("sheet", "grp", "action", "startup", "duration", "hitstop",
                  "iframe_start", "iframe_frames", "end_frame", "poise",
                  "ult", "concerto")
ENEMY_COLUMNS = ("name", "level", "hp", "defense")

# 来源字段名 -> 表字段名。deconstructions/_shared 用的是另一套名字，
# 这里显式对齐，免得 ETL 悄悄写进去一堆 NULL。
ACTION_ALIASES = {
    "group": "grp",
    "hitstop_self": "hitstop",
    "iframe_dur": "iframe_frames",
    "end": "end_frame",
}


def connect(path: str | Path) -> sqlite3.Connection:
    """打开（或新建）数据库；``:memory:`` 用于测试。"""
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def create(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def _insert(conn, table: str, columns: Sequence[str],
            rows: Iterable[Mapping]) -> int:
    placeholders = ", ".join("?" for _ in columns)
    sql = "INSERT INTO %s (%s) VALUES (%s)" % (
        table, ", ".join(columns), placeholders)
    payload = [tuple(r.get(c) for c in columns) for r in rows]
    conn.executemany(sql, payload)
    conn.commit()
    return len(payload)


def insert_actions(conn, rows: Iterable[Mapping]) -> int:
    """写入动作行，顺带把来源字段名映射成表字段名。"""
    def normalise(r: Mapping) -> dict:
        out = dict(r)
        for src, dst in ACTION_ALIASES.items():
            if dst not in out and src in out:
                out[dst] = out[src]
        return out
    return _insert(conn, "actions", ACTION_COLUMNS, (normalise(r) for r in rows))


def insert_enemies(conn, rows: Iterable[Mapping]) -> int:
    return _insert(conn, "enemies", ENEMY_COLUMNS, rows)


def query(conn: sqlite3.Connection, sql: str,
          params: Sequence = ()) -> list[dict]:
    """执行查询，返回 dict 列表。"""
    cur = conn.execute(sql, params)
    return [dict(r) for r in cur.fetchall()]


def format_table(rows: Sequence[Mapping], limit: int = 20,
                 max_col: int = 34) -> str:
    """把结果排成等宽表格，便于命令行阅读。"""
    if not rows:
        return "(无结果)"
    cols = list(rows[0].keys())
    shown = rows[:limit]

    def cell(v) -> str:
        if v is None:
            return "-"
        if isinstance(v, float):
            s = ("%.2f" % v).rstrip("0").rstrip(".")
            return s if s else "0"
        s = str(v)
        return s[:max_col - 1] + "…" if len(s) > max_col else s

    widths = [len(c) for c in cols]
    for r in shown:
        for i, c in enumerate(cols):
            widths[i] = max(widths[i], len(cell(r[c])))
    line = "  ".join(c.ljust(widths[i]) for i, c in enumerate(cols))
    sep = "  ".join("-" * w for w in widths)
    body = ["  ".join(cell(r[c]).ljust(widths[i]) for i, c in enumerate(cols))
            for r in shown]
    out = [line, sep] + body
    if len(rows) > limit:
        out.append("…… 共 %d 行，仅显示前 %d 行" % (len(rows), limit))
    return "\n".join(out)


# ---------------------------------------------------------------- 预设查询
# 都是"拿来就能跑"的问题，覆盖动作与敌人两张表。
PRESETS: dict[str, dict] = {
    "poise_top": {
        "title": "削韧最高的 15 个动作",
        "sql": """
            SELECT action, poise, concerto AS conc
            FROM actions
            WHERE poise IS NOT NULL AND poise > 0 AND poise < 10000
            ORDER BY poise DESC
            LIMIT 15
        """,
    },
    "iframe_top": {
        "title": "无敌帧最长的 15 个动作",
        "sql": """
            SELECT action, iframe_frames AS frames,
                   ROUND(iframe_frames / 60.0, 2) AS seconds
            FROM actions
            WHERE iframe_frames IS NOT NULL AND iframe_frames > 0
            ORDER BY iframe_frames DESC
            LIMIT 15
        """,
    },
    "recovery_top": {
        "title": "后摇最长的 15 个动作（结束帧 - 发生帧 - 持续帧）",
        "sql": """
            SELECT action,
                   end_frame - startup - COALESCE(duration, 0) AS recovery_frames,
                   ROUND((end_frame - startup - COALESCE(duration, 0)) / 60.0, 2)
                       AS seconds
            FROM actions
            WHERE startup IS NOT NULL AND end_frame IS NOT NULL
              AND end_frame > startup
              AND end_frame - startup - COALESCE(duration, 0) > 0
            ORDER BY recovery_frames DESC
            LIMIT 15
        """,
    },
    "energy_ratio": {
        "title": "大招回收 ÷ 协奏回收 的分布（两者都 > 0）",
        "sql": """
            SELECT ROUND(ult / concerto, 1) AS ratio,
                   COUNT(*)                 AS actions
            FROM actions
            WHERE ult > 0 AND concerto > 0
            GROUP BY ratio
            ORDER BY actions DESC
            LIMIT 15
        """,
    },
    "zero_poise": {
        "title": "完全不给削韧的动作有多少",
        "sql": """
            SELECT
                SUM(CASE WHEN poise IS NULL OR poise = 0 THEN 1 ELSE 0 END) AS no_poise,
                COUNT(*)                                                     AS total,
                ROUND(100.0 * SUM(CASE WHEN poise IS NULL OR poise = 0
                                       THEN 1 ELSE 0 END) / COUNT(*), 1)     AS percent
            FROM actions
        """,
    },
    "big_both": {
        "title": "同时给高协奏与高大招回收的动作",
        "sql": """
            SELECT action, concerto AS conc, ult
            FROM actions
            WHERE concerto >= 20 AND ult >= 10
            ORDER BY concerto DESC, ult DESC
            LIMIT 15
        """,
    },
    "enemy_levels": {
        "title": "敌人血量按等级汇总",
        "sql": """
            SELECT level, COUNT(*) AS enemies,
                   CAST(AVG(hp) AS INTEGER) AS avg_hp,
                   CAST(MIN(hp) AS INTEGER) AS min_hp,
                   CAST(MAX(hp) AS INTEGER) AS max_hp
            FROM enemies
            GROUP BY level
            ORDER BY level
        """,
    },
    "enemy_tough": {
        "title": "同一等级里的血量档位分布（看是不是查表值）",
        "sql": """
            SELECT level, CAST(hp AS INTEGER) AS hp, COUNT(*) AS shared_by
            FROM enemies
            GROUP BY level, CAST(hp AS INTEGER)
            HAVING COUNT(*) >= 5
            ORDER BY shared_by DESC
            LIMIT 15
        """,
    },
}
