from __future__ import annotations

from .models import EnemyState, EnemyType, HazardState, ProjectileState


def make_enemy_state(
    enemy_type: EnemyType,
    x: float,
    y: float,
    hp: float,
    damage: float,
    dash_cooldown: float,
    split_depth: int,
    elite: bool,
) -> EnemyState:
    return {
        "type": enemy_type,
        "x": x,
        "y": y,
        "hp": hp,
        "damage": damage,
        "dash_timer": 0.0,
        "dash_cooldown": dash_cooldown,
        "dash_vx": 0.0,
        "dash_vy": 0.0,
        "split_depth": split_depth,
        "elite": elite,
    }


def make_outage_state(
    enemy_type: EnemyType,
    x: float,
    y: float,
    hp: float,
    damage: float,
) -> EnemyState:
    outage = make_enemy_state(enemy_type, x, y, hp, damage, 99.0, 0, True)
    outage.update(
        {
            "max_hp": hp,
            "boss": True,
            "pulse_timer": 2.4,
            "summon_timer": 4.8,
            "rage": False,
        }
    )
    return outage


def make_projectile(
    x: float,
    y: float,
    vx: float,
    vy: float,
    damage: float,
    radius: float,
    color: tuple[int, int, int],
    pierce: int,
    source: str,
    chain: int,
    chain_range: float,
    chain_hits: int | None = None,
) -> ProjectileState:
    projectile: ProjectileState = {
        "x": x,
        "y": y,
        "vx": vx,
        "vy": vy,
        "damage": damage,
        "radius": radius,
        "color": color,
        "pierce": pierce,
        "source": source,
        "chain": chain,
        "chain_range": chain_range,
    }
    if chain_hits is not None:
        projectile["chain_hits"] = chain_hits
    return projectile


def make_hazard(
    x: float,
    y: float,
    radius: float,
    warn: float,
    duration: float,
    damage: float,
) -> HazardState:
    return {
        "x": x,
        "y": y,
        "radius": radius,
        "warn": warn,
        "duration": duration,
        "damage": damage,
        "hit": False,
    }
