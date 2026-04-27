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
    PURPLE,
    RED,
    TEXT,
    WIDTH,
    XP_COLOR,
)
from ..content import ACHIEVEMENT_DEFS, ACHIEVEMENT_GROUPS
from ..models import EnemyState
from ..ui import draw_bar, draw_translucent_rect, wrap_text
from ..ui_screens import draw_menu_option, draw_title_overlay, draw_title_scene


class RendererMixin:
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

    def draw_help_overlay(self) -> None:
        """Draw the scrollable title-screen help page."""
        self.draw_overlay_panel(150, 70, 980, 590)
        self.blit(self.large_font, "How To Play", TEXT, 210, 108)
        self.blit(self.small_font, "Up / Down scroll   |   Esc back", MUTED, 780, 126)
        lines = self.help_overlay_lines()
        start = min(self.help_scroll, max(0, len(lines) - 16))
        self.help_scroll = start
        self.draw_help_lines(lines[start : start + 16])
        self.draw_help_scrollbar(start, len(lines))

    def help_overlay_lines(self) -> list[tuple[str, str]]:
        content = [
            ("Controls", [
                "WASD or Arrow Keys: move the developer.",
                "P: pause or resume the run.",
                "Esc: quit during a run, or close this page.",
                "1 / 2 / 3: choose upgrades during level-up.",
                "On the title screen, 1 / 2 / 3 selects Easy, Medium, or Hard.",
            ]),
            ("Core Loop", [
                "Move constantly to build Momentum.",
                "Automatic patches target nearby issues.",
                "Collect Insight shards to level up.",
                "Deploy windows are optional risk-reward objectives.",
                "Powerups are short-term rescue tools.",
            ]),
            ("Upgrades", [
                "Patch Notes: more patch damage.",
                "Multicast: fire extra patches.",
                "Rollback Thread: patches pierce more issues.",
                "Code Review: patches chain into nearby issues.",
                "Pair Programmer: adds helper patches.",
                "Rollback Guard: low-health emergency pulse.",
                "Overclocked Build: Overdrive hits create bursts.",
            ]),
            ("Powerups", [
                "Coffee Break: recover part of your HP.",
                "Refactor Bomb: heavy screen damage; bosses can survive.",
                "CI Boost: temporarily ships patches faster.",
            ]),
        ]
        lines: list[tuple[str, str]] = []
        for heading, entries in content:
            lines.append(("heading", heading))
            for entry in entries:
                lines.append(("body", entry))
            lines.append(("space", ""))
        return lines

    def draw_help_lines(self, visible: list[tuple[str, str]]) -> None:
        y = 178
        for kind, text in visible:
            if kind == "heading":
                self.blit(self.font, text, ACCENT, 210, y)
                y += 34
            elif kind == "body":
                self.blit(self.small_font, text, TEXT, 238, y)
                y += 26
            else:
                y += 10

    def draw_help_scrollbar(self, start: int, line_count: int) -> None:
        ratio = start / max(1, line_count - 16)
        bar = pygame.Rect(1080, 176, 8, 410)
        pygame.draw.rect(self.screen, GRID, bar, border_radius=999)
        pygame.draw.rect(
            self.screen,
            ACCENT,
            (bar.x, int(bar.y + ratio * 300), bar.width, 110),
            border_radius=999,
        )

    def draw_about_overlay(self) -> None:
        """Draw the title-screen story page."""
        self.draw_overlay_panel(170, 92, 940, 548)
        self.blit(self.large_font, "Game Story", TEXT, 240, 138)
        self.blit(self.small_font, "Esc back", MUTED, 924, 150)
        story_lines = [
            "You are a developer trying to keep production alive before the deadline.",
            "Bugs, alerts, meetings, scope creep, and outages push in from every side.",
            "Your patches fire automatically, but survival depends on movement, upgrades,",
            "deploy timing, and knowing when to grab a rescue powerup.",
        ]
        for index, line in enumerate(story_lines):
            self.blit(self.small_font, line, TEXT, 240, 222 + index * 30)

        draw_title_scene(self, 440, 360, 390, 220)

    def draw_achievements_overlay(self) -> None:
        self.draw_overlay_panel(150, 60, 980, 610)
        self.blit(self.large_font, "Achievements", TEXT, 200, 94)

        achievements = self.progression["achievements"]
        totals = self.progression["totals"]
        unlocked_count = sum(1 for value in achievements.values() if value.get("unlocked"))
        completion_ratio = unlocked_count / max(1, len(ACHIEVEMENT_DEFS))

        self.draw_achievement_summary_card(200, 166, "Unlocked", f"{unlocked_count}/{len(ACHIEVEMENT_DEFS)}", ACCENT)
        self.draw_achievement_summary_card(418, 166, "Best Run", f"{float(totals['best_time']):05.1f}s", BLUE)
        self.draw_achievement_summary_card(636, 166, "Runs", str(totals["runs_played"]), PURPLE)
        self.draw_achievement_summary_card(854, 166, "Resolved", str(self.total_resolved_count()), GREEN)

        progress_rect = pygame.Rect(200, 256, 880, 48)
        pygame.draw.rect(self.screen, BG, progress_rect, border_radius=16)
        pygame.draw.rect(self.screen, GRID, progress_rect, 1, border_radius=16)
        self.blit(self.small_font, "Overall progress", MUTED, 224, 268)
        self.blit(self.font, f"{int(completion_ratio * 100)}%", TEXT, 224, 288)
        self.draw_achievement_progress_bar(314, 284, 230, 10, completion_ratio, GREEN)

        next_hint = self.next_achievement_hint()
        if next_hint is not None:
            hint_title, hint_description = next_hint
            self.blit(self.small_font, "Next target", MUTED, 590, 268)
            self.blit(self.font, hint_title, GREEN, 590, 286)
            self.blit(self.small_font, hint_description, MUTED, 784, 290)
        else:
            self.blit(self.font, "All current achievements unlocked.", GREEN, 590, 282)

        group_positions = [(190, 326), (650, 326), (190, 492), (650, 492)]
        for group_x, group_y, group in zip(
            [position[0] for position in group_positions],
            [position[1] for position in group_positions],
            ACHIEVEMENT_GROUPS,
        ):
            self.draw_achievement_group_card(group_x, group_y, group)

        self.blit(self.small_font, "A / Backspace / Esc return", ACCENT, 200, 644)

    def draw_achievement_summary_card(
        self,
        x: int,
        y: int,
        label: str,
        value: str,
        color: tuple[int, int, int],
    ) -> None:
        """Draw a compact top-level achievement metric."""
        rect = pygame.Rect(x, y, 190, 66)
        pygame.draw.rect(self.screen, BG, rect, border_radius=14)
        pygame.draw.rect(self.screen, GRID, rect, 1, border_radius=14)
        pygame.draw.circle(self.screen, color, (x + 22, y + 22), 7)
        self.blit(self.small_font, label, MUTED, x + 40, y + 12)
        self.blit(self.font, value, TEXT, x + 20, y + 34)

    def draw_achievement_group_card(
        self,
        x: int,
        y: int,
        group: tuple[str, tuple[int, int, int], str, list[tuple[str, str]]],
    ) -> None:
        """Draw one achievement category without long text collisions."""
        group_name, group_color, group_description, rows = group
        group_summary = {
            "Milestones": "First unlocks and core systems.",
            "Challenges": "Harder goals for confident runs.",
            "Build Goals": "Targets for different upgrade paths.",
            "Mastery": "Long-term account progress.",
        }.get(group_name, group_description)
        achievements = self.progression["achievements"]
        unlocked_in_group = sum(1 for key, _ in rows if achievements[key].get("unlocked"))
        self.draw_achievement_group_frame(x, y, group_name, group_color, group_summary, unlocked_in_group, len(rows))
        for row_index, (key, _) in enumerate(rows):
            self.draw_achievement_group_row(x, y + 74 + row_index * 22, key)

    def draw_achievement_group_frame(
        self,
        x: int,
        y: int,
        group_name: str,
        group_color: tuple[int, int, int],
        group_summary: str,
        unlocked_count: int,
        total_count: int,
    ) -> None:
        rect = pygame.Rect(x, y, 440, 142)
        pygame.draw.rect(self.screen, BG, rect, border_radius=16)
        pygame.draw.rect(self.screen, group_color, (x, y, rect.width, 5), border_radius=16)
        pygame.draw.rect(self.screen, GRID, rect, 1, border_radius=16)
        pygame.draw.circle(self.screen, group_color, (x + 22, y + 28), 8)
        self.blit(self.font, group_name, group_color, x + 40, y + 14)
        self.blit(self.small_font, f"{unlocked_count}/{total_count}", MUTED, x + 374, y + 20)
        self.blit(self.small_font, group_summary, MUTED, x + 20, y + 48)

    def draw_achievement_group_row(self, x: int, row_y: int, key: str) -> None:
        achievements = self.progression["achievements"]
        unlocked = achievements[key].get("unlocked", False)
        recent = self.achievement_is_recent(key)
        progress_ratio = self.achievement_progress_ratio(key)
        marker_color = ACCENT if recent else (GREEN if unlocked else GRID)
        progress_color = marker_color if unlocked or recent else MUTED
        text_color = TEXT if unlocked or recent else MUTED
        pygame.draw.circle(self.screen, marker_color, (x + 26, row_y + 7), 5)
        self.blit(self.small_font, ACHIEVEMENT_DEFS[key], text_color, x + 42, row_y - 3)
        if recent:
            self.blit(self.small_font, "NEW", ACCENT, x + 232, row_y - 3)
        self.blit(self.small_font, self.achievement_progress_text(key), progress_color, x + 286, row_y - 3)
        self.draw_achievement_progress_bar(
            x + 42,
            row_y + 15,
            190,
            5,
            progress_ratio,
            GREEN if unlocked else ACCENT,
        )

    def draw_achievement_progress_bar(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        ratio: float,
        color: tuple[int, int, int],
    ) -> None:
        ratio = max(0.0, min(1.0, ratio))
        pygame.draw.rect(self.screen, GRID, (x, y, width, height), border_radius=999)
        pygame.draw.rect(self.screen, color, (x, y, int(width * ratio), height), border_radius=999)

    def draw_paused_overlay(self) -> None:
        self.draw_overlay_panel(260, 180, 760, 280)
        self.blit(self.large_font, "Paused", TEXT, 360, 245)
        self.blit(self.font, "Press P to continue the deploy.", TEXT, 360, 330)
        self.blit(self.font, "Use Esc if you want to quit the run.", MUTED, 360, 375)

    def draw_floating_texts(self) -> None:
        for item in self.floating_texts:
            alpha = max(0, min(255, int(255 * min(1.0, item["ttl"] / 0.7))))
            surface = self.small_font.render(item["text"], True, item["color"])
            surface.set_alpha(alpha)
            self.screen.blit(surface, (item["x"], item["y"]))

    def draw_level_up_overlay(self) -> None:
        self.draw_overlay_panel(140, 120, 1000, 480)
        self.blit(self.large_font, "New Insight", TEXT, 200, 170)
        self.blit(self.font, "Choose one developer upgrade.", MUTED, 200, 235)

        for index, upgrade in enumerate(self.level_choices):
            rect = pygame.Rect(190 + index * 300, 290, 260, 220)
            pygame.draw.rect(self.screen, PANEL, rect, border_radius=18)
            pygame.draw.rect(self.screen, ACCENT, rect, 2, border_radius=18)
            self.blit(self.large_font, str(index + 1), ACCENT, rect.x + 20, rect.y + 14)
            self.blit(self.font, upgrade.name, TEXT, rect.x + 20, rect.y + 84)
            wrapped = wrap_text(self.small_font, upgrade.description, 220)
            for line_index, line in enumerate(wrapped):
                self.blit(self.small_font, line, MUTED, rect.x + 20, rect.y + 132 + line_index * 24)

    def draw_game_over_overlay(self) -> None:
        self.draw_overlay_panel(190, 88, 900, 540)
        title, description, tags = self.current_run_evaluation()
        self.draw_game_over_cards()
        self.draw_game_over_header()
        self.draw_game_over_evaluation(title, description, tags)
        self.draw_game_over_stats()
        self.draw_game_over_menu()

    def draw_game_over_cards(self) -> None:
        summary_rect = pygame.Rect(250, 204, 780, 154)
        stats_rect = pygame.Rect(250, 376, 780, 112)
        menu_rect = pygame.Rect(250, 506, 780, 94)
        for rect in (summary_rect, stats_rect, menu_rect):
            pygame.draw.rect(self.screen, BG, rect, border_radius=18)
            pygame.draw.rect(self.screen, GRID, rect, 1, border_radius=18)

    def draw_game_over_header(self) -> None:
        self.blit(self.font, "Deploy Failed", RED, 250, 128)
        self.blit(
            self.large_font,
            f"{self.time_survived:05.1f}s",
            TEXT,
            250,
            152,
        )
        self.blit(self.small_font, f"Best run {self.best_time:05.1f}s", MUTED, 520, 174)
        self.blit(self.small_font, f"Difficulty {self.current_difficulty().label}", ACCENT, 770, 174)

    def draw_game_over_evaluation(self, title: str, description: str, tags: list[str]) -> None:
        self.blit(self.small_font, "Run evaluation", MUTED, 276, 230)
        self.blit(self.font, title, ACCENT, 276, 256)
        wrapped = wrap_text(self.small_font, description, 560)
        for index, line in enumerate(wrapped[:2]):
            self.blit(self.small_font, line, MUTED, 276, 298 + index * 22)
        chip_x = 760
        if tags:
            for index, tag in enumerate(tags[:2]):
                self.draw_equipped_chip(chip_x, 248 + index * 36, tag, GREEN)
        if self.new_achievements:
            unlocked_names = [ACHIEVEMENT_DEFS.get(key, key) for key in self.new_achievements[:2]]
            self.blit(self.small_font, "Unlocked: " + " | ".join(unlocked_names), ACCENT, 276, 334)

    def draw_game_over_stats(self) -> None:
        stat_cards = [
            ("Resolved", self.run_resolved_count()),
            ("Insight", int(self.stats["insight"])),
            ("Deploys", self.stats["deploys"]),
            ("Powerups", self.stats["powerups"]),
        ]
        for index, (label, value) in enumerate(stat_cards):
            card = pygame.Rect(276 + index * 184, 400, 158, 64)
            pygame.draw.rect(self.screen, PANEL, card, border_radius=14)
            pygame.draw.rect(self.screen, GRID, card, 1, border_radius=14)
            self.blit(self.font, str(value), TEXT, card.x + 18, card.y + 10)
            self.blit(self.small_font, label, MUTED, card.x + 18, card.y + 40)

    def draw_game_over_menu(self) -> None:
        self.blit(self.small_font, "Choose next action", MUTED, 276, 524)
        menu_items = ["Restart", "Achievements", "Main Menu"]
        for index, label in enumerate(menu_items):
            draw_menu_option(self, 276 + index * 230, 552, label, index == self.game_over_menu_index)
        self.blit(self.small_font, "Left / Right select   Enter confirm   Space restart   1/2/3 difficulty", MUTED, 276, 608)

    def draw_overlay_panel(self, x: int, y: int, width: int, height: int) -> None:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 192 if self.state == "game_over" else 160))
        self.screen.blit(overlay, (0, 0))
        pygame.draw.rect(self.screen, PANEL, (x, y, width, height), border_radius=22)
        pygame.draw.rect(self.screen, ACCENT, (x, y, width, height), 2, border_radius=22)

    def draw_equipped_chip(
        self,
        x: int,
        y: int,
        label: str,
        color: tuple[int, int, int],
    ) -> None:
        text_width, _ = self.small_font.size(label)
        width = text_width + 30
        rect = pygame.Rect(x, y, width, 28)
        pygame.draw.rect(self.screen, PANEL, rect, border_radius=999)
        pygame.draw.rect(self.screen, color, rect, 2, border_radius=999)
        pygame.draw.circle(self.screen, color, (x + 14, y + 14), 5)
        self.blit(self.small_font, label, TEXT, x + 24, y + 5)

    def blit(
        self,
        font: pygame.font.Font,
        text: str,
        color: tuple[int, int, int],
        x: int,
        y: int,
    ) -> None:
        self.screen.blit(font.render(text, True, color), (x, y))
