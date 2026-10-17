"""Numerical analysis primitives for game balance design.

This package collects the small set of computations a numerical designer
runs every day: growth curves, multi-zone damage formulas, marginal
benefit / dilution analysis, resource allocation, build tables, and gacha
expectations.

Everything is dependency-light on purpose: the core modules only use the
standard library so that anyone can clone the repo and run it. ``openpyxl``
is optional and only needed for XLSX export.
"""
from .curves import linear, exponential, piecewise, logarithmic, marginal, fit_power_law
from .damage import Zone, DamageModel
from .allocate import optimal_allocation, greedy_allocation, allocation_report
from .gacha import GachaConfig, simulate_pulls, expected_pulls, pull_distribution
from .wuwa import (defense_constant, defense_zone, resistance_zone, crit_zone, baseline_model)
from .builds import (
    Build, apply_build, build_table, crit_multiplier, enumerate_builds,
    format_insights, insights, to_csv, to_markdown, to_xlsx,
)
from .ttk import (
    Action, Rotation, action_damage, rotation_damage, rotation_dps,
    time_to_kill, ttk_report, damage_share, optimal_rotation_order,
)
from .sensitivity import (
    Sensitivity, sweep, sweep_points, sweep_ranges, rank as sensitivity_rank,
    top_lever, investable_only, equalise, format_tornado, format_points,
)

__all__ = [
    "linear", "exponential", "piecewise", "logarithmic", "marginal", "fit_power_law",
    "Zone", "DamageModel",
    "optimal_allocation", "greedy_allocation", "allocation_report",
    "GachaConfig", "simulate_pulls", "expected_pulls", "pull_distribution",
    "Build", "apply_build", "build_table", "crit_multiplier", "enumerate_builds",
    "format_insights", "insights", "to_csv", "to_markdown", "to_xlsx",
    "defense_constant", "defense_zone", "resistance_zone", "crit_zone", "baseline_model",
    "Action", "Rotation", "action_damage", "rotation_damage", "rotation_dps",
    "time_to_kill", "ttk_report", "damage_share", "optimal_rotation_order",
    "Sensitivity", "sweep", "sweep_points", "sweep_ranges",
    "sensitivity_rank", "top_lever", "investable_only", "equalise",
    "format_tornado", "format_points",
]

__version__ = "0.3.0"
