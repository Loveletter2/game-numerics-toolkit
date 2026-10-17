"""Unit tests: ``python -m unittest discover -s tests -t .``"""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from numerics import (  # noqa: E402
    DamageModel, GachaConfig, Zone, allocation_report, exponential,
    greedy_allocation, linear, logarithmic, optimal_allocation, piecewise,
    simulate_pulls,
)
from numerics.curves import curve_summary, fit_power_law, marginal  # noqa: E402
from numerics.gacha import analytic_expected, naive_expectation  # noqa: E402


class TestCurves(unittest.TestCase):
    def test_linear(self):
        self.assertEqual(linear(100, 10, 4), [100, 110, 120, 130])

    def test_exponential(self):
        series = exponential(100, 2.0, 4)
        self.assertEqual(series, [100, 200, 400, 800])

    def test_piecewise_is_continuous(self):
        series = piecewise(100, [(39, 18), (40, 5)], 80)
        self.assertEqual(len(series), 80)
        self.assertEqual(series[0], 100)
        self.assertEqual(series[39], 100 + 39 * 18)      # level 40
        self.assertEqual(series[79], 100 + 39 * 18 + 40 * 5)  # level 80
        # no jump between segments
        self.assertEqual(series[40] - series[39], 5)

    def test_logarithmic_is_concave(self):
        series = logarithmic(100, 50, 20)
        inc = marginal(series)
        self.assertTrue(all(a > b for a, b in zip(inc, inc[1:])))

    def test_marginal(self):
        self.assertEqual(marginal([1, 3, 6]), [2, 3])

    def test_fit_power_law_recovers_exponent(self):
        xs = [1, 2, 4, 8, 16]
        ys = [3 * x ** 1.5 for x in xs]
        a, b = fit_power_law(xs, ys)
        self.assertAlmostEqual(b, 1.5, places=6)
        self.assertAlmostEqual(a, 3.0, places=6)

    def test_fit_rejects_bad_input(self):
        with self.assertRaises(ValueError):
            fit_power_law([1], [1])

    def test_curve_summary_detects_decay(self):
        s = curve_summary(piecewise(100, [(39, 18), (40, 5)], 80))
        self.assertLess(s["increment_ratio"], 1.0)
        self.assertAlmostEqual(s["multiple"], 1002 / 100)


class TestDamageModel(unittest.TestCase):
    def setUp(self):
        self.model = DamageModel("test", [
            Zone("ATK", 1000.0, per_point_gain=10.0),   # 1 point = +1%
            Zone("Crit", 1.6, per_point_gain=0.02),     # 1 point = +1.25%
            Zone("Defense", 0.5),                       # not investable
        ])

    def test_total_is_a_product(self):
        self.assertAlmostEqual(self.model.total(), 1000.0 * 1.6 * 0.5)

    def test_marginal_gain_is_delta_over_value(self):
        # the dilution formula: (points * gain) / value
        self.assertAlmostEqual(self.model.marginal_gain("ATK", 5), 5 * 10.0 / 1000.0)
        self.assertAlmostEqual(self.model.marginal_gain("Crit", 5), 5 * 0.02 / 1.6)

    def test_marginal_gain_zero_for_fixed_zone(self):
        self.assertEqual(self.model.marginal_gain("Defense", 5), 0.0)

    def test_cheapest_zone_is_the_most_diluted(self):
        # ATK: 1%/point, Crit: 0.5%/point -> Crit is the better target
        self.assertEqual(self.model.cheapest_zone(), "Crit")

    def test_boost_preserves_other_zones(self):
        boosted = self.model.boost("ATK", 10)
        self.assertAlmostEqual(boosted.zone("ATK").value, 1100.0)
        self.assertAlmostEqual(boosted.zone("Crit").value, 1.6)
        self.assertAlmostEqual(boosted.total(), 1100.0 * 1.6 * 0.5)

    def test_boost_rejects_fixed_zone(self):
        with self.assertRaises(ValueError):
            self.model.boost("Defense", 1)

    def test_dilution_curve_is_linear_in_absolute_damage(self):
        # one point always buys the same absolute damage -- dilution is a
        # property of the *relative* return, not the absolute one
        xs, ys = self.model.dilution_curve("ATK", max_points=100, steps=5)
        self.assertEqual(len(xs), 5)
        gains = [b - a for a, b in zip(ys, ys[1:])]
        self.assertAlmostEqual(max(gains) - min(gains), 0.0, places=9)

    def test_marginal_curve_decays(self):
        xs, ys = self.model.marginal_curve("ATK", max_points=100, steps=20)
        self.assertTrue(all(a > b for a, b in zip(ys, ys[1:])))
        self.assertAlmostEqual(ys[0], 10.0 / 1000.0)

    def test_spread_gain_matches_formula(self):
        info = self.model.spread_gain(1.0)
        n = 2  # two investable zones
        self.assertAlmostEqual(info["optimal_multiple"], (1 + 1.0 / n) ** n)
        self.assertAlmostEqual(info["all_in_multiple"], 2.0)

    def test_invalid_zone_rejected(self):
        with self.assertRaises(ValueError):
            Zone("bad", 0.0)
        with self.assertRaises(ValueError):
            Zone("bad", 1.0, per_point_gain=-1.0)

    def test_roundtrip_dict(self):
        again = DamageModel.from_dict(self.model.to_dict())
        self.assertAlmostEqual(again.total(), self.model.total())


class TestAllocation(unittest.TestCase):
    def test_optimal_ignores_inefficient_zone(self):
        model = DamageModel("t", [
            Zone("cheap", 1.0, per_point_gain=0.01),   # value/gain = 100
            Zone("expensive", 5.0, per_point_gain=0.01),  # value/gain = 500
        ])
        alloc = optimal_allocation(model, 1.0)
        self.assertAlmostEqual(alloc["cheap"], 1.0)
        self.assertAlmostEqual(alloc["expensive"], 0.0)

    def test_optimal_splits_budget(self):
        model = DamageModel("t", [
            Zone("a", 1.0, per_point_gain=0.01),
            Zone("b", 1.0, per_point_gain=0.01),
        ])
        alloc = optimal_allocation(model, 2.0)
        self.assertAlmostEqual(alloc["a"], 1.0)
        self.assertAlmostEqual(alloc["b"], 1.0)

    def test_greedy_matches_closed_form(self):
        model = DamageModel("t", [
            Zone("a", 1.0, per_point_gain=0.01),
            Zone("b", 1.5, per_point_gain=0.02),
            Zone("c", 2.0, per_point_gain=0.03),
        ])
        opt = optimal_allocation(model, 5.0)
        greedy = greedy_allocation(model, 5.0, step=0.01)

        def total(alloc):
            m = model
            for name, pts in alloc.items():
                if pts > 0:
                    m = m.boost(name, pts)
            return m.total()

        self.assertAlmostEqual(total(opt) / total(greedy), 1.0, delta=0.005)

    def test_report_flags_spreading_is_better(self):
        model = DamageModel("t", [
            Zone("a", 1.0, per_point_gain=0.01),
            Zone("b", 1.0, per_point_gain=0.01),
        ])
        rep = allocation_report(model, 4.0)
        self.assertGreater(rep["gap_optimal_vs_all_in"], 0.0)

    def test_negative_budget_rejected(self):
        model = DamageModel("t", [Zone("a", 1.0, per_point_gain=0.01)])
        with self.assertRaises(ValueError):
            optimal_allocation(model, -1.0)


class TestGacha(unittest.TestCase):
    def test_analytic_expectation_between_bounds(self):
        cfg = GachaConfig()
        e = analytic_expected(cfg)
        # never better than the naive rate, never worse than hard pity
        self.assertLess(e, naive_expectation(cfg))
        self.assertLessEqual(e, cfg.hard_pity)

    def test_monte_carlo_matches_analytic(self):
        cfg = GachaConfig()
        samples = simulate_pulls(cfg, n_sim=20_000, seed=7)
        mc = sum(samples) / len(samples)
        self.assertAlmostEqual(mc / analytic_expected(cfg), 1.0, delta=0.03)

    def test_hard_pity_bounds_every_sample(self):
        cfg = GachaConfig(soft_pity_start=5, hard_pity=12)
        self.assertTrue(all(p <= 12 for p in simulate_pulls(cfg, n_sim=500, seed=1)))

    def test_rate_grows_after_soft_pity(self):
        cfg = GachaConfig()
        self.assertLess(cfg.rate_at(10), cfg.rate_at(cfg.soft_pity_start + 3))
        self.assertEqual(cfg.rate_at(cfg.hard_pity), 1.0)

    def test_invalid_config_rejected(self):
        with self.assertRaises(ValueError):
            GachaConfig(base_rate=0)
        with self.assertRaises(ValueError):
            GachaConfig(soft_pity_start=90, hard_pity=80)


class TestCharts(unittest.TestCase):
    def test_line_chart_writes_valid_svg(self):
        import pathlib
        import tempfile
        import xml.dom.minidom

        from numerics.charts import line_chart

        with tempfile.TemporaryDirectory() as tmp:
            path = line_chart({"a": ([0, 1, 2], [1, 2, 4])},
                              pathlib.Path(tmp) / "c.svg", title="t")
            doc = xml.dom.minidom.parse(str(path))
            self.assertEqual(len(doc.getElementsByTagName("polyline")), 1)
            self.assertEqual(doc.documentElement.tagName, "svg")

    def test_bar_chart_draws_marker(self):
        import pathlib
        import tempfile
        import xml.dom.minidom

        from numerics.charts import bar_chart

        with tempfile.TemporaryDirectory() as tmp:
            path = bar_chart([1, 2, 3], [5, 10, 2],
                             pathlib.Path(tmp) / "b.svg",
                             title="t", marker=(2.0, "naive"))
            doc = xml.dom.minidom.parse(str(path))
            self.assertEqual(len(doc.getElementsByTagName("rect")), 4)  # bg + 3 bars

    def test_charts_reject_empty_input(self):
        from numerics.charts import bar_chart, line_chart

        with self.assertRaises(ValueError):
            line_chart({}, "unused.svg")
        with self.assertRaises(ValueError):
            bar_chart([], [], "unused.svg")


class TestBuilds(unittest.TestCase):
    def setUp(self):
        from numerics import Build, DamageModel, Zone
        self.Build = Build
        self.model = DamageModel("base", [
            Zone("ATK", 1000.0, per_point_gain=10.0),
            Zone("Crit", 1.5, per_point_gain=0.01),
            Zone("Defense", 0.5),
        ])

    def test_crit_multiplier(self):
        from numerics import crit_multiplier
        self.assertAlmostEqual(crit_multiplier(0.55, 1.10), 1.605)
        self.assertAlmostEqual(crit_multiplier(1.0, 2.0), 3.0)
        self.assertEqual(crit_multiplier(0.0, 5.0), 1.0)

    def test_crit_multiplier_rejects_bad_input(self):
        from numerics import crit_multiplier
        with self.assertRaises(ValueError):
            crit_multiplier(1.5, 1.0)
        with self.assertRaises(ValueError):
            crit_multiplier(0.5, -1.0)

    def test_apply_build_overrides_value_only(self):
        from numerics import apply_build
        b = self.Build("b", {"ATK": 1200.0})
        m = apply_build(self.model, b)
        self.assertAlmostEqual(m.zone("ATK").value, 1200.0)
        self.assertAlmostEqual(m.zone("ATK").per_point_gain, 10.0)  # kept
        self.assertAlmostEqual(m.zone("Crit").value, 1.5)
        self.assertAlmostEqual(m.total(), 1200.0 * 1.5 * 0.5)
        # the original model is untouched
        self.assertAlmostEqual(self.model.zone("ATK").value, 1000.0)

    def test_apply_build_rejects_unknown_zone(self):
        from numerics import apply_build
        with self.assertRaises(KeyError):
            apply_build(self.model, self.Build("b", {"Haste": 1.0}))

    def test_build_rejects_non_positive_value(self):
        with self.assertRaises(ValueError):
            self.Build("b", {"ATK": 0.0})

    def test_enumerate_count_and_order(self):
        from numerics import enumerate_builds
        builds = enumerate_builds({"ATK": [1000.0, 1200.0], "Crit": [1.5, 1.8, 2.1]})
        self.assertEqual(len(builds), 6)
        self.assertEqual(builds[0].name, "ATK=1000, Crit=1.5")
        self.assertEqual(builds[-1].name, "ATK=1200, Crit=2.1")

    def test_enumerate_respects_cap(self):
        from numerics import enumerate_builds
        with self.assertRaises(ValueError):
            enumerate_builds({"ATK": list(range(100)), "Crit": list(range(100))},
                             max_builds=1000)

    def test_enumerate_rejects_empty_grid(self):
        from numerics import enumerate_builds
        with self.assertRaises(ValueError):
            enumerate_builds({})

    def test_table_is_ranked_and_normalised(self):
        from numerics import build_table, enumerate_builds
        rows = build_table(self.model, enumerate_builds(
            {"ATK": [900.0, 1000.0, 1100.0], "Crit": [1.5, 1.8]}))
        damages = [r["damage"] for r in rows]
        self.assertEqual(damages, sorted(damages, reverse=True))
        self.assertEqual(rows[0]["rank"], 1)
        self.assertAlmostEqual(rows[0]["pct_of_best"], 1.0)
        self.assertAlmostEqual(rows[0]["gap_to_best"], 0.0)
        self.assertTrue(all(r["pct_of_best"] <= 1.0 for r in rows))
        self.assertTrue(all(r["best_next_zone"] for r in rows))

    def test_csv_export_roundtrip(self):
        import csv
        import pathlib
        import tempfile

        from numerics import build_table, enumerate_builds, to_csv
        rows = build_table(self.model, enumerate_builds({"ATK": [1000.0, 1200.0]}))
        with tempfile.TemporaryDirectory() as tmp:
            path = to_csv(rows, pathlib.Path(tmp) / "b.csv")
            raw = path.read_bytes()
            self.assertTrue(raw.startswith(b"\xef\xbb\xbf"))  # BOM for Excel
            with path.open(encoding="utf-8-sig", newline="") as fh:
                table = list(csv.reader(fh))
        self.assertEqual(len(table), 3)  # header + 2 builds
        self.assertEqual(table[0][0], "rank")
        self.assertEqual(table[1][0], "1")

    def test_markdown_export_contains_header(self):
        import pathlib
        import tempfile

        from numerics import build_table, enumerate_builds, to_markdown
        rows = build_table(self.model, enumerate_builds({"ATK": [1000.0, 1200.0]}))
        with tempfile.TemporaryDirectory() as tmp:
            path = to_markdown(rows, pathlib.Path(tmp) / "b.md", top=1)
            text = path.read_text(encoding="utf-8")
        self.assertIn("| Rank |", text)
        self.assertIn("builds total", text)  # truncation note

    def test_insights_are_consistent(self):
        from numerics import build_table, enumerate_builds, format_insights, insights
        rows = build_table(self.model, enumerate_builds(
            {"ATK": [900.0, 1100.0], "Crit": [1.5, 2.0]}))
        info = insights(rows, self.model)
        self.assertEqual(info["n_builds"], 4)
        self.assertGreater(info["spread"], 0.0)
        self.assertGreater(info["gap_over_runner_up"], 0.0)
        self.assertAlmostEqual(info["baseline_damage"], self.model.total())
        lines = format_insights(info)
        self.assertEqual(len(lines), 4)
        self.assertTrue(all(isinstance(x, str) and x for x in lines))


class TestWuwaZones(unittest.TestCase):
    """The decoded WuWa pipeline: K scales with level, resistance is 3-segment."""

    def test_defense_constant_scales_with_level(self):
        from numerics.wuwa import defense_constant
        self.assertEqual(defense_constant(90), 1520.0)   # 800 + 8*90
        self.assertEqual(defense_constant(80), 1440.0)
        self.assertEqual(defense_constant(1), 808.0)
        with self.assertRaises(ValueError):
            defense_constant(0)

    def test_defense_zone_value(self):
        from numerics.wuwa import defense_zone
        # 600 DEF against a level-90 character: 1 / (1 + 600/1520)
        self.assertAlmostEqual(defense_zone(600, 90), 1.0 / (1.0 + 600 / 1520))
        self.assertAlmostEqual(defense_zone(600, 90), 0.716981, places=6)

    def test_defense_shred_increases_the_zone(self):
        from numerics.wuwa import defense_zone
        base = defense_zone(600, 90)
        self.assertGreater(defense_zone(600, 90, ignore=0.4), base)
        self.assertGreater(defense_zone(600, 90, reduction=0.4), base)
        both = defense_zone(600, 90, ignore=0.4, reduction=0.4)
        self.assertGreater(both, defense_zone(600, 90, ignore=0.4))

    def test_defense_zone_is_capped(self):
        from numerics.wuwa import defense_zone
        # over-shredding drives effective defence below -K -> hard cap
        self.assertEqual(defense_zone(1520, 90, ignore=2.0), 2.0)
        self.assertEqual(defense_zone(600, 90, ignore=3.0), 2.0)

    def test_defense_rejects_bad_input(self):
        from numerics.wuwa import defense_zone
        with self.assertRaises(ValueError):
            defense_zone(-1, 90)
        with self.assertRaises(ValueError):
            defense_zone(600, 90, ignore=-0.5)

    def test_resistance_segments_are_continuous(self):
        from numerics.wuwa import resistance_zone
        self.assertAlmostEqual(resistance_zone(0.0), 1.0)
        self.assertAlmostEqual(resistance_zone(-0.0001), 1.0, places=3)
        self.assertAlmostEqual(resistance_zone(0.8), 0.2)
        self.assertAlmostEqual(resistance_zone(0.7999), 0.2001, places=3)

    def test_resistance_negative_pays_half(self):
        from numerics.wuwa import resistance_zone
        self.assertAlmostEqual(resistance_zone(-0.4), 1.2)   # not 1.4
        self.assertAlmostEqual(resistance_zone(-1.0), 1.5)

    def test_resistance_high_never_reaches_zero(self):
        from numerics.wuwa import resistance_zone
        self.assertAlmostEqual(resistance_zone(1.0), 1.0 / 6.0)
        self.assertGreater(resistance_zone(1.0), 0.0)

    def test_crit_zone_uses_total_multiplier(self):
        from numerics.wuwa import crit_zone
        # 55% rate, crit hits for 210% -> 1 + 0.55 * 1.10
        self.assertAlmostEqual(crit_zone(0.55, 2.1), 1.605)
        self.assertAlmostEqual(crit_zone(1.0, 2.1), 2.1)
        self.assertAlmostEqual(crit_zone(0.0, 2.1), 1.0)
        self.assertAlmostEqual(crit_zone(0.55, 2.1, expected=False), 2.1)

    def test_crit_zone_rejects_a_bonus_as_multiplier(self):
        from numerics.wuwa import crit_zone
        # a total multiplier can never be below 1.0; 0.5 is a bonus
        with self.assertRaises(ValueError):
            crit_zone(0.55, 0.5)

    def test_additive_zone_dilutes_multiplicative_does_not(self):
        from numerics.wuwa import additive_zone, multiplicative_zone
        self.assertAlmostEqual(additive_zone(0.2, 0.3), 1.5)
        self.assertAlmostEqual(multiplicative_zone(0.2, 0.3), 1.2 * 1.3)
        # the same total bonus is worth more when multiplied
        self.assertGreater(multiplicative_zone(0.2, 0.3),
                           additive_zone(0.2, 0.3))

    def test_ceiling_rounds_up_per_instance(self):
        from numerics.wuwa import apply_ceiling
        self.assertEqual(apply_ceiling(10.1), 11)
        self.assertEqual(apply_ceiling(10.0), 10)
        self.assertEqual(apply_ceiling(0.2), 1)


class TestAttackZone(unittest.TestCase):
    """white * (1 + pct) + flat -- the two-rate zone."""

    def test_attack_value(self):
        from numerics.wuwa import attack_value
        # white 1000 (char 600 + weapon 400), 60% attack, 200 flat
        self.assertAlmostEqual(attack_value(1000, 0.6, 200), 1800)
        self.assertAlmostEqual(attack_value(1000, 0.0, 0), 1000)

    def test_flat_does_not_benefit_from_pct(self):
        from numerics.wuwa import attack_value
        base = attack_value(1000, 0.5, 0)
        with_flat = attack_value(1000, 0.5, 100)
        # 100 flat adds exactly 100, not 150
        self.assertAlmostEqual(with_flat - base, 100)

    def test_pct_to_flat_exchange_rate(self):
        from numerics.wuwa import pct_to_flat
        self.assertAlmostEqual(pct_to_flat(1000), 10.0)    # 1% == 10 flat
        self.assertAlmostEqual(pct_to_flat(1200), 12.0)
        self.assertAlmostEqual(pct_to_flat(1000, 5), 50.0)

    def test_pct_and_flat_are_interchangeable_once_converted(self):
        from numerics.wuwa import attack_value, pct_to_flat
        # +1% attack and +white/100 flat must give the same total
        by_pct = attack_value(1000, 0.61, 200)
        by_flat = attack_value(1000, 0.60, 200 + pct_to_flat(1000))
        self.assertAlmostEqual(by_pct, by_flat)

    def test_attack_marginal_gain_is_added_over_total(self):
        from numerics.wuwa import attack_marginal_gain
        # total 1800, +18 attack -> +1%
        self.assertAlmostEqual(attack_marginal_gain(1000, 0.6, 200, 18), 0.01)

    def test_attack_rejects_bad_input(self):
        from numerics.wuwa import attack_value
        with self.assertRaises(ValueError):
            attack_value(0, 0.5, 0)
        with self.assertRaises(ValueError):
            attack_value(1000, -0.1, 0)

    def test_baseline_model_assembles_nine_zones(self):
        from numerics.wuwa import baseline_model, attack_value
        model = baseline_model(
            atk_white=1000, atk_pct=0.2, atk_flat=0,
            multiplier=1.8, crit_rate=0.55, crit_multiplier=2.1,
            dmg_bonus=[0.46], enemy_defense=600, char_level=90,
            enemy_resistance=0.1,
        )
        self.assertEqual(len(model.zones), 10)
        self.assertAlmostEqual(model.total(),
                               attack_value(1000, 0.2, 0) * 1.8 * 1.605 * 1.46
                               * (1 / (1 + 600 / 1520)) * 0.9)
        # one point of investment in ATK == 1% == white/100 flat attack
        self.assertAlmostEqual(model.zone("ATK").per_point_gain, 10.0)


class TestCritSources(unittest.TestCase):
    """Base is 5% rate and a 150% *total* multiplier."""

    def test_crit_multiplier_from_bonus_adds_to_150(self):
        from numerics.wuwa import crit_multiplier_from_bonus
        self.assertAlmostEqual(crit_multiplier_from_bonus(0.0), 1.5)
        self.assertAlmostEqual(crit_multiplier_from_bonus(0.6), 2.1)

    def test_crit_rate_total_starts_at_5_percent(self):
        from numerics.wuwa import crit_rate_total
        self.assertAlmostEqual(crit_rate_total(), 0.05)
        self.assertAlmostEqual(crit_rate_total(0.08, 0.30), 0.43)
        self.assertAlmostEqual(crit_rate_total(0.125), 0.175)   # ally buff

    def test_crit_rate_is_capped_at_100_percent(self):
        from numerics.wuwa import crit_rate_total
        self.assertAlmostEqual(crit_rate_total(2.0), 1.0)

    def test_zero_investment_crit_zone(self):
        from numerics.wuwa import crit_multiplier_from_bonus, crit_zone
        # 5% rate, no crit damage -> tiny but non-zero contribution
        self.assertAlmostEqual(crit_zone(0.05, crit_multiplier_from_bonus(0)),
                               1.0 + 0.05 * 0.5)

    def test_full_crit_reproduces_the_multiplier(self):
        from numerics.wuwa import crit_multiplier_from_bonus, crit_zone
        m = crit_multiplier_from_bonus(1.1)     # 260% total
        self.assertAlmostEqual(crit_zone(1.0, m), m)

    def test_crit_sources_reject_negative(self):
        from numerics.wuwa import crit_multiplier_from_bonus, crit_rate_total
        with self.assertRaises(ValueError):
            crit_multiplier_from_bonus(-0.1)
        with self.assertRaises(ValueError):
            crit_rate_total(-0.01)


class TestDefenseEquivalence(unittest.TestCase):
    """Two parameterisations of the same defence zone must agree exactly."""

    def test_k_and_level_forms_are_identical(self):
        from numerics.wuwa import defense_zone, defense_zone_by_level
        for char_lv in (1, 40, 80, 90):
            for enemy_lv in (1, 50, 90, 99):
                def_value = 8.0 * (enemy_lv + 99)    # the table's DEF column
                a = defense_zone(def_value, char_lv)
                b = defense_zone_by_level(char_lv, enemy_lv)
                self.assertAlmostEqual(a, b, places=12,
                                       msg=f"lv{char_lv} vs {enemy_lv}")

    def test_known_value(self):
        from numerics.wuwa import defense_zone_by_level
        # lv90 character against a lv99 enemy: 190 / (190 + 198)
        self.assertAlmostEqual(defense_zone_by_level(90, 99), 190 / 388)
        self.assertAlmostEqual(defense_zone_by_level(90, 99), 0.489691, places=6)
        # a level-90 enemy has DEF 1512, i.e. 8 * 189
        self.assertAlmostEqual(defense_zone_by_level(90, 90), 190 / 379)

    def test_ignore_defence_raises_the_zone(self):
        from numerics.wuwa import defense_zone_by_level
        self.assertGreater(defense_zone_by_level(90, 99, ignore=0.4),
                           defense_zone_by_level(90, 99))

    def test_equal_levels_are_slightly_above_half(self):
        # the attacker gets +100 and the target +99, so at equal levels the
        # attacker keeps a hair more than half -- 180/359, not 180/360
        from numerics.wuwa import defense_zone_by_level
        self.assertAlmostEqual(defense_zone_by_level(80, 80), 180 / 359)
        self.assertGreater(defense_zone_by_level(80, 80), 0.5)


if __name__ == "__main__":
    unittest.main(verbosity=2)

