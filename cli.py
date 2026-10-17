#!/usr/bin/env python3
"""Command line entry point for the toolkit.

    python cli.py damage   --config examples/wuwa_demo.json
    python cli.py allocate --config examples/wuwa_demo.json --budget 10
    python cli.py gacha    --base-rate 0.006 --soft-pity 66 --hard-pity 80
    python cli.py curves   --levels 80
    python cli.py demo     --out out
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

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

