from __future__ import annotations


def insight_value_for_enemy(enemy_name: str) -> float:
    if enemy_name == "Alert":
        return 4.0
    if enemy_name == "Meeting":
        return 6.0
    if enemy_name == "Scope Creep":
        return 7.0
    if enemy_name == "Outage":
        return 24.0
    return 3.0


def fix_label_for_enemy(enemy_name: str) -> str:
    labels = {
        "Bug": "bug fixed",
        "Meeting": "meeting dodged",
        "Alert": "alert silenced",
        "Scope Creep": "scope trimmed",
        "Bugling": "tiny bug fixed",
        "Outage": "outage resolved",
    }
    return labels.get(enemy_name, "issue fixed")


def stat_key_for_enemy(enemy_name: str) -> str | None:
    stat_map = {
        "Bug": "bugs_fixed",
        "Bugling": "bugs_fixed",
        "Meeting": "meetings_dodged",
        "Alert": "alerts_silenced",
        "Scope Creep": "scope_trimmed",
        "Outage": "outages_resolved",
    }
    return stat_map.get(enemy_name)
