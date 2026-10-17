# -*- coding: utf-8 -*-
"""动作数据表的共用读取器。

表是社区整理的官方动作数据，每秒 60 帧。所有拆解脚本都从这里取数，
免得每个文件各写一遍列索引。

用法:
    from _shared import load_actions, FPS
    rows = load_actions("path/to/动作数据表.xlsx")
"""
from __future__ import annotations

from openpyxl import load_workbook

FPS = 60

# 列索引（0 起）。表头见 docs 或 README。
COLS = {
    "group": 0,          # 名称（体型骨架，不是角色名）
    "id": 1,
    "action": 2,
    "startup": 4,        # 发生帧
    "duration": 5,       # 持续帧
    "hitstop_self": 7,
    "iframe_start": 10,
    "iframe_dur": 11,
    "end": 15,           # 动作结束帧
    "poise": 19,         # 削韧值
    "ult": 21,           # 大招回收
    "concerto": 22,      # 协奏回收
    "core1": 23,
    "core2": 24,
    "core3": 25,
}


# 缓存：整个工作簿只解析一次，各表按需物化。
# 之前按 (文件, 表) 缓存，结果是每读一张新表就重开一次 10MB 的 xlsx，
# 反而比不缓存更慢。
_WORKBOOKS: dict[str, object] = {}
_ROWS: dict[tuple[str, str, int], list[tuple]] = {}


def _workbook(xlsx: str):
    import os as _os
    key = _os.path.abspath(xlsx)
    if key not in _WORKBOOKS:
        _WORKBOOKS[key] = load_workbook(xlsx, data_only=True, read_only=True)
    return _WORKBOOKS[key]


def sheet_rows(xlsx: str, sheet: str, header: bool = False) -> list[tuple]:
    """读取一张表的数据行。

    ``header=False`` 跳过第一行（多数表第一行是表头），
    ``header=True`` 连表头一起返回（更新日志需要）。
    """
    import os as _os
    key = (_os.path.abspath(xlsx), sheet, 1 if header else 0)
    if key not in _ROWS:
        wb = _workbook(xlsx)
        if sheet in wb.sheetnames:
            _ROWS[key] = list(wb[sheet].iter_rows(min_row=1 if header else 2,
                                                  values_only=True))
        else:
            _ROWS[key] = []
    return _ROWS[key]


def clear_row_cache() -> None:
    """测试或换文件时清缓存。"""
    for wb in _WORKBOOKS.values():
        try:
            wb.close()
        except Exception:
            pass
    _WORKBOOKS.clear()
    _ROWS.clear()


def _num(v):
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        try:
            return float(v.strip())
        except ValueError:
            return None
    return None


def load_actions(xlsx: str) -> list[dict]:
    """把「角色-女」「角色-男」两页合成一张扁平的动作表。"""
    rows: list[dict] = []
    for sheet in ("角色-女", "角色-男"):
        for r in sheet_rows(xlsx, sheet):
            if not r or len(r) <= COLS["core3"]:
                continue
            action = r[COLS["action"]]
            if not action or not str(action).strip():
                continue
            item = {"sheet": sheet, "action": str(action).strip()}
            for key, idx in COLS.items():
                if key == "action":
                    continue
                v = r[idx]
                item[key] = v.strip() if isinstance(v, str) else v
            for key in ("startup", "duration", "iframe_start", "iframe_dur",
                        "end", "poise", "ult", "concerto", "core1", "core2",
                        "core3", "hitstop_self"):
                item[key] = _num(item.get(key))
            rows.append(item)
    return rows


def seconds(frames: float | None) -> float | None:
    return None if frames is None else round(frames / FPS, 3)
