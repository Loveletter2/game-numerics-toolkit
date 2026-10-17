"""Gacha (pity-system) expectations.

Why a designer cares
--------------------
The advertised rate and the experienced cost are two different numbers,
and the gap between them is deliberate. A "1.6% five-star rate" with a
soft pity ramp and an 80-pull hard pity does not average out to
``1 / 0.016 = 62.5`` pulls -- it averages out to something meaningfully
lower, because the tail is truncated by the guarantee.

Designers tune three knobs against each other:

* ``base_rate``           -- the headline number in the marketing copy
* ``soft_pity_start``     -- where luck starts being replaced by arithmetic
* ``hard_pity``           -- the backstop that bounds the worst case

The expected value is only half the story; the *variance* decides how many
players walk away feeling cheated.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class GachaConfig:
    """A soft-pity + hard-pity banner configuration.

    The defaults are illustrative, not any specific game's numbers.
    """

    base_rate: float = 0.006
    soft_pity_start: int = 66
    soft_pity_increment: float = 0.06
    hard_pity: int = 80

    def __post_init__(self) -> None:
        if not 0 < self.base_rate <= 1:
            raise ValueError("base_rate must be in (0, 1]")
        if self.hard_pity < 1:
            raise ValueError("hard_pity must be >= 1")
        if self.soft_pity_start >= self.hard_pity:
            raise ValueError("soft_pity_start must be < hard_pity")
        if self.soft_pity_increment < 0:
            raise ValueError("soft_pity_increment must be >= 0")

    def rate_at(self, pull: int) -> float:
        """Probability of the featured result on the ``pull``-th attempt (1-based)."""
        if pull < 1:
            raise ValueError("pull is 1-based")
        if pull >= self.hard_pity:
            return 1.0
        if pull >= self.soft_pity_start:
            bump = (pull - self.soft_pity_start + 1) * self.soft_pity_increment
            return min(1.0, self.base_rate + bump)
        return self.base_rate


def simulate_pulls(cfg: GachaConfig, n_sim: int = 100_000,
                   seed: Optional[int] = 0) -> list[int]:
    """Monte-Carlo: how many pulls each simulated player needed."""
    if n_sim < 1:
        raise ValueError("n_sim must be >= 1")
    rng = random.Random(seed)
    out: list[int] = []
    for _ in range(n_sim):
        for pull in range(1, cfg.hard_pity + 1):
            if rng.random() < cfg.rate_at(pull):
                out.append(pull)
                break
        else:  # pragma: no cover - rate_at(hard_pity) == 1.0 guarantees a break
            out.append(cfg.hard_pity)
    return out


def expected_pulls(cfg: GachaConfig, n_sim: int = 100_000,
                   seed: Optional[int] = 0) -> float:
    """Monte-Carlo mean of :func:`simulate_pulls`."""
    samples = simulate_pulls(cfg, n_sim=n_sim, seed=seed)
    return sum(samples) / len(samples)


def analytic_expected(cfg: GachaConfig) -> float:
    """Exact expectation via the tail-sum formula ``E[N] = sum P(N > k)``."""
    total = 0.0
    survival = 1.0
    for k in range(0, cfg.hard_pity):
        total += survival
        survival *= (1.0 - cfg.rate_at(k + 1))
    return total


def pull_distribution(cfg: GachaConfig, n_sim: int = 100_000,
                      seed: Optional[int] = 0) -> dict[int, int]:
    """Histogram of pulls needed, keyed by pull count."""
    hist: dict[int, int] = {}
    for pulls in simulate_pulls(cfg, n_sim=n_sim, seed=seed):
        hist[pulls] = hist.get(pulls, 0) + 1
    return hist


def naive_expectation(cfg: GachaConfig) -> float:
    """What a player naively assumes: ``1 / base_rate``.

    Comparing this to :func:`analytic_expected` is the point of the module.
    """
    return 1.0 / cfg.base_rate


def summary(cfg: GachaConfig, n_sim: int = 100_000, seed: Optional[int] = 0) -> dict:
    samples = simulate_pulls(cfg, n_sim=n_sim, seed=seed)
    samples_sorted = sorted(samples)
    n = len(samples_sorted)
    mean = sum(samples_sorted) / n
    var = sum((x - mean) ** 2 for x in samples_sorted) / n
    return {
        "naive_expectation": naive_expectation(cfg),
        "analytic_expectation": analytic_expected(cfg),
        "simulated_expectation": mean,
        "std_dev": var ** 0.5,
        "p50": samples_sorted[n // 2],
        "p90": samples_sorted[int(n * 0.9)],
        "p99": samples_sorted[min(n - 1, int(n * 0.99))],
        "rate_up_share": 1.0,
    }
