"""Chart builders specific to this project's analyses.

Each helper turns a model object into the one SVG that answers the
question the model was built to answer. Keeping them here (rather than
inline in the CLI) means the charts are importable from a notebook too.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional, Sequence

from .charts import bar_chart, line_chart
from .curves import marginal
from .damage import DamageModel
from .gacha import GachaConfig, pull_distribution


def plot_dilution(model: DamageModel, zones: Sequence[str],
                  out: str | Path, max_points: float = 100.0) -> Path:
    """Marginal return of the next point, as each zone grows.

    Every series starts at 100% and decays: the same investment is worth
    less the more you have already put into a zone.
    """
    series: dict[str, tuple[list[float], list[float]]] = {}
    for name in zones:
        xs, ys = model.marginal_curve(name, max_points=max_points)
        base = ys[0]
        series[name] = (xs, [y / base * 100.0 for y in ys])
    return line_chart(series, out,
                      title="Dilution: the next point is worth less as a zone grows",
                      xlabel="resource points already invested in this zone",
                      ylabel="relative gain of next point (% of first)")


def plot_curves(curves: dict[str, Sequence[float]], out: str | Path,
                title: str = "Growth curves: stat and increment per level") -> Path:
    """Two panels cannot be done in one SVG, so the increment chart wins:
    the shape of the increment list *is* the curve's feel."""
    series: dict[str, tuple[list[float], list[float]]] = {}
    for name, values in curves.items():
        inc = marginal(values)
        series[name] = (list(range(2, len(inc) + 2)), inc)
    return line_chart(series, out, title=title,
                      xlabel="level", ylabel="stat gained per level")


def plot_gacha(cfg: GachaConfig, out: str | Path,
               n_sim: int = 50_000, seed: Optional[int] = 0) -> Path:
    """Distribution of pulls needed, with the naive expectation marked."""
    hist = pull_distribution(cfg, n_sim=n_sim, seed=seed)
    total = sum(hist.values())
    xs = sorted(hist)
    ys = [hist[x] / total * 100.0 for x in xs]
    return bar_chart(xs, ys, out,
                     title="Pity system: where the outcomes actually sit",
                     xlabel="pulls until the featured result",
                     ylabel="share of players (%)",
                     marker=(1.0 / cfg.base_rate,
                             f"naive 1/rate = {1.0 / cfg.base_rate:.0f}"))
