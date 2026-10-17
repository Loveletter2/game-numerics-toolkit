"""Multi-zone damage model.

Most modern action RPGs compute damage as a **product** of independent
zones::

    damage = atk_or_hp * multiplier * crit * dmg_bonus * amplify
             * resistance * defense * final * vulnerability

The product structure is the whole story. Because every zone multiplies,
adding a fixed amount to a *small* zone is worth more than adding the same
amount to a *large* zone::

    relative_gain = delta / zone_value

That single line is the mathematical statement of "dilution" (稀释), and
every "stack stats evenly" piece of advice in the community is a corollary
of it. This module makes the structure explicit so it can be measured
instead of argued about.

Units
-----
One "resource point" is an abstract unit defined by the user. Set
``Zone.per_point_gain`` to how much *zone value* one point buys. For a
zone whose value is expressed in absolute attack, one point (= 1% attack
on a 1200-attack character) buys 12. For a zone expressed as a
multiplier such as ``1.46``, one point (= 1% bonus damage) buys 0.01.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable, Sequence


@dataclass
class Zone:
    """One multiplicative factor of the damage formula."""

    name: str
    value: float
    per_point_gain: float = 0.0
    note: str = ""

    def __post_init__(self) -> None:
        if self.value <= 0:
            raise ValueError(f"zone {self.name!r} must have a positive value")
        if self.per_point_gain < 0:
            raise ValueError(f"zone {self.name!r} must not have a negative gain")

    @property
    def investable(self) -> bool:
        return self.per_point_gain > 0


@dataclass
class DamageModel:
    """A product of zones."""

    label: str = ""
    zones: list[Zone] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.zones:
            raise ValueError("a damage model needs at least one zone")

    # ---------------------------------------------------------------- core
    def total(self) -> float:
        out = 1.0
        for z in self.zones:
            out *= z.value
        return out

    def values(self) -> dict[str, float]:
        return {z.name: z.value for z in self.zones}

    def zone(self, name: str) -> Zone:
        for z in self.zones:
            if z.name == name:
                return z
        raise KeyError(f"unknown zone: {name}")

    # ------------------------------------------------------- marginal gain
    def marginal_gain(self, name: str, points: float = 1.0) -> float:
        """Relative damage gain from spending ``points`` on one zone.

        ``gain = (delta / zone_value)`` where ``delta = points * per_point_gain``.
        This is the dilution formula in code form.
        """
        z = self.zone(name)
        if not z.investable:
            return 0.0
        return (points * z.per_point_gain) / z.value

    def marginal_table(self, points: float = 1.0) -> list[tuple[str, float]]:
        """Every investable zone ranked by the gain from one more point."""
        rows = [(z.name, self.marginal_gain(z.name, points))
                for z in self.zones if z.investable]
        rows.sort(key=lambda r: r[1], reverse=True)
        return rows

    def cheapest_zone(self, points: float = 1.0) -> str:
        """The zone with the highest return -- i.e. the most diluted one."""
        table = self.marginal_table(points)
        if not table:
            raise ValueError("no investable zones")
        return table[0][0]

    # ------------------------------------------------------- dilution curve
    def dilution_curve(self, name: str, max_points: float = 100.0,
                       steps: int = 41) -> tuple[list[float], list[float]]:
        """Damage as a function of repeatedly dumping points into one zone.

        Note the exact shape: absolute damage grows *linearly* with points
        (one point always adds the same amount), which is why "damage vs
        investment" plots as a straight line. The dilution lives in the
        *relative* return, which decays like ``1 / zone_value`` -- see
        :meth:`marginal_curve` for the curve people actually mean.

        Returns ``(points, damage)``.
        """
        z = self.zone(name)
        base_total = self.total()
        xs: list[float] = []
        ys: list[float] = []
        for i in range(steps):
            p = max_points * i / (steps - 1)
            new_value = z.value + p * z.per_point_gain
            xs.append(p)
            ys.append(base_total * new_value / z.value)
        return xs, ys

    def marginal_curve(self, name: str, max_points: float = 100.0,
                       steps: int = 41) -> tuple[list[float], list[float]]:
        """Relative gain of the *next* point, as the zone grows.

        This is the dilution curve. It is hyperbolic and strictly
        decreasing: the first point is worth ``e / Z`` and the n-th is
        worth ``e / (Z + n * e)``.

        Returns ``(points_already_invested, relative_gain_per_point)``.
        """
        z = self.zone(name)
        xs: list[float] = []
        ys: list[float] = []
        for i in range(steps):
            p = max_points * i / (steps - 1)
            xs.append(p)
            ys.append(z.per_point_gain / (z.value + p * z.per_point_gain))
        return xs, ys

    # --------------------------------------------------------- redistribution
    def spread_gain(self, budget: float) -> dict[str, float]:
        """How much better is *even* distribution than *all-in*?

        With a relative budget ``B`` (each zone can be multiplied by
        ``1 + x_i`` with ``sum(x_i) == B``), the product is maximised when
        every ``x_i`` is equal::

            optimal = (1 + B / n) ** n
            all_in  = 1 + B

        Example: B = 1.0 across 4 zones gives ``1.25 ** 4 = 2.44`` versus
        ``2.0`` -- a 22% difference in damage for identical resources.
        """
        n = sum(1 for z in self.zones if z.investable)
        if n == 0:
            raise ValueError("no investable zones")
        optimal = (1.0 + budget / n) ** n
        all_in = 1.0 + budget
        return {
            "investable_zones": float(n),
            "optimal_multiple": optimal,
            "all_in_multiple": all_in,
            "gap": optimal / all_in - 1.0,
        }

    # ------------------------------------------------------------ log view
    def log_share(self) -> list[tuple[str, float]]:
        """Share of ``ln(total)`` held by each zone.

        Read this as "how many times this zone magnifies the base" rather
        than as a percentage of damage: a zone worth 1200 dwarfs a zone
        worth 1.6 in log space even though both are equally necessary.
        Use :meth:`marginal_table` for decisions; use this for a quick map
        of where the magnitude lives.
        """
        logs = [(z.name, math.log(z.value)) for z in self.zones]
        total = sum(v for _, v in logs)
        if total == 0:
            return [(n, 0.0) for n, _ in logs]
        return [(n, v / total) for n, v in logs]

    # ---------------------------------------------------------------- edit
    def boost(self, name: str, points: float) -> "DamageModel":
        """Return a copy with ``points`` spent on one zone."""
        z = self.zone(name)
        if not z.investable:
            raise ValueError(f"zone {name!r} is not investable")
        return DamageModel(
            label=self.label,
            zones=[
                Zone(z2.name, z2.value + points * z2.per_point_gain,
                     z2.per_point_gain, z2.note) if z2.name == name
                else Zone(z2.name, z2.value, z2.per_point_gain, z2.note)
                for z2 in self.zones
            ],
        )

    # ---------------------------------------------------------------- io
    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "zones": [
                {"name": z.name, "value": z.value,
                 "per_point_gain": z.per_point_gain, "note": z.note}
                for z in self.zones
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DamageModel":
        return cls(
            label=data.get("label", ""),
            zones=[Zone(**z) for z in data["zones"]],
        )


def zones_from_pairs(pairs: Iterable[Sequence]) -> list[Zone]:
    """``[("atk", 1200, 12), ...]`` -> list of :class:`Zone`."""
    return [Zone(*p) for p in pairs]
