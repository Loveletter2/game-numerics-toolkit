"""Sensitivity: which number actually moves the result?

A damage model has a dozen inputs. Most of them barely matter; one or two
dominate. This module finds out which, systematically.

The obvious first attempt is a classic tornado chart: scale every zone by
+-10% and rank by how much the total swings. **In a pure product model that
chart is flat.** Every zone gives exactly the same swing, because

    (1+p) * (1+q) * ...      scaling one factor by (1+e)
    -----------------  =  1+e
    (1+p) * (1+q) * ...      leaves the ratio unchanged

So a uniform relative perturbation cannot rank anything. That is not a bug,
it is a property of the model -- and it is worth knowing, because it means
"which zone is most sensitive" is the wrong question.

The questions that *do* differentiate are:

1. **Point sensitivity** -- one resource point buys different absolute
   amounts in different zones. ``sweep_points`` covers this, and it is what
   the player experiences.
2. **Headroom sensitivity** -- zones do not have equal realistic ranges. An
   attack zone might swing 30% between builds while an enemy-defence zone
   swings 5%. ``sweep_ranges`` takes those ranges as input and produces the
   tornado people actually expect.

Both are reported here. ``sweep`` (uniform) is kept because it is the thing
everyone reaches for first, and the fact that it comes out flat is worth
seeing once.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Mapping, Sequence

from .damage import DamageModel


@dataclass
class Sensitivity:
    zone: str
    base: float          # zone value before perturbation
    low: float           # total when scaled down
    high: float          # total when scaled up
    swing: float         # high - low, in damage
    swing_pct: float     # swing as a fraction of the unperturbed total
    investable: bool
    basis: str = "relative"   # relative | points | range


def _scaled(model: DamageModel, zone_name: str, factor: float) -> DamageModel:
    clone = copy.deepcopy(model)
    for z in clone.zones:
        if z.name == zone_name:
            z.value = z.value * factor
            break
    return clone


def _row(model: DamageModel, zone_name: str, factor: float,
         basis: str) -> Sensitivity:
    base_total = model.total()
    z = next(x for x in model.zones if x.name == zone_name)
    low = _scaled(model, zone_name, 1 - factor).total()
    high = _scaled(model, zone_name, 1 + factor).total()
    return Sensitivity(
        zone=zone_name,
        base=z.value,
        low=low,
        high=high,
        swing=high - low,
        swing_pct=(high - low) / base_total if base_total else 0.0,
        investable=z.investable,
        basis=basis,
    )


def sweep(model: DamageModel, pct: float = 0.10) -> list[Sensitivity]:
    """Uniform +-``pct`` on every zone.

    Kept for completeness, but expect a flat chart: in a product model this
    returns the same swing for every zone. Use :func:`sweep_points` or
    :func:`sweep_ranges` to rank anything.
    """
    if not 0 < pct < 1:
        raise ValueError("pct must be between 0 and 1")
    return [_row(model, z.name, pct, "relative") for z in model.zones]


def sweep_points(model: DamageModel, points: float = 1.0) -> list[Sensitivity]:
    """Add ``points`` resource units to each investable zone.

    This is the player-facing ranking. Zones differ because one point buys
    ``per_point_gain`` of value, and the same absolute gain is worth more in
    a small zone than in a large one.
    """
    base_total = model.total()
    rows = []
    for z in model.zones:
        if not z.investable:
            continue
        gain = z.per_point_gain * points
        factor = gain / z.value if z.value else 0.0
        boosted = _scaled(model, z.name, 1 + factor).total()
        rows.append(Sensitivity(
            zone=z.name,
            base=z.value,
            low=base_total,
            high=boosted,
            swing=boosted - base_total,
            swing_pct=(boosted - base_total) / base_total if base_total else 0.0,
            investable=True,
            basis="points",
        ))
    rows.sort(key=lambda s: -s.swing_pct)
    return rows


def sweep_ranges(model: DamageModel, ranges: Mapping[str, float]) -> list[Sensitivity]:
    """Per-zone realistic improvement ranges -> a tornado that ranks.

    ``ranges`` maps zone name to a fraction, e.g. ``{"ATK": 0.30, "DMG":
    0.15, "Defense": 0.05}``. Zones missing from the mapping are skipped.
    """
    rows = []
    for z in model.zones:
        if z.name not in ranges:
            continue
        pct = ranges[z.name]
        if not 0 < pct < 1:
            raise ValueError("range for %r must be between 0 and 1" % z.name)
        rows.append(_row(model, z.name, pct, "range"))
    return sorted(rows, key=lambda s: -s.swing_pct)


def rank(model: DamageModel, pct: float = 0.10) -> list[Sensitivity]:
    """``sweep`` sorted by swing. Flat by construction; see module docstring."""
    return sorted(sweep(model, pct), key=lambda s: -s.swing)


def top_lever(model: DamageModel, pct: float = 0.10) -> Sensitivity | None:
    rows = rank(model, pct)
    return rows[0] if rows else None


def investable_only(model: DamageModel, pct: float = 0.10) -> list[Sensitivity]:
    return [s for s in rank(model, pct) if s.investable]


def equalise(model: DamageModel,
             zones: Sequence[str] | None = None,
             pct: float = 0.10) -> list[dict]:
    """How much each zone would need to move to match the most sensitive one.

    Under a uniform sweep every zone already matches, so this is mostly a
    readability check. With :func:`sweep_ranges` it becomes useful: it tells
    you where the next balance change is cheapest.
    """
    rows = rank(model, pct)
    if not rows:
        return []
    target = rows[0].swing
    names = set(zones) if zones else None
    out = []
    for s in rows:
        if names and s.zone not in names:
            continue
        # swing 是 ±pct 两端的差，即 2*pct 的系数；换算成「每 1% 摆幅」
        per_pct = s.swing / (2 * pct) if s.swing else 0.0
        needed = (target / (2 * per_pct)) if per_pct else float("inf")
        out.append({
            "zone": s.zone,
            "needed_change_pct": None if needed == float("inf") else round(needed * 100, 1),
            "matches": rows[0].zone,
        })
    return out


def format_tornado(rows: Sequence[Sensitivity], width: int = 34) -> str:
    """Plain-text tornado."""
    if not rows:
        return "(没有乘区)"
    top = max(r.swing_pct for r in rows) or 1.0
    lines = ["%-14s %10s %10s %8s  %s" % ("乘区", "低", "高", "摆幅", "影响"),
             "-" * 70]
    for r in rows:
        bar = "#" * max(1, int(width * r.swing_pct / top))
        lines.append("%-14s %10.1f %10.1f %7.2f%%  %s%s" % (
            r.zone, r.low, r.high, r.swing_pct * 100, bar,
            "  (可投资)" if r.investable else ""))
    return "\n".join(lines)


def format_points(rows: Sequence[Sensitivity], points: float = 1.0) -> str:
    if not rows:
        return "(没有可投资的乘区)"
    lines = ["每投入 %.2g 点资源，各乘区的收益：" % points,
             "%-14s %12s %10s" % ("乘区", "当前值", "收益"),
             "-" * 40]
    for r in rows:
        lines.append("%-14s %12.2f %9.2f%%" % (r.zone, r.base, r.swing_pct * 100))
    return "\n".join(lines)
