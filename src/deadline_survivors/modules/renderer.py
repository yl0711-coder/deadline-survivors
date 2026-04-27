"""Rendering mixin for the Deadline Survivors runtime."""

from __future__ import annotations

from math import cos, pi, sin
from random import random

import pygame

from ..constants import (
    ACCENT,
    BG,
    BLUE,
    GREEN,
    GRID,
    HEIGHT,
    MUTED,
    OUTAGE_COLOR,
    PANEL,
    PROJECTILE_COLOR,
    RED,
    TEXT,
    WIDTH,
    XP_COLOR,
)
from ..models import EnemyState
from ..ui import draw_bar, draw_translucent_rect
from ..ui_screens import draw_title_overlay
from .overlay_renderer import OverlayRendererMixin


class RendererMixin(OverlayRendererMixin):
    def draw(self) -> None:
        shake_x, shake_y = self.current_screen_shake_offset()
        self.draw_world()
        self.draw_state_overlay()
        self.apply_screen_shake(shake_x, shake_y)

    def current_screen_shake_offset(self) -> tuple[int, int]:
        shake_x = 0
        shake_y = 0
        if self.state != "game_over" and self.shake_timer > 0 and self.shake_strength > 0:
            shake_x = int((random() - 0.5) * 2 * self.shake_strength)
            shake_y = int((random() - 0.5) * 2 * self.shake_strength)
        return shake_x, shake_y

    def draw_world(self) -> None:
        self.screen.fill(BG)
        self.draw_grid()
        self.draw_objective()
        self.draw_hazards()
        self.draw_flash_overlay()
        self.draw_xp_shards()
        self.draw_powerups()
        self.draw_drones()
        self.draw_projectiles()
        self.draw_enemies()
        self.draw_player_effects()
        if self.state not in {"title", "achievements", "game_over"}:
            self.draw_hud()
            self.draw_floating_texts()

    def draw_flash_overlay(self) -> None:
        if self.level_flash > 0:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((110, 78, 255, int(90 * self.level_flash)))
            self.screen.blit(overlay, (0, 0))
        elif self.hit_flash > 0:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((190, 42, 42, int(120 * self.hit_flash)))
            self.screen.blit(overlay, (0, 0))
        elif self.kill_flash > 0:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((255, 176, 60, int(70 * self.kill_flash)))
            self.screen.blit(overlay, (0, 0))

    def draw_xp_shards(self) -> None:
        for shard in self.xp_shards:
            pygame.draw.circle(self.screen, XP_COLOR, (int(shard["x"]), int(shard["y"])), 6)

    def draw_projectiles(self) -> None:
        for projectile in self.projectiles:
            pygame.draw.circle(
                self.screen,
                projectile.get("color", PROJECTILE_COLOR),
                (int(projectile["x"]), int(projectile["y"])),
                int(projectile["radius"]),
            )

    def draw_enemies(self) -> None:
        for enemy in self.enemies:
            self.draw_enemy(enemy)

    def draw_enemy(self, enemy: EnemyState) -> None:
        self.draw_enemy_body(enemy)
        self.draw_elite_marker(enemy)
        self.draw_enemy_detail(enemy)

    def draw_enemy_body(self, enemy: EnemyState) -> None:
        pygame.draw.circle(
            self.screen,
            enemy["type"].color,
            (int(enemy["x"]), int(enemy["y"])),
            int(enemy["type"].radius),
        )

    def draw_elite_marker(self, enemy: EnemyState) -> None:
        if enemy.get("elite"):
            pygame.draw.circle(
                self.screen,
                ACCENT,
                (int(enemy["x"]), int(enemy["y"])),
                int(enemy["type"].radius + 6),
                2,
            )

    def draw_enemy_detail(self, enemy: EnemyState) -> None:
        enemy_name = enemy["type"].name
        if enemy_name == "Meeting":
            pygame.draw.circle(self.screen, (230, 240, 255), (int(enemy["x"]), int(enemy["y"])), 6)
        elif enemy_name == "Alert":
            pygame.draw.circle(self.screen, (255, 233, 205), (int(enemy["x"]), int(enemy["y"])), 4)
            if enemy.get("dash_timer", 0) > 0:
                pygame.draw.circle(
                    self.screen,
                    (255, 255, 255),
                    (int(enemy["x"]), int(enemy["y"])),
                    int(enemy["type"].radius + 4),
                    2,
                )
        elif enemy_name == "Scope Creep":
            pygame.draw.circle(self.screen, (245, 228, 255), (int(enemy["x"]), int(enemy["y"])), 5)
        elif enemy_name == "Outage":
            pygame.draw.circle(self.screen, PANEL, (int(enemy["x"]), int(enemy["y"])), 12)
            pygame.draw.circle(self.screen, TEXT, (int(enemy["x"]), int(enemy["y"])), 6, 2)
            if enemy.get("rage"):
                pygame.draw.circle(
                    self.screen,
                    RED,
                    (int(enemy["x"]), int(enemy["y"])),
                    int(enemy["type"].radius + 10),
                    2,
                )
        elif enemy_name == "Bugling":
            pygame.draw.circle(self.screen, (255, 248, 255), (int(enemy["x"]), int(enemy["y"])), 3)

    def draw_player_effects(self) -> None:
        self.draw_player()
        if self.state == "game_over" and self.death_burst_timer > 0:
            self.draw_death_burst()
        if self.grace_timer > 0:
            pygame.draw.circle(
                self.screen,
                (255, 255, 255),
                (int(self.player_x), int(self.player_y)),
                int(self.player_radius + 6),
                2,
            )
        if self.pulse_unlocked:
            pygame.draw.circle(
                self.screen,
                (111, 82, 255),
                (int(self.player_x), int(self.player_y)),
                int(self.effective_pickup_radius() * 0.35),
                2,
            )

    def draw_state_overlay(self) -> None:
        if self.state == "title":
            draw_title_overlay(self)
        elif self.state == "help":
            self.draw_help_overlay()
        elif self.state == "about":
            self.draw_about_overlay()
        elif self.state == "achievements":
            self.draw_achievements_overlay()
        elif self.state == "level_up":
            self.draw_level_up_overlay()
        elif self.state == "paused":
            self.draw_paused_overlay()
        elif self.state == "game_over":
            self.draw_game_over_overlay()

    def apply_screen_shake(self, shake_x: int, shake_y: int) -> None:
        if shake_x or shake_y:
            shaken = self.screen.copy()
            self.screen.fill(BG)
            self.screen.blit(shaken, (shake_x, shake_y))

    def draw_player(self) -> None:
        """Render a readable little developer character without sprite assets."""
        skin = self.current_skin()
        x = int(self.player_x)
        y = int(self.player_y)
        lean_x = int(self.player_dx * 4)
        lean_y = int(self.player_dy * 3)
        self.draw_player_shadow(x, y)
        self.draw_player_legs(x, y, lean_x)
        self.draw_player_body(x, y, lean_x, lean_y, skin)
        self.draw_player_head(x, y, lean_x, lean_y, skin)
        self.draw_player_laptop(x, y, skin)

    def draw_player_shadow(self, x: int, y: int) -> None:
        shadow = pygame.Rect(x - 18, y + 24, 36, 9)
        pygame.draw.ellipse(self.screen, (8, 10, 14), shadow)

    def draw_player_legs(self, x: int, y: int, lean_x: int) -> None:
        left_leg = pygame.Rect(x - 11 + lean_x, y + 14, 8, 18)
        right_leg = pygame.Rect(x + 3 + lean_x, y + 14, 8, 18)
        pygame.draw.rect(self.screen, (63, 92, 145), left_leg, border_radius=4)
        pygame.draw.rect(self.screen, (63, 92, 145), right_leg, border_radius=4)

    def draw_player_body(self, x: int, y: int, lean_x: int, lean_y: int, skin: dict) -> None:
        body = pygame.Rect(x - 15 + lean_x, y - 4 + lean_y, 30, 27)
        pygame.draw.rect(self.screen, skin["body"], body, border_radius=9)
        pygame.draw.rect(self.screen, skin["outline"], body, 2, border_radius=9)
        pygame.draw.line(self.screen, skin["arms"], (x - 13, y + 3), (x - 24, y + 12), 4)
        pygame.draw.line(self.screen, skin["arms"], (x + 13, y + 3), (x + 24, y + 12), 4)

    def draw_player_head(self, x: int, y: int, lean_x: int, lean_y: int, skin: dict) -> None:
        pygame.draw.circle(self.screen, skin["skin"], (x + lean_x, y - 20 + lean_y), 13)
        pygame.draw.arc(
            self.screen,
            skin["hair"],
            (x - 12 + lean_x, y - 32 + lean_y, 24, 16),
            pi,
            pi * 2,
            5,
        )
        pygame.draw.circle(self.screen, TEXT, (x - 5 + lean_x, y - 22 + lean_y), 2)
        pygame.draw.circle(self.screen, TEXT, (x + 5 + lean_x, y - 22 + lean_y), 2)
        pygame.draw.arc(
            self.screen,
            (87, 58, 35),
            (x - 7 + lean_x, y - 21 + lean_y, 14, 12),
            0,
            pi,
            2,
        )

    def draw_player_laptop(self, x: int, y: int, skin: dict) -> None:
        laptop = pygame.Rect(x - 21, y + 5, 42, 19)
        pygame.draw.rect(self.screen, PANEL, laptop, border_radius=4)
        pygame.draw.rect(self.screen, ACCENT, laptop, 2, border_radius=4)
        self.blit(self.small_font, "</>", skin["screen"], x - 17, y + 5)
        pygame.draw.line(self.screen, MUTED, (x - 24, y + 27), (x + 24, y + 27), 4)

    def draw_grid(self) -> None:
        for x in range(0, WIDTH, 40):
            pygame.draw.line(self.screen, GRID, (x, 0), (x, HEIGHT), 1)
        for y in range(0, HEIGHT, 40):
            pygame.draw.line(self.screen, GRID, (0, y), (WIDTH, y), 1)

    def draw_hazards(self) -> None:
        if not self.hazards:
            return

        surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for hazard in self.hazards:
            center = (int(hazard["x"]), int(hazard["y"]))
            radius = int(hazard["radius"])
            if hazard["warn"] > 0:
                alpha = 80 + int(70 * min(1.0, hazard["warn"]))
                pygame.draw.circle(surface, (255, 75, 75, alpha), center, radius, 3)
                pygame.draw.circle(surface, (255, 75, 75, 42), center, max(8, radius - 14), 2)
            else:
                pygame.draw.circle(surface, (190, 35, 35, 64), center, radius)
                pygame.draw.circle(surface, (255, 95, 85, 180), center, radius, 3)
        self.screen.blit(surface, (0, 0))

    def draw_powerups(self) -> None:
        for powerup in self.powerups:
            x = int(powerup["x"])
            y = int(powerup["y"])
            radius = int(powerup["radius"])
            color = powerup["color"]
            pygame.draw.circle(self.screen, color, (x, y), radius)
            pygame.draw.circle(self.screen, TEXT, (x, y), radius, 2)

            if powerup["kind"] == "heal":
                pygame.draw.ellipse(self.screen, PANEL, (x - 7, y - 8, 14, 18), 2)
                pygame.draw.arc(self.screen, TEXT, (x - 5, y - 13, 10, 10), pi, pi * 2, 2)
                pygame.draw.line(self.screen, TEXT, (x - 6, y - 2), (x + 6, y - 2), 2)
            elif powerup["kind"] == "bomb":
                pygame.draw.circle(self.screen, RED, (x, y), 8)
                self.blit(self.small_font, "{}", TEXT, x - 10, y - 10)
                pygame.draw.line(self.screen, TEXT, (x + 4, y - 10), (x + 10, y - 16), 2)
            elif powerup["kind"] == "haste":
                points = [(x - 7, y - 10), (x + 3, y - 2), (x - 2, y), (x + 8, y + 10)]
                pygame.draw.lines(self.screen, TEXT, False, points, 3)

    def draw_drones(self) -> None:
        if self.drone_count <= 0:
            return
        for index in range(self.drone_count):
            angle = self.time_survived * 2.4 + index * (2 * pi / max(1, self.drone_count))
            x = int(self.player_x + cos(angle) * 34)
            y = int(self.player_y + sin(angle) * 34)
            pygame.draw.circle(self.screen, BLUE, (x, y), 8)
            pygame.draw.circle(self.screen, TEXT, (x, y), 8, 2)
            pygame.draw.line(self.screen, TEXT, (x - 4, y), (x + 4, y), 2)
            pygame.draw.line(self.screen, TEXT, (x, y - 4), (x, y + 4), 2)

    def draw_objective(self) -> None:
        if self.objective is None:
            return

        objective = self.objective
        center = (int(objective["x"]), int(objective["y"]))
        radius = int(objective["radius"])
        progress = max(0.0, min(1.0, objective["progress"] / objective["required"]))
        ttl_ratio = max(0.0, min(1.0, objective["ttl"] / 16.0))
        surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

        pygame.draw.circle(surface, (93, 201, 136, 32), center, radius)
        pygame.draw.circle(surface, (93, 201, 136, 150), center, radius, 3)
        pygame.draw.circle(surface, (255, 177, 66, 180), center, max(4, int(radius * progress)))
        pygame.draw.circle(surface, (19, 22, 29, 210), center, 14)
        pygame.draw.circle(surface, (239, 242, 248, 230), center, 5)

        timer_width = int(radius * 2 * ttl_ratio)
        timer_rect = pygame.Rect(center[0] - radius, center[1] + radius + 10, timer_width, 6)
        pygame.draw.rect(surface, (93, 201, 136, 190), timer_rect, border_radius=999)
        self.screen.blit(surface, (0, 0))

        label = f"Deploy {int(progress * 100)}%"
        self.blit(self.small_font, label, GREEN, center[0] - 44, center[1] - radius - 30)

    def draw_hud(self) -> None:
        """Draw a compact translucent HUD so gameplay remains visible underneath."""
        self.draw_hud_panel()
        outage = self.draw_hud_phase_status()
        self.draw_hud_player_bars()
        self.draw_hud_build_status()
        self.draw_hud_objective_hint(outage is not None)

    def draw_hud_panel(self) -> None:
        panel = pygame.Rect(18, 18, 372, 144)
        draw_translucent_rect(self.screen, panel, PANEL, 150, 16)
        pygame.draw.rect(self.screen, GRID, panel, 1, border_radius=16)

    def draw_hud_phase_status(self) -> EnemyState | None:
        self.blit(self.font, f"{self.current_phase().name}", TEXT, 28, 24)
        self.blit(self.small_font, f"Time {self.time_survived:05.1f}s", TEXT, 28, 58)
        self.blit(self.small_font, f"Lv {self.level}", TEXT, 170, 58)
        self.blit(self.small_font, self.current_difficulty().label, ACCENT, 232, 58)
        self.blit(self.small_font, f"Best {self.best_time:05.1f}s", MUTED, 28, 82)
        if self.current_phase().name == "Alert Storm":
            self.blit(self.small_font, "Pager noise rising", RED, 170, 82)
        if self.crisis_banner_timer > 0:
            self.blit(self.font, self.crisis_name, RED, 500, 28)

        outage = next((enemy for enemy in self.enemies if enemy["type"].name == "Outage"), None)
        if outage is not None:
            ratio = max(0.0, min(1.0, outage["hp"] / outage.get("max_hp", outage["hp"])))
            draw_bar(self.screen, self.small_font, 500, 58, 260, 12, ratio, OUTAGE_COLOR, "Outage")
        return outage

    def draw_hud_player_bars(self) -> None:
        hp_ratio = max(0.0, self.player_hp / self.player_max_hp)
        xp_ratio = max(0.0, min(1.0, self.xp / self.xp_to_level))
        draw_bar(
            self.screen,
            self.small_font,
            28,
            106,
            210,
            10,
            hp_ratio,
            RED,
            f"HP {int(self.player_hp)}",
        )
        draw_bar(
            self.screen,
            self.small_font,
            28,
            122,
            210,
            10,
            xp_ratio,
            BLUE,
            f"Insight {int(self.xp)}/{int(self.xp_to_level)}",
        )
        draw_bar(
            self.screen,
            self.small_font,
            28,
            138,
            210,
            10,
            self.momentum,
            GREEN,
            f"{self.momentum_tier}",
        )

    def draw_hud_build_status(self) -> None:
        status_y = 24
        self.blit(self.small_font, "P pause  |  Esc quit", MUTED, 930, status_y)
        status_y += 24
        if self.regen_interval > 0:
            self.blit(self.small_font, f"Regen {self.regen_interval:0.1f}s", MUTED, 930, status_y)
            status_y += 24
        if self.pierce > 0:
            self.blit(self.small_font, f"Pierce {self.pierce}", MUTED, 930, status_y)
            status_y += 24
        if self.focus_timer > 0:
            self.blit(self.small_font, f"Focus {self.focus_timer:0.1f}s", GREEN, 930, status_y)
            status_y += 24
        if self.haste_timer > 0:
            self.blit(self.small_font, f"CI Boost {self.haste_timer:0.1f}s", BLUE, 930, status_y)
            status_y += 24
        if self.momentum_tier != "Idle":
            self.blit(
                self.small_font,
                f"{self.momentum_tier}: Insight x{self.xp_multiplier():0.2f}",
                GREEN,
                930,
                status_y,
            )
            status_y += 24
        if self.drone_count > 0:
            self.blit(self.small_font, f"Pairs {self.drone_count}", MUTED, 930, status_y)
            status_y += 24
        if self.chain_count > 0:
            self.blit(self.small_font, f"Code Review {self.chain_count}", MUTED, 930, status_y)
            status_y += 24
        if self.failsafe_level > 0:
            cooldown = "ready" if self.failsafe_cooldown <= 0 else f"{self.failsafe_cooldown:0.1f}s"
            self.blit(self.small_font, f"Guard {cooldown}", MUTED, 930, status_y)
            status_y += 24
        if self.overclock_level > 0:
            self.blit(self.small_font, f"Overclock {self.overclock_level}", MUTED, 930, status_y)

    def draw_hud_objective_hint(self, has_outage: bool) -> None:
        if self.objective is not None:
            objective_y = 82 if has_outage else 58
            self.blit(self.small_font, "Optional: hold deploy window", GREEN, 500, objective_y)

    def draw_death_burst(self) -> None:
        """Render the brief failure burst behind the game-over report."""
        x = int(self.death_burst_x)
        y = int(self.death_burst_y)
        surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for radius, alpha, color in (
            (34, 170, ACCENT),
            (58, 110, RED),
            (86, 64, OUTAGE_COLOR),
        ):
            pygame.draw.circle(surface, (*color, alpha), (x, y), radius, 4)
        for index in range(10):
            angle = index * (2 * pi / 10)
            start = (int(x + cos(angle) * 18), int(y + sin(angle) * 18))
            end = (int(x + cos(angle) * 76), int(y + sin(angle) * 76))
            pygame.draw.line(surface, (*ACCENT, 125), start, end, 3)
        pygame.draw.circle(surface, (*TEXT, 200), (x, y), 8)
        self.screen.blit(surface, (0, 0))

    def draw_floating_texts(self) -> None:
        for item in self.floating_texts:
            alpha = max(0, min(255, int(255 * min(1.0, item["ttl"] / 0.7))))
            surface = self.small_font.render(item["text"], True, item["color"])
            surface.set_alpha(alpha)
            self.screen.blit(surface, (item["x"], item["y"]))

    def blit(
        self,
        font: pygame.font.Font,
        text: str,
        color: tuple[int, int, int],
        x: int,
        y: int,
    ) -> None:
        self.screen.blit(font.render(text, True, color), (x, y))
