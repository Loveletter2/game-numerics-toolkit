"""Economy: how long does progression take, and where does it stall?

Battle-side numerics asks "how hard does this hit". Growth-side numerics asks
"how long until the player gets there, and where do they get stuck". Both are
the same job, and this module covers the second one.

The central quantity is not the cost itself but **time**:

    到达等级 N 所需天数 = 累计消耗(N) / 每日产出

Cost curves that look smooth in absolute numbers often produce a lumpy
days-to-reach curve, because income usually does not scale with cost. The
lumps are the chokepoints -- the places where players stop playing.

Why this matters for design
---------------------------
A 2x cost jump late in the game is invisible in a spreadsheet of costs, and
extremely visible to a player who has been stuck for a week. Converting to
days makes the shape honest.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass
class Progression:
    """A cost table plus the income used to pay for it."""

    label: str = ""
    levels: list[float] = None            # 每级消耗（绝对量）
    daily_income: float = 0.0

    def __post_init__(self) -> None:
        if self.levels is None:
            self.levels = []
        if self.daily_income < 0:
            raise ValueError("daily_income must not be negative")

    @property
    def total_cost(self) -> float:
        return sum(self.levels)

    def cumulative(self) -> list[float]:
        return cumulative_cost(self.levels)

    def days(self) -> list[float]:
        return days_to_reach(self.cumulative(), self.daily_income)


def cumulative_cost(per_level: Sequence[float]) -> list[float]:
    """Running total of a per-level cost list."""
    out: list[float] = []
    acc = 0.0
    for c in per_level:
        if c < 0:
            raise ValueError("costs must not be negative")
        acc += c
        out.append(acc)
    return out


def build_levels(base: float, growth: float, count: int,
                 ascension: dict[int, float] | None = None) -> list[float]:
    """Generate a per-level cost table from a simple geometric spec.

    ``ascension`` maps a level number to a multiplier applied at that level,
    which is how most games model ascension walls.
    """
    if count <= 0:
        raise ValueError("count must be positive")
    if base <= 0 or growth <= 0:
        raise ValueError("base and growth must be positive")
    asc = ascension or {}
    out = []
    for i in range(1, count + 1):
        cost = base * (growth ** (i - 1))
        cost *= asc.get(i, 1.0)
        out.append(cost)
    return out


def days_to_reach(cumulative: Sequence[float], daily_income: float) -> list[float]:
    """Days needed to afford each cumulative milestone."""
    if daily_income <= 0:
        raise ValueError("daily_income must be positive")
    return [c / daily_income for c in cumulative]


def level_gaps(cumulative: Sequence[float]) -> list[float]:
    """Cost of each single level, recovered from the cumulative curve."""
    out: list[float] = []
    prev = 0.0
    for c in cumulative:
        out.append(c - prev)
        prev = c
    return out


def incremental_days(days: Sequence[float]) -> list[float]:
    """Days spent on each single level (not cumulative)."""
    out: list[float] = []
    prev = 0.0
    for d in days:
        out.append(d - prev)
        prev = d
    return out


def chokepoints(days: Sequence[float], top: int = 5,
                threshold: float = 2.0) -> list[dict]:
    """The levels whose *incremental* wait spikes above the local norm.

    A chokepoint is where the per-level time is more than ``threshold`` times
    the median of its neighbours. Returns them sorted by severity.
    """
    inc = incremental_days(days)
    if not inc:
        return []
    rows = []
    for i, d in enumerate(inc):
        lo = max(0, i - 2)
        hi = min(len(inc), i + 3)
        window = [x for j, x in enumerate(inc[lo:hi], lo) if j != i]
        if not window:
            continue
        baseline = sorted(window)[len(window) // 2]
        if baseline <= 0:
            continue
        ratio = d / baseline
        if ratio >= threshold:
            rows.append({
                "level": i + 1,
                "days": round(d, 2),
                "baseline": round(baseline, 2),
                "severity": round(ratio, 2),
            })
    rows.sort(key=lambda r: -r["severity"])
    return rows[:top]


def smoothness(days: Sequence[float]) -> dict:
    """Summary statistics of the incremental time curve.

    ``cv`` (coefficient of variation) is the one to watch: a well-tuned
    progression tends to keep it low, because players tolerate "always a bit
    of a wait" better than "instant, instant, one week, instant".
    """
    inc = incremental_days(days)
    if not inc:
        return {"n": 0, "mean": 0.0, "std": 0.0, "cv": 0.0,
                "min": 0.0, "max": 0.0, "ratio": 0.0}
    n = len(inc)
    mean = sum(inc) / n
    var = sum((x - mean) ** 2 for x in inc) / n
    std = var ** 0.5
    return {
        "n": n,
        "mean": round(mean, 3),
        "std": round(std, 3),
        "cv": round(std / mean, 3) if mean else 0.0,
        "min": round(min(inc), 3),
        "max": round(max(inc), 3),
        "ratio": round(max(inc) / min(inc), 2) if min(inc) > 0 else float("inf"),
    }


def income_to_hit(days_target: float,
                  total_cost: float) -> float:
    """Daily income needed to reach the end in ``days_target`` days."""
    if days_target <= 0:
        raise ValueError("days_target must be positive")
    return total_cost / days_target


def flatten(days: Sequence[float], cap: float) -> list[float]:
    """Clip per-level waits at ``cap`` days and re-accumulate.

    Useful as a first pass when a cost curve produces one unacceptable
    chokepoint: cap the spike, then rescale the rest to hit the same total.
    """
    inc = incremental_days(days)
    clipped = [min(x, cap) for x in inc]
    out: list[float] = []
    acc = 0.0
    for c in clipped:
        acc += c
        out.append(acc)
    return out


def report(prog: Progression, top: int = 5) -> dict:
    days = prog.days()
    return {
        "label": prog.label,
        "levels": len(prog.levels),
        "total_cost": round(prog.total_cost, 1),
        "daily_income": prog.daily_income,
        "days_to_max": round(days[-1], 1) if days else 0.0,
        "smoothness": smoothness(days),
        "chokepoints": chokepoints(days, top=top),
    }


def format_report(rep: dict) -> str:
    s = rep["smoothness"]
    lines = [
        "养成节奏：%s" % (rep["label"] or "(未命名)"),
        "  等级数 %d   总消耗 %.1f   每日产出 %.1f   满级需要 %.1f 天"
        % (rep["levels"], rep["total_cost"], rep["daily_income"], rep["days_to_max"]),
        "  每级等待：均值 %.2f 天，标准差 %.2f，变异系数 %.2f，最长/最短 %.1f 倍"
        % (s["mean"], s["std"], s["cv"], s["ratio"]),
    ]
    if rep["chokepoints"]:
        lines.append("  卡点（该级等待超过邻居中位数的 2 倍）：")
        for c in rep["chokepoints"]:
            lines.append("    第 %2d 级  等待 %.2f 天  ≈ 邻域的 %.1f 倍"
                         % (c["level"], c["days"], c["severity"]))
    else:
        lines.append("  没有明显卡点。")
    return "\n".join(lines)
