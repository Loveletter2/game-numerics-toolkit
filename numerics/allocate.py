"""Resource allocation across multiplicative zones.

The optimization problem
------------------------
Let every investable zone ``i`` start at value ``Z_i`` and let one point
buy ``e_i`` of zone value, so after spending ``p_i`` points the zone reads
``Z_i + e_i * p_i``. Damage is the product, so we maximise the sum of logs:

    maximise    sum_i ln(Z_i + e_i * p_i)
    subject to  sum_i p_i = B,  p_i >= 0

The Lagrangian condition gives

    e_i / (Z_i + e_i * p_i) = lam      =>      Z_i + e_i * p_i = e_i / lam

i.e. **at the optimum the final zone values are proportional to their
efficiency**. When every zone is equally efficient (``e_i`` equal) the
optimum is to bring all zones to the same value -- the precise meaning of
"stack evenly".

Solving it
----------
With ``t = 1 / lam`` the condition is ``p_i = t - Z_i / e_i``, kept only
where positive. ``t`` is found by bisection on the budget constraint; the
result is exact for the continuous relaxation. :func:`greedy_allocation`
solves the same problem in discrete steps by always spending the next
point where the marginal gain is highest, which is optimal here because
each zone's marginal gain is decreasing.
"""
from __future__ import annotations

from typing import Sequence

from .damage import DamageModel, Zone


def _marginal(model: DamageModel, name: str, unit: float) -> float:
    z = model.zone(name)
    return (unit * z.per_point_gain) / z.value


def optimal_allocation(model: DamageModel, budget: float,
                       tolerance: float = 1e-12,
                       max_iter: int = 200) -> dict[str, float]:
    """Closed-form (continuous) optimal split of ``budget`` points.

    Returns a mapping ``zone name -> points``. Zones whose current value is
    already large relative to their efficiency receive nothing.
    """
    if budget < 0:
        raise ValueError("budget must be >= 0")
    investable: list[Zone] = [z for z in model.zones if z.investable]
    if not investable:
        raise ValueError("no investable zones")
    if budget == 0:
        return {z.name: 0.0 for z in model.zones}

    # p_i(t) = t - Z_i / e_i, only where positive; find t with sum = budget.
    def spent(t: float) -> float:
        return sum(max(0.0, t - z.value / z.per_point_gain) for z in investable)

    lo, hi = 0.0, 1.0
    while spent(hi) < budget:
        hi *= 2.0
        if hi > 1e12:
            raise RuntimeError("budget too large to solve")
    for _ in range(max_iter):
        mid = (lo + hi) / 2.0
        if spent(mid) < budget:
            lo = mid
        else:
            hi = mid
        if hi - lo < tolerance:
            break
    t = (lo + hi) / 2.0

    out = {z.name: 0.0 for z in model.zones}
    for z in investable:
        out[z.name] = max(0.0, t - z.value / z.per_point_gain)
    return out


def greedy_allocation(model: DamageModel, budget: float,
                      step: float = 0.01) -> dict[str, float]:
    """Discrete greedy allocation -- spend each next step where it pays most."""
    if budget < 0:
        raise ValueError("budget must be >= 0")
    if not any(z.investable for z in model.zones):
        raise ValueError("no investable zones")

    alloc = {z.name: 0.0 for z in model.zones}
    current = model
    remaining = budget
    while remaining > 1e-12:
        take = min(step, remaining)
        table = current.marginal_table(take)
        best, _ = table[0]
        alloc[best] += take
        current = current.boost(best, take)
        remaining -= take
    return alloc


def allocation_report(model: DamageModel, budget: float,
                      step: float = 0.01) -> dict:
    """Compare optimal, greedy and naive allocations on the same budget."""
    base = model.total()
    opt = optimal_allocation(model, budget)
    greedy = greedy_allocation(model, budget, step=step)

    def apply(alloc: dict[str, float]) -> float:
        m = model
        for name, pts in alloc.items():
            if pts > 0:
                m = m.boost(name, pts)
        return m.total()

    investable = [z.name for z in model.zones if z.investable]
    first = model.cheapest_zone()
    all_in = {n: (budget if n == first else 0.0) for n in investable}

    tot_opt = apply(opt)
    tot_greedy = apply(greedy)
    tot_all_in = apply(all_in)

    return {
        "base_damage": base,
        "budget": budget,
        "optimal": {"allocation": opt, "damage": tot_opt,
                    "gain": tot_opt / base - 1.0},
        "greedy": {"allocation": greedy, "damage": tot_greedy,
                   "gain": tot_greedy / base - 1.0},
        "all_in_one_zone": {"zone": first, "damage": tot_all_in,
                            "gain": tot_all_in / base - 1.0},
        "gap_optimal_vs_all_in": tot_opt / tot_all_in - 1.0,
    }
