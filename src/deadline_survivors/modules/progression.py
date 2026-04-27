"""Cosmetic progression, level choices, and upgrade application."""

from __future__ import annotations

from random import choice

from ..constants import ACCENT, BLUE, GREEN, PURPLE, XP_COLOR
from ..content import (
    PATCH_THEMES,
    PLAYER_BADGES,
    PLAYER_SKINS,
    UPGRADES,
)
from ..models import Upgrade
from ..storage import save_progression
from .achievement_system import AchievementSystemMixin


class ProgressionMixin(AchievementSystemMixin):
    def unlocked_skins(self) -> list[str]:
        skins = []
        for key, skin in PLAYER_SKINS.items():
            unlock_key = skin["unlock"]
            if unlock_key is None or self.progression["achievements"].get(unlock_key, {}).get("unlocked"):
                skins.append(key)
        return skins

    def current_skin(self) -> dict:
        if self.selected_skin not in self.unlocked_skins():
            self.selected_skin = "default"
            self.progression["selected_skin"] = self.selected_skin
        return PLAYER_SKINS[self.selected_skin]

    def cycle_skin(self) -> None:
        skins = self.unlocked_skins()
        current_index = skins.index(self.selected_skin) if self.selected_skin in skins else 0
        self.selected_skin = skins[(current_index + 1) % len(skins)]
        self.progression["selected_skin"] = self.selected_skin
        save_progression(self.best_time, self.progression)

    def unlocked_badges(self) -> list[str]:
        badges = []
        for key, badge in PLAYER_BADGES.items():
            unlock_key = badge["unlock"]
            if unlock_key is None or self.progression["achievements"].get(unlock_key, {}).get("unlocked"):
                badges.append(key)
        return badges

    def current_badge(self) -> dict:
        if self.selected_badge not in self.unlocked_badges():
            self.selected_badge = "none"
            self.progression["selected_badge"] = self.selected_badge
        return PLAYER_BADGES[self.selected_badge]

    def cycle_badge(self) -> None:
        badges = self.unlocked_badges()
        current_index = badges.index(self.selected_badge) if self.selected_badge in badges else 0
        self.selected_badge = badges[(current_index + 1) % len(badges)]
        self.progression["selected_badge"] = self.selected_badge
        save_progression(self.best_time, self.progression)

    def unlocked_patch_themes(self) -> list[str]:
        themes = []
        for key, theme in PATCH_THEMES.items():
            unlock_key = theme["unlock"]
            if unlock_key is None or self.progression["achievements"].get(unlock_key, {}).get("unlocked"):
                themes.append(key)
        return themes

    def current_patch_theme(self) -> dict:
        if self.selected_patch_theme not in self.unlocked_patch_themes():
            self.selected_patch_theme = "default"
            self.progression["selected_patch_theme"] = self.selected_patch_theme
        return PATCH_THEMES[self.selected_patch_theme]

    def cycle_patch_theme(self) -> None:
        themes = self.unlocked_patch_themes()
        current_index = (
            themes.index(self.selected_patch_theme) if self.selected_patch_theme in themes else 0
        )
        self.selected_patch_theme = themes[(current_index + 1) % len(themes)]
        self.progression["selected_patch_theme"] = self.selected_patch_theme
        save_progression(self.best_time, self.progression)

    def check_level_up(self) -> None:
        """Enter the upgrade choice state when enough insight has been collected."""
        if self.xp < self.xp_to_level:
            return

        self.xp -= self.xp_to_level
        self.level += 1
        self.xp_to_level = self.xp_required_for_level(self.level)
        self.state = "level_up"
        self.level_choices = self.pick_level_choices()
        self.level_flash = 0.4
        self.spawn_floating_text(self.player_x, self.player_y - 54, f"Level {self.level}", ACCENT)

    def xp_required_for_level(self, level: int) -> float:
        """Return insight needed to advance from current level to the next level.

        The curve is intentionally steeper than enemy insight growth so individual
        shards become a smaller percentage of the bar at higher levels.
        """
        level_index = max(1, level)
        return float(round(70 + (level_index - 1) * 30 + (level_index - 1) ** 2 * 7))

    def pick_level_choices(self) -> list[Upgrade]:
        """Pick three distinct upgrade choices with light contextual weighting."""
        weighted = self.weighted_upgrade_pool()
        choices = self.pick_unique_upgrades(weighted, 3)
        self.fill_upgrade_choices(choices, 3)
        return choices

    def weighted_upgrade_pool(self) -> list[Upgrade]:
        weighted: list[Upgrade] = []
        for upgrade in UPGRADES:
            weighted.extend([upgrade] * self.upgrade_choice_weight(upgrade))
        return weighted

    def upgrade_choice_weight(self, upgrade: Upgrade) -> int:
        weight = 1
        if upgrade.key in {"damage", "projectiles", "speed"} and self.level <= 3:
            weight += 2
        if upgrade.key == "projectiles" and self.projectile_count >= 5:
            weight = 1
        if upgrade.key == "shield" and self.player_hp < self.player_max_hp * 0.45:
            weight += 2
        if upgrade.key == "pulse" and self.level >= 3:
            weight += 1
        if upgrade.key == "recovery" and self.level >= 4:
            weight += 1
        if upgrade.key == "pierce" and self.level >= 4:
            weight += 1
        if upgrade.key == "chain" and self.level >= 3:
            weight += 2
        if upgrade.key == "drone" and self.level >= 4:
            weight += 2
        if upgrade.key == "failsafe" and self.player_hp < self.player_max_hp * 0.55:
            weight += 2
        if upgrade.key == "overclock" and self.level >= 5:
            weight += 2
        return weight

    def pick_unique_upgrades(self, weighted: list[Upgrade], count: int) -> list[Upgrade]:
        choices: list[Upgrade] = []
        pool = weighted[:]
        while pool and len(choices) < count:
            candidate = choice(pool)
            if candidate not in choices:
                choices.append(candidate)
            pool = [item for item in pool if item.key != candidate.key]
        return choices

    def fill_upgrade_choices(self, choices: list[Upgrade], count: int) -> None:
        while len(choices) < count:
            fallback = choice(UPGRADES)
            if fallback not in choices:
                choices.append(fallback)

    def choose_upgrade(self, key: str) -> None:
        """Apply a run-long level-up upgrade."""
        scaling = self.run_scaling_bonus()
        handlers = {
            "damage": self.apply_damage_upgrade,
            "speed": self.apply_speed_upgrade,
            "projectiles": self.apply_projectiles_upgrade,
            "magnet": self.apply_magnet_upgrade,
            "shield": self.apply_shield_upgrade,
            "pierce": self.apply_pierce_upgrade,
            "pulse": self.apply_pulse_upgrade,
            "recovery": self.apply_recovery_upgrade,
            "chain": self.apply_chain_upgrade,
            "drone": self.apply_drone_upgrade,
            "failsafe": self.apply_failsafe_upgrade,
            "overclock": self.apply_overclock_upgrade,
        }
        handler = handlers.get(key)
        if handler:
            handler(scaling)
        self.play_sound("level")

    def apply_damage_upgrade(self, scaling: float) -> None:
        gain = int(8 * scaling)
        self.projectile_damage += gain
        self.spawn_floating_text(self.player_x, self.player_y - 44, f"+{gain} damage", ACCENT)

    def apply_speed_upgrade(self, scaling: float) -> None:
        del scaling
        self.player_speed *= 1.12 + min(0.07, (self.level - 1) * 0.006)
        self.spawn_floating_text(self.player_x, self.player_y - 44, "Move up", BLUE)

    def apply_projectiles_upgrade(self, scaling: float) -> None:
        del scaling
        if self.projectile_count < 5:
            self.projectile_count += 1
            self.spawn_floating_text(self.player_x, self.player_y - 44, "+1 patch", PURPLE)
            return
        self.attack_cooldown *= 0.94
        self.projectile_damage += 2
        self.spawn_floating_text(self.player_x, self.player_y - 44, "Multicast tuned", PURPLE)

    def apply_magnet_upgrade(self, scaling: float) -> None:
        self.pickup_radius += int(26 * scaling)
        self.spawn_floating_text(self.player_x, self.player_y - 44, "Radar up", XP_COLOR)

    def apply_shield_upgrade(self, scaling: float) -> None:
        max_hp_gain = int(24 * scaling)
        heal_gain = int(14 * scaling)
        self.player_max_hp += max_hp_gain
        self.player_hp = min(self.player_max_hp, self.player_hp + heal_gain)
        self.spawn_floating_text(self.player_x, self.player_y - 44, "Shield up", BLUE)

    def apply_pierce_upgrade(self, scaling: float) -> None:
        del scaling
        self.pierce += 1
        self.spawn_floating_text(self.player_x, self.player_y - 44, "Pierce +1", PURPLE)

    def apply_pulse_upgrade(self, scaling: float) -> None:
        self.pulse_unlocked = True
        self.pulse_timer = min(self.pulse_timer, 1.0)
        self.pulse_radius += int(22 * scaling)
        self.pulse_damage += int(8 * scaling)
        self.spawn_floating_text(self.player_x, self.player_y - 44, "Pulse online", PURPLE)

    def apply_recovery_upgrade(self, scaling: float) -> None:
        del scaling
        self.regen_interval = (
            6.0 if self.regen_interval == 0 else max(2.7, self.regen_interval * 0.82)
        )
        self.regen_timer = self.regen_interval
        self.spawn_floating_text(self.player_x, self.player_y - 44, "Recovery up", BLUE)

    def apply_chain_upgrade(self, scaling: float) -> None:
        del scaling
        self.chain_count += 1
        self.chain_range = 120 + self.chain_count * 20
        self.spawn_floating_text(self.player_x, self.player_y - 44, "Code review", PURPLE)

    def apply_drone_upgrade(self, scaling: float) -> None:
        del scaling
        self.drone_count += 1
        self.drone_cooldown = max(0.34, self.drone_cooldown * 0.86)
        self.drone_timer = min(self.drone_timer, 0.35)
        self.spawn_floating_text(self.player_x, self.player_y - 44, "Pair online", GREEN)

    def apply_failsafe_upgrade(self, scaling: float) -> None:
        del scaling
        self.failsafe_level += 1
        self.failsafe_cooldown = min(self.failsafe_cooldown, 3.0)
        self.spawn_floating_text(self.player_x, self.player_y - 44, "Guard armed", BLUE)

    def apply_overclock_upgrade(self, scaling: float) -> None:
        del scaling
        self.overclock_level += 1
        self.spawn_floating_text(self.player_x, self.player_y - 44, "Build overclocked", ACCENT)
