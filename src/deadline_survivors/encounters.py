from __future__ import annotations

from .models import EnemyType


def enemy_spawn_pool(enemy_types: list[EnemyType], phase_name: str) -> list[EnemyType]:
    available = []
    for enemy_type in enemy_types:
        weight = enemy_type.weight
        if phase_name == "Warmup":
            if enemy_type.name == "Meeting":
                weight *= 0.12
            if enemy_type.name == "Alert":
                weight *= 0.35
            if enemy_type.name == "Scope Creep":
                weight *= 0.05
        elif phase_name == "Incident Queue":
            if enemy_type.name == "Meeting":
                weight *= 0.6
            if enemy_type.name == "Scope Creep":
                weight *= 0.22
        elif phase_name == "Alert Storm":
            if enemy_type.name == "Alert":
                weight *= 1.28
            if enemy_type.name == "Meeting":
                weight *= 0.82
            if enemy_type.name == "Scope Creep":
                weight *= 0.6
        elif phase_name == "Deadline Crunch":
            if enemy_type.name == "Meeting":
                weight *= 1.12
            if enemy_type.name == "Scope Creep":
                weight *= 1.34
        available.extend([enemy_type] * max(1, int(weight * 10)))
    return available
