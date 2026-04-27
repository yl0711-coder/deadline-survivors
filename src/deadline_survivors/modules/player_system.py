"""Player movement, build effects, and floating feedback."""

from __future__ import annotations

from math import atan2, cos, dist, hypot, pi, sin

import pygame

from ..constants import BLUE, GREEN, HEIGHT, PURPLE, WIDTH
from ..state_factory import make_projectile


class PlayerSystemMixin:
    def update_regen(self, dt: float) -> None:
        if self.regen_interval <= 0 or self.player_hp >= self.player_max_hp:
            return
        self.regen_timer -= dt
        if self.regen_timer <= 0:
            self.player_hp = min(self.player_max_hp, self.player_hp + 2)
            self.regen_timer = self.regen_interval
            self.spawn_floating_text(self.player_x, self.player_y - 20, "+2", BLUE)

    def update_momentum(self, dt: float) -> None:
        """Reward active movement with visible Flow and Overdrive tiers."""
        previous_tier = self.momentum_tier
        moving = self.player_dx != 0 or self.player_dy != 0
        if moving:
            self.momentum = min(1.0, self.momentum + dt * 0.9)
        else:
            self.momentum = max(0.0, self.momentum - dt * 1.15)
        self.max_momentum = max(self.max_momentum, self.momentum)

        self.momentum_tier = self.current_momentum_tier()
        if self.momentum_tier != previous_tier and self.momentum_tier != "Idle":
            self.spawn_floating_text(
                self.player_x,
                self.player_y - 66,
                self.momentum_tier,
                GREEN,
            )
            if self.momentum_tier == "Overdrive":
                self.unlock_achievement("first_overdrive")

    def current_momentum_tier(self) -> str:
        if self.momentum >= 0.8:
            return "Overdrive"
        if self.momentum >= 0.35:
            return "Flow"
        return "Idle"

    def update_pulse(self, dt: float) -> None:
        self.pulse_timer -= dt
        if self.pulse_timer > 0:
            return
        self.pulse_timer = self.pulse_cooldown
        hit_count = 0
        for enemy in self.enemies:
            if dist((self.player_x, self.player_y), (enemy["x"], enemy["y"])) <= self.pulse_radius:
                enemy["hp"] -= self.pulse_damage
                hit_count += 1
        if hit_count:
            self.kill_flash = 0.22
            self.trigger_screen_shake(0.12, 2.0)
            self.spawn_floating_text(
                self.player_x,
                self.player_y - 42,
                f"Pulse x{hit_count}",
                PURPLE,
            )

    def update_drone(self, dt: float) -> None:
        if self.drone_count <= 0 or not self.enemies:
            return
        self.drone_timer -= dt
        if self.drone_timer > 0:
            return

        self.drone_timer = self.drone_cooldown
        damage_multiplier = 0.58 + min(0.3, self.drone_count * 0.08)
        orbit_radius = 34
        for index in range(self.drone_count):
            angle = self.time_survived * 2.4 + index * (2 * pi / max(1, self.drone_count))
            origin_x = self.player_x + cos(angle) * orbit_radius
            origin_y = self.player_y + sin(angle) * orbit_radius
            target = min(
                self.enemies,
                key=lambda enemy: dist((origin_x, origin_y), (enemy["x"], enemy["y"])),
            )
            shot_angle = atan2(target["y"] - origin_y, target["x"] - origin_x)
            self.projectiles.append(
                make_projectile(
                    origin_x,
                    origin_y,
                    cos(shot_angle) * self.projectile_speed * 0.88,
                    sin(shot_angle) * self.projectile_speed * 0.88,
                    self.projectile_damage * damage_multiplier,
                    max(4, self.projectile_radius() - 1),
                    BLUE,
                    max(0, self.pierce - 1),
                    "drone",
                    max(0, self.chain_count - 1),
                    self.chain_range,
                )
            )
        if self.fire_sound_timer <= 0:
            self.play_sound("patch")
            self.fire_sound_timer = 0.08

    def move_player(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        dx = float(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - float(
            keys[pygame.K_a] or keys[pygame.K_LEFT]
        )
        dy = float(keys[pygame.K_s] or keys[pygame.K_DOWN]) - float(
            keys[pygame.K_w] or keys[pygame.K_UP]
        )
        length = hypot(dx, dy)
        if length:
            dx /= length
            dy /= length
        self.player_dx = dx
        self.player_dy = dy

        self.player_x = max(
            self.player_radius,
            min(WIDTH - self.player_radius, self.player_x + dx * self.player_speed * dt),
        )
        self.player_y = max(
            self.player_radius,
            min(HEIGHT - self.player_radius, self.player_y + dy * self.player_speed * dt),
        )

    def update_floating_texts(self, dt: float) -> None:
        remaining = []
        for item in self.floating_texts:
            item["ttl"] -= dt
            item["y"] -= item["rise"] * dt
            if item["ttl"] > 0:
                remaining.append(item)
        self.floating_texts = remaining

    def spawn_floating_text(
        self,
        x: float,
        y: float,
        text: str,
        color: tuple[int, int, int],
    ) -> None:
        self.floating_texts.append(
            {
                "x": x,
                "y": y,
                "text": text,
                "color": color,
                "ttl": 0.7,
                "rise": 36.0,
            }
        )
