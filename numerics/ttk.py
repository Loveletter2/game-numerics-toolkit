"""Rotation -> DPS -> time to kill.

The damage model answers "how hard is one hit". A rotation answers "how long
does a rotation take". Enemy data answers "how much health is there". Put the
three together and you get the number a designer actually argues about:

    时间击杀 = 敌人血量 / (一轮总伤 / 一轮时长)

Why a separate module
----------------------
``DamageModel`` deliberately knows nothing about time. That keeps it easy to
reason about: it is a pure product of zones. But "this build is +12% damage"
and "this build kills 1.4 seconds faster" are different statements, and only
the second one survives contact with a real fight.

Units
-----
Frames, not seconds, because that is how action data is authored. The default
is 60 fps, matching the frame data tables.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable, Sequence

from .damage import DamageModel

DEFAULT_FPS = 60


@dataclass
class Action:
    """One entry in a rotation."""

    name: str
    multiplier: float          # 1.0 == 100% of the model's base damage
    frames: int
    hits: int = 1
    note: str = ""

    def __post_init__(self) -> None:
        if self.frames <= 0:
            raise ValueError(f"action {self.name!r} needs a positive frame count")
        if self.hits < 1:
            raise ValueError(f"action {self.name!r} needs at least one hit")


@dataclass
class Rotation:
    """An ordered list of actions that loops."""

    label: str = ""
    actions: list[Action] = field(default_factory=list)
    fps: int = DEFAULT_FPS

    @property
    def total_frames(self) -> int:
        return sum(a.frames for a in self.actions)

    @property
    def seconds(self) -> float:
        return self.total_frames / self.fps if self.fps else 0.0

    def __len__(self) -> int:
        return len(self.actions)

    @classmethod
    def from_dict(cls, data: dict) -> "Rotation":
        return cls(
            label=data.get("label", ""),
            fps=int(data.get("fps", DEFAULT_FPS)),
            actions=[Action(
                name=a["name"],
                multiplier=float(a["multiplier"]),
                frames=int(a["frames"]),
                hits=int(a.get("hits", 1)),
                note=a.get("note", ""),
            ) for a in data.get("actions", [])],
        )


def action_damage(model: DamageModel, action: Action) -> float:
    """One action's damage: base model value x multiplier x hits."""
    return model.total() * action.multiplier * action.hits


def rotation_damage(model: DamageModel, rotation: Rotation) -> float:
    return sum(action_damage(model, a) for a in rotation.actions)


def rotation_dps(model: DamageModel, rotation: Rotation) -> float:
    seconds = rotation.seconds
    if seconds <= 0:
        raise ValueError("rotation has no duration")
    return rotation_damage(model, rotation) / seconds


def time_to_kill(hp: float, dps: float) -> float:
    """Seconds needed to remove ``hp`` at ``dps``."""
    if dps <= 0:
        raise ValueError("dps must be positive")
    return hp / dps


def rotations_to_kill(hp: float, model: DamageModel, rotation: Rotation) -> float:
    """How many full rotations fit into one kill."""
    dmg = rotation_damage(model, rotation)
    if dmg <= 0:
        raise ValueError("rotation deals no damage")
    return hp / dmg


def damage_share(model: DamageModel, rotation: Rotation) -> list[dict]:
    """Per-action damage and share of the rotation, largest first."""
    total = rotation_damage(model, rotation)
    rows = []
    for a in rotation.actions:
        dmg = action_damage(model, a)
        rows.append({
            "action": a.name,
            "damage": round(dmg, 1),
            "share": round(dmg / total * 100, 2) if total else 0.0,
            "frames": a.frames,
            "dps": round(dmg / (a.frames / rotation.fps), 1) if a.frames else 0.0,
        })
    rows.sort(key=lambda r: -r["damage"])
    return rows


def ttk_report(model: DamageModel, rotation: Rotation,
               targets: Sequence[dict]) -> dict:
    """Compare this rotation against a list of ``{name, hp}`` targets.

    Returns per-target TTK in seconds and in rotations, which is how a
    designer usually frames the question ("does one rotation kill it?").
    """
    dmg = rotation_damage(model, rotation)
    dps = rotation_dps(model, rotation)
    rows = []
    for t in targets:
        hp = float(t["hp"])
        rows.append({
            "target": t.get("name", ""),
            "hp": hp,
            "ttk": round(time_to_kill(hp, dps), 1),
            "rotations": round(rotations_to_kill(hp, model, rotation), 2),
            "kill_in_one": dmg >= hp,
        })
    return {
        "rotation": rotation.label,
        "seconds": round(rotation.seconds, 2),
        "damage": round(dmg, 1),
        "dps": round(dps, 1),
        "targets": rows,
    }


def optimal_rotation_order(model: DamageModel,
                           actions: Iterable[Action]) -> list[Action]:
    """Sort by damage per frame, descending.

    Only meaningful when actions are freely reorderable. Real rotations are
    constrained by cooldowns and energy, so treat this as an upper bound on
    rotation efficiency rather than a schedule.
    """
    return sorted(actions, key=lambda a: -action_damage(model, a) / a.frames)


def efficiency_loss(model: DamageModel, rotation: Rotation) -> float:
    """How much damage per frame the given order gives up vs the best order.

    Returns a fraction: 0.0 means the rotation is already optimal by this
    metric.
    """
    best = optimal_rotation_order(model, rotation.actions)
    best_damage = sum(action_damage(model, a) for a in best)
    actual = rotation_damage(model, rotation)
    if best_damage <= 0:
        return 0.0
    return max(0.0, 1.0 - actual / best_damage)


def frames_from_seconds(seconds: float, fps: int = DEFAULT_FPS) -> int:
    return int(math.ceil(seconds * fps))
