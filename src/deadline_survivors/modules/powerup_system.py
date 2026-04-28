"""Powerup drops, pickup handling, and temporary rescue effects."""

from __future__ import annotations

from math import dist
from random import choice, random

from ..constants import ACCENT, BLUE, GREEN, HEIGHT, WIDTH
from ..models import EnemyState


class PowerupSystemMixin:
    def maybe_drop_powerup(self, enemy: EnemyState) -> None:
        """Drop short-term rescue tools without polluting level-up choices."""
        if enemy["type"].name == "Outage":
            self.spawn_powerup(choice(["heal", "bomb", "haste"]), enemy["x"], enemy["y"])
            return
        drop_roll = random()
        drop_bonus = 0.04 if enemy["type"].name in {"Meeting", "Scope Creep"} else 0.0
        if drop_roll >= 0.12 + drop_bonus:
            return

        if self.player_hp < self.player_max_hp * 0.55:
            kind = "heal"
        elif drop_roll < 0.04:
            kind = "bomb"
        elif drop_roll < 0.08:
            kind = "haste"
        else:
            kind = choice(["heal", "haste", "bomb"])
        self.spawn_powerup(kind, enemy["x"], enemy["y"])

    def spawn_powerup(self, kind: str, x: float, y: float) -> None:
        labels = {
            "heal": "Coffee Break",
            "bomb": "Refactor Bomb",
            "haste": "CI Boost",
        }
        colors = {
            "heal": GREEN,
            "bomb": ACCENT,
            "haste": BLUE,
        }
        self.powerups.append(
            {
                "kind": kind,
                "label": labels[kind],
                "color": colors[kind],
                "x": max(24, min(WIDTH - 24, x)),
                "y": max(24, min(HEIGHT - 24, y)),
                "radius": 16,
                "ttl": 14.0,
            }
        )

    def update_powerups(self, dt: float) -> None:
        remaining = []
        for powerup in self.powerups:
            powerup["ttl"] -= dt
            if powerup["ttl"] <= 0:
                continue
            if (
                dist((self.player_x, self.player_y), (powerup["x"], powerup["y"]))
                <= self.player_radius + powerup["radius"]
            ):
                self.apply_powerup(powerup["kind"])
            else:
                remaining.append(powerup)
        self.powerups = remaining

    def apply_powerup(self, kind: str) -> None:
        """Apply immediate or temporary effects from picked-up powerups."""
        self.stats["powerups"] += 1
        scaling = self.run_scaling_bonus()
        handlers = {
            "heal": self.apply_heal_powerup,
            "bomb": self.apply_bomb_powerup,
            "haste": self.apply_haste_powerup,
        }
        handler = handlers.get(kind)
        if handler:
            handler(scaling)

    def apply_heal_powerup(self, scaling: float) -> None:
        heal_amount = 28.0 * scaling
        recovered = min(heal_amount, self.player_max_hp - self.player_hp)
        self.player_hp = min(self.player_max_hp, self.player_hp + heal_amount)
        self.play_sound("pickup")
        self.spawn_floating_text(
            self.player_x,
            self.player_y - 44,
            f"Coffee +{int(recovered)} HP",
            GREEN,
        )

    def apply_bomb_powerup(self, scaling: float) -> None:
        defeated = self.damage_enemies_with_bomb(92.0 * scaling, scaling)
        self.kill_flash = 0.6
        self.play_sound("crisis")
        self.trigger_screen_shake(0.2, 5.5)
        self.spawn_floating_text(
            self.player_x,
            self.player_y - 52,
            f"Refactor x{defeated}",
            ACCENT,
        )

    def damage_enemies_with_bomb(self, bomb_damage: float, scaling: float) -> int:
        defeated = 0
        survivors = []
        for enemy in self.enemies:
            enemy["hp"] -= bomb_damage
            if enemy["hp"] <= 0:
                defeated += 1
                self.resolve_enemy(
                    enemy,
                    0.7 * scaling,
                    allow_powerup_drop=False,
                    allow_split=False,
                )
            else:
                survivors.append(enemy)
                if enemy["type"].name == "Outage":
                    self.spawn_floating_text(
                        enemy["x"] - 28,
                        enemy["y"] - 52,
                        "Outage damaged",
                        ACCENT,
                    )
        self.enemies = survivors
        return defeated

    def apply_haste_powerup(self, scaling: float) -> None:
        self.haste_timer = min(12.0, 7.0 * scaling)
        self.play_sound("pickup")
        self.spawn_floating_text(self.player_x, self.player_y - 44, "CI Boost", BLUE)
