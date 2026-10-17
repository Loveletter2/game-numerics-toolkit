#!/usr/bin/env python3
"""Command line entry point for the toolkit.

    python cli.py damage   --config examples/wuwa_demo.json
    python cli.py allocate --config examples/wuwa_demo.json --budget 10
    python cli.py gacha    --base-rate 0.006 --soft-pity 66 --hard-pity 80
    python cli.py curves   --levels 80
    python cli.py demo     --out out
    python cli.py sql      --db data/game.db --list
    python cli.py sql      --db data/game.db --query poise_top
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from numerics import (
    DamageModel, GachaConfig, allocation_report, Build, build_table, enumerate_builds,
    exponential, format_insights, insights, linear, logarithmic, piecewise,
    to_csv, to_markdown, to_xlsx,
)
from numerics.curves import curve_summary
from numerics.gacha import analytic_expected, naive_expectation, summary


def _load_raw(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load(path: str) -> DamageModel:
    return DamageModel.from_dict(_load_raw(path))


def _rule(char: str = "-", width: int = 62) -> str:
    return char * width


def cmd_damage(args: argparse.Namespace) -> int:
    model = _load(args.config)
    print(_rule("="))
    print(f"damage model: {model.label or '(unnamed)'}")
    print(_rule("="))
    print(f"{'zone':<16}{'value':>12}{'per point':>12}")
    for z in model.zones:
        print(f"{z.name:<16}{z.value:>12.4f}{z.per_point_gain:>12.4f}")
    print(_rule())
    print(f"total damage = {model.total():,.1f}")

    print("\nmarginal gain from one more point (higher = more diluted):")
    for name, gain in model.marginal_table():
        print(f"  {name:<16}{gain * 100:>7.3f}%")

    info = model.spread_gain(args.budget)
    print(f"\nspreading {args.budget:g} relative budget across "
          f"{int(info['investable_zones'])} zones:")
    print(f"  all-in on one zone : x{info['all_in_multiple']:.4f}")
    print(f"  spread evenly      : x{info['optimal_multiple']:.4f}")
    print(f"  difference         : {info['gap'] * 100:+.2f}%")

    print("\nlog-space share (magnitude map, not a budget split):")
    for name, share in model.log_share():
        print(f"  {name:<16}{share * 100:>7.2f}%")
    return 0


def cmd_allocate(args: argparse.Namespace) -> int:
    model = _load(args.config)
    rep = allocation_report(model, args.budget, step=args.step)
    print(_rule("="))
    print(f"resource allocation, budget = {args.budget:g} points")
    print(_rule("="))
    print(f"base damage = {rep['base_damage']:,.1f}\n")

    for key, title in (("optimal", "optimal (closed form)"),
                       ("greedy", "greedy (discrete)"),
                       ("all_in_one_zone", "all-in on one zone")):
        block = rep[key]
        dmg = block["damage"]
        gain = block["gain"]
        print(f"{title}")
        print(f"  damage = {dmg:,.1f}   gain = {gain * 100:+.2f}%")
        if "allocation" in block:
            items = sorted(block["allocation"].items(), key=lambda kv: -kv[1])
            parts = [f"{n}={p:.2f}" for n, p in items if p > 0]
            print(f"  split  = {', '.join(parts) or '(none)'}")
        else:
            print(f"  split  = {block['zone']} = {args.budget:g}")
        print()
    print(f"even spread beats all-in by {rep['gap_optimal_vs_all_in'] * 100:+.2f}%")
    return 0


def cmd_gacha(args: argparse.Namespace) -> int:
    cfg = GachaConfig(base_rate=args.base_rate,
                      soft_pity_start=args.soft_pity,
                      soft_pity_increment=args.soft_pity_increment,
                      hard_pity=args.hard_pity)
    print(_rule("="))
    print("gacha expectation")
    print(_rule("="))
    print(f"base rate        : {cfg.base_rate:.4%}")
    print(f"soft pity starts : pull {cfg.soft_pity_start}")
    print(f"hard pity        : pull {cfg.hard_pity}")
    print()
    print(f"naive 1/rate            = {naive_expectation(cfg):7.2f} pulls")
    print(f"analytic E[N]           = {analytic_expected(cfg):7.2f} pulls")
    s = summary(cfg, n_sim=args.n_sim, seed=args.seed)
    print(f"simulated E[N] (n={args.n_sim:,}) = {s['simulated_expectation']:7.2f} pulls")
    print()
    print(f"std dev = {s['std_dev']:.2f}   p50 = {s['p50']}   p90 = {s['p90']}   p99 = {s['p99']}")
    print(f"\nthe pity system cuts the average by "
          f"{(1 - s['analytic_expectation'] / naive_expectation(cfg)) * 100:.1f}% "
          f"vs. the headline rate")
    return 0


def cmd_curves(args: argparse.Namespace) -> int:
    n = args.levels
    curves = {
        "linear": linear(100, 12, n),
        "exponential": exponential(100, 1.045, n),
        "piecewise": piecewise(100, [(39, 18), (40, 5)], n),
        "logarithmic": logarithmic(100, 180, n),
    }
    print(_rule("="))
    print(f"growth curves, {n} levels")
    print(_rule("="))
    print(f"{'curve':<14}{'start':>8}{'end':>10}{'x':>8}"
          f"{'1st inc':>9}{'last inc':>10}{'ratio':>8}")
    for name, series in curves.items():
        s = curve_summary(series)
        print(f"{name:<14}{s['start']:>8.1f}{s['end']:>10.1f}"
              f"{s['multiple']:>8.2f}{s['first_increment']:>9.2f}"
              f"{s['last_increment']:>10.2f}"
              f"{(s['increment_ratio'] or 0):>8.2f}")
    print("\nratio < 1 : growth slows down (front-loaded feel)")
    print("ratio > 1 : growth accelerates (late-game inflation)")
    return 0


def cmd_table(args: argparse.Namespace) -> int:
    raw = _load_raw(args.config)
    model = DamageModel.from_dict(raw)

    # two ways to describe the candidates:
    #   "builds": [{"name": ..., "overrides": {...}}]  -- explicit, e.g. echo sets
    #   "grid":   {"zone": [v1, v2, ...]}              -- cartesian product
    if raw.get("builds"):
        builds = [Build(b["name"], b.get("overrides", {})) for b in raw["builds"]]
        source = f"{len(builds)} explicit builds"
    else:
        grid = _load_raw(args.grid) if args.grid else raw.get("grid", {})
        if not grid:
            raise SystemExit(
                "no candidates: add a 'grid' or 'builds' section to the config, "
                "or pass --grid"
            )
        builds = enumerate_builds(grid, max_builds=args.max_builds)
        source = f"{len(builds)} builds, {len(grid)} varying zones"

    rows = build_table(model, builds)
    info = insights(rows, model)

    out = Path(args.out)
    produced = [to_csv(rows, out / "builds.csv"),
                to_markdown(rows, out / "builds.md", top=args.top)]
    if not args.no_xlsx:
        try:
            produced.append(to_xlsx(rows, out / "builds.xlsx"))
        except RuntimeError as exc:
            print(f"(xlsx export skipped: {exc})")

    print(_rule("="))
    print(f"build table: {source}")
    print(_rule("="))
    print(f"{'rank':<6}{'build':<52}{'damage':>12}{'% best':>10}")
    for row in rows[:args.top]:
        name = row["build"]
        if len(name) > 50:
            name = name[:49] + "…"
        print(f"{row['rank']:<6}{name:<52}{row['damage']:>12,.1f}"
              f"{row['pct_of_best'] * 100:>9.2f}%")
    if len(rows) > args.top:
        print(f"... {len(rows) - args.top} more rows in the exported files")
    print()
    for line in format_insights(info):
        print("  · " + line)
    print()
    for path in produced:
        print(f"wrote {path}")
    return 0


def cmd_demo(args: argparse.Namespace) -> int:
    from numerics.report import plot_curves, plot_dilution, plot_gacha

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    model = _load("examples/wuwa_demo.json")
    plot_dilution(model, ["ATK", "DMG", "Amplify", "Final"],
                  out / "dilution.svg")
    plot_curves({
        "linear": linear(100, 12, 80),
        "exponential": exponential(100, 1.045, 80),
        "piecewise": piecewise(100, [(39, 18), (40, 5)], 80),
    }, out / "curves.svg")
    plot_gacha(GachaConfig(), out / "gacha.svg")

    rep = allocation_report(model, 10.0)
    (out / "report.json").write_text(
        json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"charts  -> {out / 'dilution.svg'}")
    print(f"          {out / 'curves.svg'}")
    print(f"          {out / 'gacha.svg'}")
    print(f"report  -> {out / 'report.json'}")
    print(f"optimal gain = {rep['optimal']['gain'] * 100:+.2f}% "
          f"(all-in: {rep['all_in_one_zone']['gain'] * 100:+.2f}%)")
    return 0


def cmd_sql(args: argparse.Namespace) -> int:
    """在 game.db 上跑 SQL：列预设、跑预设、或直接给一句 SQL。"""
    from numerics.store import PRESETS, connect, format_table, query

    if args.list:
        print("可用的预设查询：")
        for name, spec in PRESETS.items():
            print("  %-14s %s" % (name, spec["title"]))
        print("\n用法：python cli.py sql --db data/game.db --query poise_top")
        return 0

    if not args.query and not args.sql:
        print("需要 --list / --query / --sql 三者之一")
        return 2

    if not Path(args.db).exists():
        print("找不到数据库：%s" % args.db)
        print("先建库：python tools/build_db.py <动作数据表.xlsx> %s" % args.db)
        return 2

    conn = connect(args.db)
    try:
        if args.query:
            spec = PRESETS.get(args.query)
            if spec is None:
                print("没有这个预设：%s（用 --list 看全部）" % args.query)
                return 2
            print("== %s ==" % spec["title"])
            rows = query(conn, spec["sql"])
        else:
            rows = query(conn, args.sql)
    finally:
        conn.close()

    print(format_table(rows, limit=args.limit))
    return 0


def cmd_ttk(args: argparse.Namespace) -> int:
    """配装模型 + 输出轴 + 敌人血量 → 击杀时间。"""
    from numerics.ttk import Rotation, damage_share, ttk_report

    model = _load(args.config)
    rotation = Rotation.from_dict(_load_raw(args.rotation))

    targets = []
    for item in args.enemy or []:
        name, _, hp = item.partition(":")
        try:
            targets.append({"name": name or "敌人", "hp": float(hp)})
        except ValueError:
            print("敌人血量格式应为 名字:血量，收到 %r" % item)
            return 2
    if not targets:
        print("至少给一个 --enemy 名字:血量")
        return 2

    rep = ttk_report(model, rotation, targets)
    print("=" * 62)
    print("rotation: %s" % rep["rotation"])
    print("时长 %.2f 秒   总伤 %.1f   DPS %.1f" % (rep["seconds"], rep["damage"], rep["dps"]))
    print("=" * 62)
    print("%-18s %12s %10s %10s %6s" % ("目标", "血量", "TTK(秒)", "需几轮", "一轮杀"))
    print("-" * 62)
    for r in rep["targets"]:
        print("%-18s %12.0f %10.1f %10.2f %6s" % (
            r["target"], r["hp"], r["ttk"], r["rotations"],
            "是" if r["kill_in_one"] else "否"))

    if args.share:
        print("\n各动作伤害占比：")
        print("%-16s %12s %8s %7s" % ("动作", "伤害", "占比", "帧"))
        print("-" * 46)
        for row in damage_share(model, rotation):
            print("%-16s %12.1f %7.2f%% %7d" % (
                row["action"], row["damage"], row["share"], row["frames"]))
    return 0


def cmd_tornado(args: argparse.Namespace) -> int:
    """哪个乘区动了最影响结果。"""
    from numerics.sensitivity import (format_points, format_tornado,
                                      sweep_points, sweep_ranges)

    model = _load(args.config)

    print(format_points(sweep_points(model, points=args.points)))

    ranges = {}
    for item in args.range or []:
        name, _, pct = item.partition(":")
        try:
            ranges[name] = float(pct) / 100.0
        except ValueError:
            print("范围格式应为 乘区:百分比，收到 %r" % item)
            return 2
    if ranges:
        print()
        print("按各乘区的现实可调范围做摆幅（越大越值得动）：")
        print(format_tornado(sweep_ranges(model, ranges)))
    return 0


def cmd_economy(args: argparse.Namespace) -> int:
    """养成曲线：总消耗、满级天数、卡点。"""
    from numerics.economy import Progression, build_levels, chokepoints, format_report, report, smoothness

    cfg = _load_raw(args.config)
    spec = cfg.get("spec")
    if cfg.get("levels"):
        levels = cfg["levels"]
    elif spec:
        levels = build_levels(
            base=float(spec["base"]),
            growth=float(spec["growth"]),
            count=int(spec["count"]),
            ascension={int(k): float(v) for k, v in (spec.get("ascension") or {}).items()},
        )
    else:
        print("配置里需要 levels 或 spec")
        return 2

    income = args.income or float(cfg.get("daily_income", 0))
    if income <= 0:
        print("需要正数的每日产出：--income 或配置里的 daily_income")
        return 2

    prog = Progression(label=cfg.get("label", ""), levels=levels, daily_income=income)
    rep = report(prog, top=args.top)
    print(format_report(rep))

    if args.curve:
        days = prog.days()
        inc = []
        prev = 0.0
        for d in days:
            inc.append(d - prev)
            prev = d
        print("\n每级等待（天）：")
        step = max(1, len(inc) // args.points)
        for i in range(0, len(inc), step):
            bar = "#" * max(1, int(40 * inc[i] / max(inc)))
            print("  Lv%-3d %8.2f  %s" % (i + 1, inc[i], bar))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="numerics", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)

    d = sub.add_parser("damage", help="inspect a damage model")
    d.add_argument("--config", default="examples/wuwa_demo.json")
    d.add_argument("--budget", type=float, default=1.0)
    d.set_defaults(func=cmd_damage)

    a = sub.add_parser("allocate", help="solve the stat allocation problem")
    a.add_argument("--config", default="examples/wuwa_demo.json")
    a.add_argument("--budget", type=float, default=10.0)
    a.add_argument("--step", type=float, default=0.01)
    a.set_defaults(func=cmd_allocate)

    g = sub.add_parser("gacha", help="gacha expectation under a pity system")
    g.add_argument("--base-rate", type=float, default=0.006)
    g.add_argument("--soft-pity", type=int, default=66)
    g.add_argument("--soft-pity-increment", type=float, default=0.06)
    g.add_argument("--hard-pity", type=int, default=80)
    g.add_argument("--n-sim", type=int, default=200_000)
    g.add_argument("--seed", type=int, default=0)
    g.set_defaults(func=cmd_gacha)

    c = sub.add_parser("curves", help="compare growth curves")
    c.add_argument("--levels", type=int, default=80)
    c.set_defaults(func=cmd_curves)

    m = sub.add_parser("demo", help="generate charts and a sample report")
    m.add_argument("--out", default="out")
    m.set_defaults(func=cmd_demo)

    t = sub.add_parser("table", help="enumerate builds and export a ranked table")
    t.add_argument("--config", default="examples/wuwa_demo.json")
    t.add_argument("--grid", default=None,
                   help="separate JSON file containing a 'grid' section")
    t.add_argument("--out", default="out")
    t.add_argument("--top", type=int, default=15)
    t.add_argument("--max-builds", type=int, default=20000)
    t.add_argument("--no-xlsx", action="store_true")
    t.set_defaults(func=cmd_table)

    s = sub.add_parser("sql", help="query the game database with SQL")
    s.add_argument("--db", default="data/game.db")
    s.add_argument("--list", action="store_true", help="列出预设查询")
    s.add_argument("--query", default=None, help="预设查询名")
    s.add_argument("--sql", default=None, help="直接给一句 SQL")
    s.add_argument("--limit", type=int, default=20)
    s.set_defaults(func=cmd_sql)

    k = sub.add_parser("ttk", help="rotation -> dps -> time to kill")
    k.add_argument("--config", default="examples/wuwa_demo.json")
    k.add_argument("--rotation", default="examples/rotation_demo.json")
    k.add_argument("--enemy", action="append", metavar="名字:血量",
                   help="可重复，例如 --enemy 'Lv90:630254'")
    k.add_argument("--share", action="store_true", help="同时打印各动作伤害占比")
    k.set_defaults(func=cmd_ttk)

    o = sub.add_parser("tornado", help="which zone moves the result most")
    o.add_argument("--config", default="examples/wuwa_demo.json")
    o.add_argument("--points", type=float, default=1.0,
                   help="每投入多少点资源")
    o.add_argument("--range", action="append", metavar="乘区:百分比",
                   help="该乘区的现实可调范围，可重复，例如 --range ATK:30")
    o.set_defaults(func=cmd_tornado)

    e = sub.add_parser("economy", help="progression cost curve, days to max, chokepoints")
    e.add_argument("--config", default="examples/progression_demo.json")
    e.add_argument("--income", type=float, default=0.0, help="每日产出，覆盖配置里的值")
    e.add_argument("--top", type=int, default=5, help="列出几个卡点")
    e.add_argument("--curve", action="store_true", help="打印每级等待的柱状图")
    e.add_argument("--points", type=int, default=20)
    e.set_defaults(func=cmd_economy)

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

