from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict


Color = tuple[int, int, int]


@dataclass
class EnemyType:
    name: str
    radius: float
    speed: float
    hp: float
    damage: float
    color: Color
    weight: float


@dataclass
class Upgrade:
    key: str
    name: str
    description: str


@dataclass
class Phase:
    name: str
    duration: float
    spawn_base: float
    pressure: float


@dataclass(frozen=True)
class Difficulty:
    key: str
    label: str
    description: str
    enemy_hp_mult: float
    enemy_damage_mult: float
    spawn_interval_mult: float
    insight_mult: float


class EnemyState(TypedDict, total=False):
    type: EnemyType
    x: float
    y: float
    hp: float
    max_hp: float
    damage: float
    dash_timer: float
    dash_cooldown: float
    dash_vx: float
    dash_vy: float
    split_depth: int
    elite: bool
    boss: bool
    pulse_timer: float
    summon_timer: float
    rage: bool


class ProjectileState(TypedDict, total=False):
    x: float
    y: float
    vx: float
    vy: float
    damage: float
    radius: float
    color: Color
    pierce: int
    source: str
    chain: int
    chain_hits: int
    chain_range: float


class InsightShardState(TypedDict):
    x: float
    y: float
    value: float


class HazardState(TypedDict):
    x: float
    y: float
    radius: float
    warn: float
    duration: float
    damage: float
    hit: bool


class PowerupState(TypedDict):
    kind: str
    label: str
    color: Color
    x: float
    y: float
    radius: float
    ttl: float


class FloatingTextState(TypedDict):
    x: float
    y: float
    text: str
    color: Color
    ttl: float
    rise: float


class ObjectiveState(TypedDict):
    name: str
    x: float
    y: float
    radius: float
    progress: float
    required: float
    ttl: float
    reward: float
