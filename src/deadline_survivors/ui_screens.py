from __future__ import annotations

from typing import Protocol

import pygame

from .constants import (
    ACCENT,
    ALERT_COLOR,
    BG,
    BLUE,
    BUG_COLOR,
    GREEN,
    GRID,
    MEETING_COLOR,
    MUTED,
    PANEL,
    PLAYER_COLOR,
    SCOPE_COLOR,
    TEXT,
)
from .models import Difficulty


class TitleScreenHost(Protocol):
    screen: pygame.Surface
    small_font: pygame.font.Font
    font: pygame.font.Font
    large_font: pygame.font.Font
    title_menu_index: int
    best_time: float

    def blit(
        self,
        font: pygame.font.Font,
        text: str,
        color: tuple[int, int, int],
        x: int,
        y: int,
    ) -> None: ...

    def current_difficulty(self) -> Difficulty: ...

    def current_patch_theme(self) -> dict: ...

    def draw_overlay_panel(self, x: int, y: int, width: int, height: int) -> None: ...


def draw_title_overlay(game: TitleScreenHost) -> None:
    game.draw_overlay_panel(170, 92, 940, 548)
    difficulty = game.current_difficulty()
    game.blit(game.large_font, "Deadline Survivors", TEXT, 238, 126)
    game.blit(
        game.small_font,
        "Ship patches. Dodge pressure. Survive the deadline.",
        MUTED,
        242,
        190,
    )

    draw_title_scene(game, 238, 228, 460, 284)

    menu_rect = pygame.Rect(738, 238, 280, 236)
    pygame.draw.rect(game.screen, BG, menu_rect, border_radius=18)
    pygame.draw.rect(game.screen, GRID, menu_rect, 1, border_radius=18)
    game.blit(game.font, "Menu", ACCENT, 768, 266)
    menu_items = ["Start Game", "How To Play", "Game Story"]
    for index, label in enumerate(menu_items):
        draw_menu_option(game, 768, 318 + index * 48, label, index == game.title_menu_index)

    game.blit(game.small_font, "Up / Down select", MUTED, 768, 482)
    game.blit(game.small_font, "Enter / Space confirm", MUTED, 768, 506)

    draw_title_status_bar(game, 238, 534, difficulty)


def draw_title_scene(game: TitleScreenHost, x: int, y: int, width: int, height: int) -> None:
    scene = pygame.Rect(x, y, width, height)
    pygame.draw.rect(game.screen, BG, scene, border_radius=18)
    pygame.draw.rect(game.screen, GRID, scene, 1, border_radius=18)
    game.blit(game.small_font, "Developer vs production pressure", MUTED, x + 28, y + 22)

    floor_y = y + height - 56
    pygame.draw.line(game.screen, GRID, (x + 38, floor_y), (x + width - 38, floor_y), 2)
    developer_x = x + width // 2
    developer_y = y + int(height * 0.58)
    pygame.draw.circle(game.screen, PLAYER_COLOR, (developer_x, developer_y - 50), 22)
    pygame.draw.rect(
        game.screen,
        BLUE,
        (developer_x - 24, developer_y - 26, 48, 56),
        border_radius=12,
    )
    pygame.draw.rect(
        game.screen,
        PANEL,
        (developer_x - 38, developer_y - 2, 76, 40),
        border_radius=8,
    )
    pygame.draw.rect(
        game.screen,
        GREEN,
        (developer_x - 30, developer_y + 5, 60, 24),
        2,
        border_radius=5,
    )
    game.blit(game.small_font, "</>", GREEN, developer_x - 18, developer_y + 3)

    enemies = [
        (x + int(width * 0.19), y + int(height * 0.54), BUG_COLOR, "Bug"),
        (x + int(width * 0.79), y + int(height * 0.45), ALERT_COLOR, "Alert"),
        (x + int(width * 0.84), y + int(height * 0.78), SCOPE_COLOR, "Scope"),
        (x + int(width * 0.27), y + int(height * 0.78), MEETING_COLOR, "Meeting"),
    ]
    for enemy_x, enemy_y, color, label in enemies:
        pygame.draw.circle(game.screen, color, (enemy_x, enemy_y), 20)
        pygame.draw.circle(game.screen, TEXT, (enemy_x, enemy_y), 5, 2)
        game.blit(game.small_font, label, MUTED, enemy_x - 34, enemy_y + 30)

    for offset in (0, 38, 76):
        pygame.draw.circle(
            game.screen,
            game.current_patch_theme()["color"],
            (developer_x + 58 + offset, developer_y - 8),
            6,
        )


def draw_title_status_bar(
    game: TitleScreenHost,
    x: int,
    y: int,
    difficulty: Difficulty,
) -> None:
    rect = pygame.Rect(x, y, 780, 76)
    pygame.draw.rect(game.screen, BG, rect, border_radius=14)
    pygame.draw.rect(game.screen, GRID, rect, 1, border_radius=14)
    game.blit(game.small_font, f"Difficulty: {difficulty.label}", ACCENT, x + 22, y + 16)
    game.blit(game.small_font, f"Best: {game.best_time:05.1f}s", MUTED, x + 220, y + 16)
    game.blit(game.small_font, "1 Easy   2 Medium   3 Hard", MUTED, x + 386, y + 16)
    game.blit(game.small_font, "A achievements   S/B/T cosmetics", MUTED, x + 22, y + 46)


def draw_menu_option(
    game: TitleScreenHost,
    x: int,
    y: int,
    label: str,
    selected: bool,
) -> None:
    rect = pygame.Rect(x, y, 230, 32)
    if selected:
        pygame.draw.rect(game.screen, PANEL, rect, border_radius=8)
        pygame.draw.rect(game.screen, ACCENT, rect, 2, border_radius=8)
    marker = ">" if selected else " "
    game.blit(game.small_font, marker, ACCENT if selected else MUTED, x + 12, y + 7)
    game.blit(game.small_font, label, TEXT if selected else MUTED, x + 42, y + 7)
