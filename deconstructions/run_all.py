# -*- coding: utf-8 -*-
"""一条命令跑完 deconstructions 系列的全部分析，并生成汇总报告。

用法:
    python deconstructions/run_all.py <动作数据表.xlsx> <nanoka目录>
    python deconstructions/run_all.py ... --charts     # 顺带重画所有图
    python deconstructions/run_all.py ... --report docs/DATA-REPORT.md

每节会打印耗时。工作簿各页是分别读取的，所以整轮跑下来要几分钟。
"""
from __future__ import annotations

import io
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import energy          # noqa: E402
import frames          # noqa: E402
import energy_budget   # noqa: E402
import enemies         # noqa: E402
import hitbox          # noqa: E402
import multipliers     # noqa: E402
import poise           # noqa: E402
import recovery        # noqa: E402
import sonata          # noqa: E402
import stats as stats_mod   # noqa: E402
import toughness       # noqa: E402
import weapons         # noqa: E402
from _shared import load_actions   # noqa: E402

CASE_DPS = 90695.0     # 案例页那张表的队伍 DPS，用于击杀时间换算


def main():
    xlsx = sys.argv[1] if len(sys.argv) > 1 else r"data\鸣潮动作数据汇总.xlsx"
    nanoka = sys.argv[2] if len(sys.argv) > 2 else r"data\nanoka\3.7"
    want_charts = "--charts" in sys.argv
    report_path = None
    if "--report" in sys.argv:
        report_path = sys.argv[sys.argv.index("--report") + 1]

    char_dir = os.path.join(nanoka, "zh_character")
    results = []
    total_t0 = time.time()

    def step(label, fn):
        t0 = time.time()
        try:
            res = fn()
            ok = True
        except Exception as exc:      # 单节失败不影响其余
            res = {"error": str(exc)[:200]}
            ok = False
        dt = time.time() - t0
        print("%-22s %5.1fs  %s" % (label, dt, "ok" if ok else "FAILED"))
        results.append({"label": label, "seconds": round(dt, 1),
                        "ok": ok, "result": res})
        return res

    # 动作帧表一次读入，供三节共用
    frame_rows = step("读取动作帧表", lambda: load_actions(xlsx))
    if isinstance(frame_rows, list):
        results[-1]["result"] = {"actions": len(frame_rows),
                                 "sheets": sorted({r["sheet"] for r in frame_rows})}
    if isinstance(frame_rows, list):
        step("01 无敌窗口", lambda: {"windows": frames.dodge_windows(frame_rows)[:8]})

        step("02 协奏能量", lambda: energy.analyse(frame_rows))
        step("03 削韧值", lambda: poise.analyse(frame_rows))
        step("04 后摇", lambda: recovery.analyse(frame_rows))

    step("09 判定范围", lambda: hitbox.analyse(hitbox.load_raw(xlsx)))
    step("06 敌人血量", lambda: enemies.analyse(enemies.load(xlsx), CASE_DPS))
    step("14 敌人韧性", lambda: toughness.analyse(toughness.load(xlsx)))
    step("11 更新日志", lambda: _changelog(xlsx, char_dir))

    step("05 武器白值", lambda: weapons.analyse(
        json.load(io.open(os.path.join(nanoka, "weapon.json"), encoding="utf-8"))))
    step("07 角色成长", lambda: stats_mod.analyse(stats_mod.load_dir(char_dir)))
    step("08 声骸套装", lambda: sonata.analyse(
        json.load(io.open(os.path.join(nanoka, "sonata.json"), encoding="utf-8"))))
    step("10 技能倍率", lambda: multipliers.analyse(
        multipliers.load_dir(char_dir)))
    step("12/13 充能预算", lambda: energy_budget.analyse(
        energy_budget.load(char_dir)))

    if want_charts:
        step("重画所有图", lambda: _charts(xlsx, nanoka))

    elapsed = time.time() - total_t0
    print("---")
    print("完成 %d 节，总耗时 %.1fs" % (len(results), elapsed))

    if report_path:
        _write_report(report_path, results, elapsed)
        print("报告 ->", report_path)
    else:
        _write_report(os.path.join("docs", "DATA-REPORT.md"), results, elapsed)
        print("报告 -> docs/DATA-REPORT.md")


def _dodge(rows):
    from collections import defaultdict
    b = defaultdict(list)
    for r in rows:
        if "闪避" in r["action"] and r["iframe_dur"]:
            b[r["action"]].append(r["iframe_dur"])
    out = [{"action": a, "frames": max(v), "n": len(v)} for a, v in b.items()]
    out.sort(key=lambda x: -x["frames"])
    return out


def _changelog(xlsx, char_dir):
    import changelog
    return changelog.analyse(changelog.load_changes(xlsx),
                             changelog.load_names(char_dir))


def _charts(xlsx, nanoka):
    import subprocess
    here = os.path.dirname(os.path.abspath(__file__))
    subprocess.run([sys.executable, os.path.join(here, "charts.py"),
                    xlsx, nanoka], check=True)


def _write_report(path, results, elapsed):
    lines = ["# 数据拆解汇总报告",
             "",
             "由 `python deconstructions/run_all.py` 自动生成，"
             "内容全部来自本地数据表，不含手写数字。",
             "",
             "总耗时 %.1f 秒，共 %d 节。" % (elapsed, len(results)),
             ""]
    for r in results:
        lines.append("## %s" % r["label"])
        lines.append("")
        lines.append("耗时 %.1fs，状态 %s" % (r["seconds"],
                                            "ok" if r["ok"] else "FAILED"))
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(r["result"], ensure_ascii=False, indent=1)[:4000])
        lines.append("```")
        lines.append("")
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    io.open(path, "w", encoding="utf-8").write("\n".join(lines))


def _summary(items):
    return {"top": items}


if __name__ == "__main__":
    main()
