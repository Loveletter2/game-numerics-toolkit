"""Growth-curve models.

A growth curve answers one question: *given a level, what is the stat?*
The shape of the curve is a design decision, not an accident -- linear
growth feels flat because every level adds the same absolute amount,
exponential growth explodes and makes late-game numbers meaningless,
and a piecewise curve front-loads the early game to create a sense of
progress without inflating the endgame.

All functions return a list indexed by level (index 0 == level 1).
"""
from __future__ import annotations

import math
from typing import Sequence


def linear(start: float, growth: float, levels: int) -> list[float]:
    """stat = start + growth * (level - 1)"""
    return [start + growth * i for i in range(levels)]


def exponential(start: float, rate: float, levels: int) -> list[float]:
    """stat = start * rate ** (level - 1)

    `rate` is the per-level multiplier, e.g. 1.045 for +4.5% per level.
    """
    return [start * (rate ** i) for i in range(levels)]


def logarithmic(start: float, scale: float, levels: int) -> list[float]:
    """stat = start + scale * ln(level)

    Diminishing returns: cheap early, almost flat late.
    """
    return [start + scale * math.log(i + 1) for i in range(levels)]


def piecewise(start: float, segments: Sequence[tuple[int, float]], levels: int) -> list[float]:
    """Piecewise-linear growth.

    `segments` is a sequence of ``(increment_count, growth_per_level)``
    pairs, consumed in order. For a 80-level curve that grows by 18 for
    the first 39 levels and by 5 afterwards::

        piecewise(100, [(39, 18), (40, 5)], 80)
    """
    if not segments:
        raise ValueError("segments must not be empty")
    out = [start]
    value = start
    remaining = levels - 1
    for count, growth in segments:
        take = min(count, remaining)
        for _ in range(take):
            value += growth
            out.append(value)
        remaining -= take
        if remaining <= 0:
            break
    while remaining > 0:  # continue with the last segment's slope
        value += segments[-1][1]
        out.append(value)
        remaining -= 1
    return out


def marginal(series: Sequence[float]) -> list[float]:
    """Level-to-level increment. The shape of this list *is* the curve's feel."""
    return [b - a for a, b in zip(series, series[1:])]


def fit_power_law(xs: Sequence[float], ys: Sequence[float]) -> tuple[float, float]:
    """Least-squares fit of ``y = a * x ** b`` in log-log space.

    Returns ``(a, b)``. Useful for checking whether a hand-made curve is
    secretly a power law -- most "custom" growth curves are.
    """
    if len(xs) != len(ys) or len(xs) < 2:
        raise ValueError("xs and ys must have the same length >= 2")
    lx = [math.log(x) for x in xs]
    ly = [math.log(y) for y in ys]
    n = len(lx)
    mx = sum(lx) / n
    my = sum(ly) / n
    denom = sum((x - mx) ** 2 for x in lx)
    if denom == 0:
        raise ValueError("xs must not be constant")
    b = sum((x - mx) * (y - my) for x, y in zip(lx, ly)) / denom
    a = math.exp(my - b * mx)
    return a, b


def curve_summary(series: Sequence[float]) -> dict:
    """Cheap diagnostics used when comparing two candidate curves."""
    if not series:
        raise ValueError("series must not be empty")
    inc = marginal(series)
    first, last = series[0], series[-1]
    return {
        "levels": len(series),
        "start": first,
        "end": last,
        "total_growth": last - first,
        "multiple": last / first if first else float("inf"),
        "first_increment": inc[0] if inc else 0.0,
        "last_increment": inc[-1] if inc else 0.0,
        # >1 means growth accelerates, <1 means it decays
        "increment_ratio": (inc[-1] / inc[0]) if inc and inc[0] else None,
    }
