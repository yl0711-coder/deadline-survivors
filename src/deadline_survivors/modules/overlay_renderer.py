"""Menu and overlay rendering for non-world game states."""

from __future__ import annotations

import pygame

from ..constants import ACCENT, BG, BLUE, GREEN, GRID, HEIGHT, MUTED, PANEL, PURPLE, RED, TEXT, WIDTH
from ..content import ACHIEVEMENT_DEFS, ACHIEVEMENT_GROUPS
from ..ui import wrap_text
from ..ui_screens import draw_menu_option, draw_title_scene


class OverlayRendererMixin:
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
            (
                "Controls",
                [
                    "WASD or Arrow Keys: move the developer.",
                    "P: pause or resume the run.",
                    "Esc: quit during a run, or close this page.",
                    "1 / 2 / 3: choose upgrades during level-up.",
                    "On the title screen, 1 / 2 / 3 selects Easy, Medium, or Hard.",
                ],
            ),
            (
                "Core Loop",
                [
                    "Move constantly to build Momentum.",
                    "Automatic patches target nearby issues.",
                    "Collect Insight shards to level up.",
                    "Deploy windows are optional risk-reward objectives.",
                    "Powerups are short-term rescue tools.",
                ],
            ),
            (
                "Upgrades",
                [
                    "Patch Notes: more patch damage.",
                    "Multicast: fire extra patches.",
                    "Rollback Thread: patches pierce more issues.",
                    "Code Review: patches chain into nearby issues.",
                    "Pair Programmer: adds helper patches.",
                    "Rollback Guard: low-health emergency pulse.",
                    "Overclocked Build: Overdrive hits create bursts.",
                ],
            ),
            (
                "Powerups",
                [
                    "Coffee Break: recover part of your HP.",
                    "Refactor Bomb: heavy screen damage; bosses can survive.",
                    "CI Boost: temporarily ships patches faster.",
                ],
            ),
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
        self.draw_achievement_group_frame(
            x,
            y,
            group_name,
            group_color,
            group_summary,
            unlocked_in_group,
            len(rows),
        )
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

    def draw_history_overlay(self) -> None:
        self.draw_overlay_panel(150, 70, 980, 590)
        self.blit(self.large_font, "Run History", TEXT, 200, 108)
        self.blit(self.small_font, "H / Backspace / Esc return", ACCENT, 820, 126)

        recent_runs = self.recent_run_history()
        if not recent_runs:
            self.blit(self.font, "No completed runs yet.", TEXT, 220, 220)
            self.blit(self.small_font, "Finish a run to build your local history.", MUTED, 220, 260)
            return

        self.draw_history_best_card(self.best_run_history()[0])
        self.draw_history_table(recent_runs)

    def draw_history_best_card(self, best_run: dict) -> None:
        rect = pygame.Rect(200, 168, 880, 92)
        pygame.draw.rect(self.screen, BG, rect, border_radius=18)
        pygame.draw.rect(self.screen, ACCENT, rect, 2, border_radius=18)
        self.blit(self.small_font, "Best local run", MUTED, 226, 186)
        self.blit(self.large_font, f"{float(best_run.get('survived', 0.0)):05.1f}s", TEXT, 226, 208)
        self.blit(self.font, str(best_run.get("evaluation", "Unknown Run")), ACCENT, 470, 202)
        self.blit(
            self.small_font,
            f"Lv {best_run.get('level', 1)}  {best_run.get('difficulty', '')}",
            MUTED,
            470,
            234,
        )
        tags = best_run.get("tags", [])
        if isinstance(tags, list):
            for index, tag in enumerate(tags[:2]):
                self.draw_equipped_chip(820, 188 + index * 32, str(tag), GREEN)

    def draw_history_table(self, recent_runs: list[dict]) -> None:
        self.blit(self.small_font, "Recent completed runs", MUTED, 204, 292)
        headers = [("Time", 204), ("Run", 408), ("Diff", 516), ("Lv", 604), ("Resolved", 662), ("Build", 780)]
        for label, x in headers:
            self.blit(self.small_font, label, ACCENT, x, 324)

        for index, entry in enumerate(recent_runs[:8]):
            y = 356 + index * 31
            row = pygame.Rect(198, y - 5, 884, 27)
            if index % 2 == 0:
                pygame.draw.rect(self.screen, BG, row, border_radius=8)
            self.blit(self.small_font, str(entry.get("ended_at", ""))[5:16], MUTED, 204, y)
            self.blit(self.small_font, f"{float(entry.get('survived', 0.0)):05.1f}s", TEXT, 408, y)
            self.blit(self.small_font, str(entry.get("difficulty", "")), MUTED, 516, y)
            self.blit(self.small_font, str(entry.get("level", 1)), MUTED, 604, y)
            self.blit(self.small_font, str(entry.get("resolved", 0)), MUTED, 662, y)
            tags = entry.get("tags", [])
            build = " / ".join(str(tag) for tag in tags[:2]) if isinstance(tags, list) else ""
            self.blit(self.small_font, build or str(entry.get("evaluation", "")), MUTED, 780, y)

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
