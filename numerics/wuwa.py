"""WuWa-specific zone formulas.

These are not abstractions -- they are the concrete expressions used by the
game's damage pipeline, decoded from the community data workbook (the
``伤害计算`` sheet's array formulas) and cross-checked against the
``伤害配置`` block definitions.

Keeping them in their own module rather than hard-coding them into
:mod:`numerics.damage` matters: the generic model stays reusable, and the
game-specific constants (K = 800 + 8 * level, the three-segment resistance
curve, the 2x defence cap) live in one place that can be re-derived when a
patch changes them.

Decoded structure (one damage instance, crit and non-crit computed
separately and averaged):

    damage = atk_or_hp * multiplier
             * crit
             * defense_zone
             * (1 + dmg_bonus) * (1 + dmg_bonus_2)
             * resistance_zone * (1 + res_term_a) * (1 + res_term_b)
             * (1 - min(mitigation, 1)) * (1 - min(mitigation_2, 1))
             * prod(1 + amplify_i)          for i in 1..10   (multiplicative!)
             * prod(1 + final_i)            for i in 1..8    (multiplicative!)
             * max(1 + misc_a, 0) * max(1 + misc_b, 0)
             then CEILING to integer
"""
from __future__ import annotations

import math
from typing import Sequence

from .damage import DamageModel, Zone

#: Final-damage sources are so scarce that the zone behaves like a switch
#: rather than a stat. It can only be raised by 集谐响应, 同奏响应 and
#: environment buffs -- there is no substat, no weapon roll and no ally buff
#: that grants it. In a build table it is therefore a constant, not a
#: variable, and the toolkit must not treat it as investable.
FINAL_DAMAGE_SOURCES = ("集谐响应", "同奏响应", "环境buff增幅")
#: Vulnerability (易伤) is a *target-side* debuff written into some characters'
#: resonance chains, phrased as "the enemy takes X% more damage from <character>".
#: It is gated behind duplicate pulls and bound to that character -- it is not
#: a team-wide buff. Numerically it is a factor inside the resistance bracket,
#: but a product is commutative, so exposing it as its own zone is free and
#: makes its contribution visible in attribution tables.
VULNERABILITY_SOURCES = ("角色共鸣链", "环境")

#: Resistance and defence can only be moved from the *enemy* side: through
#: the environment, a handful of characters' own mechanics, or weapon buffs.
ENEMY_SIDE_SOURCES = ("环境", "部分特殊角色的本体机制", "武器拐力")

#: Every character starts at 5% crit rate and a **150% crit multiplier**.
#: The 150% is a *total*, not a bonus: a crit already deals 1.5x damage
#: before any crit-damage stat is added. Feeding a "bonus" into a total
#: slot understates crit builds by roughly a third.
CRIT_RATE_BASE = 0.05
CRIT_BASE_MULTIPLIER = 1.5

#: The defence constant is not a fixed 800 -- it scales with character level.
K_BASE = 800.0
K_PER_LEVEL = 8.0

#: A defence zone cannot exceed 2x, no matter how much defence shred stacks.
DEFENSE_ZONE_CAP = 2.0

#: Resistance switches behaviour at these two breakpoints.
RES_SOFT_FLOOR = 0.0
RES_SOFT_CAP = 0.8


def attack_value(white: float, pct: float, flat: float) -> float:
    """Final attack: ``white * (1 + pct) + flat``.

    The three parts are not interchangeable, and the asymmetry is the whole
    design:

    * **white** (character base + weapon base) is the multiplier's *base*.
      A better weapon does not just add attack, it raises the value of
      every percent of attack the player will ever stack.
    * **pct** is summed inside one bracket, so it dilutes like any
      additive zone -- and it dilutes against *allies'* attack buffs too,
      because they land in the same bracket.
    * **flat** is added after the bracket, so it never benefits from
      ``pct``. It is the "small tail" of this zone.
    """
    if white <= 0:
        raise ValueError("white attack must be positive")
    if pct < 0 or flat < 0:
        raise ValueError("pct and flat must be >= 0")
    return white * (1.0 + pct) + flat


def pct_to_flat(white: float, pct_points: float = 1.0) -> float:
    """Exchange rate: 1 percentage point of ATK% is worth ``white / 100`` flat.

    This is the only number a player needs to compare a "+X% attack" roll
    against a "+Y flat attack" roll, and it is *fixed by the character and
    weapon*, not by the build. A 1000-white character trades 1% for 10
    flat; a 1200-white character trades it for 12.

    Corollary: once both are converted to attack points, they are
    interchangeable -- the marginal value of one more point of attack is
    always ``1 / current_total``, no matter which of the three sources it
    came from.
    """
    if white <= 0:
        raise ValueError("white attack must be positive")
    return white / 100.0 * pct_points


def attack_marginal_gain(white: float, pct: float, flat: float,
                         added_points: float = 1.0) -> float:
    """Relative gain of adding ``added_points`` raw attack.

    Since every source lands linearly, this is simply
    ``added / current_total`` -- the same dilution rule as any other zone.
    """
    total = attack_value(white, pct, flat)
    return added_points / total


def amplify_zone(*slots: Sequence[float]) -> float:
    """Damage amplification (伤害加深).

    Per the source table, the three categories of amplification -- all-element,
    element-specific, and skill-specific -- are **summed**. But the decoded
    pipeline multiplies nine separate slots, one per instance of the buff.

    The two statements reconcile as: *sum inside a slot, multiply across
    slots*. Each slot therefore represents one source (or one stack), and a
    player carrying three amplification sources fills three slots that
    multiply together -- which is why amplification does not dilute the way
    damage bonus does.

    Call this with one sequence per slot::

        amplify_zone([0.10, 0.15], [0.08])   # slot 1: 10% + 15%, slot 2: 8%
    """
    out = 1.0
    for slot in slots:
        out *= additive_zone(*slot)
    return max(out, 0.0)


def defense_zone_by_level(char_level: int | float, enemy_level: int | float,
                          ignore: float = 0.0, cap: float = DEFENSE_ZONE_CAP) -> float:
    """Same defence zone expressed purely in levels.

    The pipeline stores a defence constant ``K = 800 + 8 * level`` and an
    enemy defence value pulled from the enemy table. Both are multiples of 8,
    so the factor cancels::

        K   = 800 + 8 * char_level  = 8 * (char_level + 100)
        DEF = 8 * (enemy_level + 99)      <- read off the enemy table

        zone = K / (K + DEF)
             = (char + 100) / ((char + 100) + (enemy + 99))

    **Note the asymmetry: +100 on the attacker, +99 on the target.** A
    level-90 enemy has DEF 1512 = 8 * 189, not 1520. Writing +100 on both
    sides -- the natural guess -- is off by about 0.26%, which is invisible
    in play but wrong, and it is exactly the kind of detail that separates
    a formula copied from a screenshot from one read out of the data.
    """
    if char_level <= 0 or enemy_level <= 0:
        raise ValueError("levels must be positive")
    if ignore < 0:
        raise ValueError("ignore must be >= 0")
    a = float(char_level) + 100.0
    b = (float(enemy_level) + 99.0) * (1.0 - ignore)
    ratio = b / a
    if ratio <= -1.0:
        return cap
    return min(cap, 1.0 / (1.0 + ratio))


def defense_constant(char_level: int | float) -> float:
    """``K = 800 + 8 * level`` -- 1520 at level 90.

    This is the single most commonly mis-quoted constant in community
    spreadsheets: people copy ``/800`` and then wonder why their model is
    8-12% off at endgame.
    """
    if char_level <= 0:
        raise ValueError("char_level must be positive")
    return K_BASE + K_PER_LEVEL * float(int(char_level))


def defense_zone(defense: float, char_level: int | float,
                 ignore: float = 0.0, reduction: float = 0.0,
                 cap: float = DEFENSE_ZONE_CAP) -> float:
    """The defence multiplier: ``1 / (1 + DEF_eff / K)``, capped at ``cap``.

    Parameters
    ----------
    defense
        Target defence, from the enemy table.
    char_level
        Character level -- K depends on it.
    ignore
        Fraction of defence ignored (``0.4`` == 40%).
    reduction
        Fraction of defence removed by debuffs.

    Notes
    -----
    Both modifiers are applied multiplicatively to the *effective* defence,
    and ``DEF_eff`` may go negative (over-shredding), which pushes the zone
    above 1.0 -- hence the hard cap.
    """
    if defense < 0:
        raise ValueError("defense must be >= 0")
    for name, value in (("ignore", ignore), ("reduction", reduction)):
        if value < 0:
            raise ValueError(f"{name} must be >= 0")
    k = defense_constant(char_level)
    effective = defense * (1.0 - ignore) * (1.0 - reduction)
    ratio = effective / k
    if ratio <= -1.0:  # over-shredded past the constant: hit the hard cap
        return cap
    return min(cap, 1.0 / (1.0 + ratio))


def resistance_zone(resistance: float) -> float:
    """Three-segment resistance curve.

    ==================  ==========================  ============================
    resistance          multiplier                  design intent
    ==================  ==========================  ============================
    ``<= 0``            ``1 - res / 2``             negative resistance pays half
    ``0 < res < 0.8``   ``1 - res``                 linear middle
    ``>= 0.8``          ``1 / (1 + 5 * res)``       high resistance never reaches 0
    ==================  ==========================  ============================

    The two breakpoints are continuous (both give 1.0 at 0 and 0.2 at 0.8),
    which is what makes the curve feel smooth while still bounding both
    ends. "Guarantee the floor, bound the ceiling" -- the same trick shows
    up in defence shred caps and mitigation caps.
    """
    if resistance < -1.0:
        raise ValueError("resistance must be >= -1.0")
    if resistance <= RES_SOFT_FLOOR:
        return 1.0 - resistance / 2.0
    if resistance < RES_SOFT_CAP:
        return 1.0 - resistance
    return 1.0 / (1.0 + 5.0 * resistance)


def crit_multiplier_from_bonus(crit_damage_bonus: float) -> float:
    """Total crit multiplier from stacked crit-damage bonuses.

    ``crit_damage_bonus = 0.6`` (60% crit damage) gives ``2.1`` -- i.e. a
    crit hits for 210% of normal damage, because the 150% base is already
    baked in.
    """
    if crit_damage_bonus < 0:
        raise ValueError("crit_damage_bonus must be >= 0")
    return CRIT_BASE_MULTIPLIER + crit_damage_bonus


def crit_rate_total(*bonuses: float, base: float = CRIT_RATE_BASE,
                    cap: float = 1.0) -> float:
    """Total crit rate: 5% base plus every source, capped at 100%.

    Sources are: weapons, echo substats, a handful of characters' inherent
    passives, environment buffs, and specific ally buffs. They all land in
    the same pool, so they dilute against each other exactly like attack
    percentage does.
    """
    for value in bonuses:
        if value < 0:
            raise ValueError("crit rate bonuses must be >= 0")
    return min(cap, base + sum(bonuses))


def crit_zone(crit_rate: float, crit_multiplier: float,
              expected: bool = True) -> float:
    """Crit multiplier.

    With ``expected=True`` this returns ``1 + crit_rate * (crit_multiplier - 1)``,
    the value of averaging the non-crit and crit branches.

    ``crit_multiplier`` is the *total* multiplier of a crit (1.5 means a
    crit hits for 150%), not the bonus. Passing the bonus by mistake
    inflates the result by ``crit_rate`` -- a 10-15% error at endgame, and
    the single easiest bug to introduce in a hand-built sheet.
    """
    if not 0.0 <= crit_rate <= 1.0:
        raise ValueError("crit_rate must be in [0, 1]")
    if crit_multiplier < 1.0:
        raise ValueError("crit_multiplier must be >= 1.0 (total, not bonus)")
    if not expected:
        return crit_multiplier
    return 1.0 + crit_rate * (crit_multiplier - 1.0)


def additive_zone(*parts: float) -> float:
    """A zone whose sources *add* inside the bracket: ``1 + sum(parts)``.

    This is where dilution lives. Damage bonus, attack percentage and
    mitigation all behave this way.
    """
    return 1.0 + sum(parts)


def multiplicative_zone(*parts: float, floor_at_zero: bool = True) -> float:
    """A zone whose sources *multiply*: ``prod(1 + part)``.

    Amplification and final-damage groups behave this way in the decoded
    pipeline -- which is why they do **not** dilute, and why a single extra
    source of them is worth far more than another point of damage bonus.
    """
    out = 1.0
    for part in parts:
        out *= (1.0 + part)
    return max(out, 0.0) if floor_at_zero else out


def apply_ceiling(damage: float) -> int:
    """The pipeline rounds *up* to an integer per damage instance.

    Small, but it compounds: a 12-hit combo silently gains 12 damage, and
    a multi-hit ultimate can drift a fraction of a percent against a
    floating-point model. This is the residual in most "why is my sheet
    0.7% off" mysteries.
    """
    return int(math.ceil(damage - 1e-9))


def baseline_model(*, atk_white: float, atk_pct: float, atk_flat: float,
                   multiplier: float, crit_rate: float,
                   crit_multiplier: float, dmg_bonus: Sequence[float],
                   enemy_defense: float, char_level: int,
                   enemy_resistance: float,
                   amplify: Sequence[float] = (),
                   final: Sequence[float] = (),
                   vulnerability: Sequence[float] = (),
                   mitigation: Sequence[float] = (),
                   ignore_def: float = 0.0,
                   def_reduction: float = 0.0) -> DamageModel:
    """Assemble the nine zones into a :class:`DamageModel` for the toolkit.

    Every zone name matches the vocabulary used in the decode notes, so the
    table/attribution/optimiser modules can be pointed at real numbers.

    Note the attack zone's ``per_point_gain``: one "point" of investment is
    one percentage point of ATK%, which is worth ``white / 100`` attack --
    *not* ``total / 100``. Using the total overstates the gain from percent
    attack by exactly the ratio ``total / white``.
    """
    return DamageModel("wuwa baseline", [
        Zone("ATK", attack_value(atk_white, atk_pct, atk_flat),
             per_point_gain=pct_to_flat(atk_white)),
        Zone("Multiplier", multiplier),
        Zone("Crit", crit_zone(crit_rate, crit_multiplier),
             per_point_gain=0.01 * (crit_multiplier - 1.0)),
        Zone("DMG bonus", additive_zone(*dmg_bonus),
             per_point_gain=0.01),
        Zone("Amplify", amplify_zone(*amplify),
             per_point_gain=0.01),
        Zone("Resistance", resistance_zone(enemy_resistance)),
        Zone("Defense", defense_zone(enemy_defense, char_level,
                                     ignore=ignore_def,
                                     reduction=def_reduction)),
        Zone("Final", multiplicative_zone(*final), per_point_gain=0.0),
        Zone("Vulnerability", multiplicative_zone(*vulnerability),
             per_point_gain=0.0),
        Zone("Mitigation", 1.0 - min(sum(mitigation), 1.0)),
    ])
