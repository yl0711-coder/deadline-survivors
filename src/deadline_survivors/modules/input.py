"""Keyboard and menu input handling for the game runtime."""

from __future__ import annotations

from typing import Protocol

import pygame


class InputRuntime(Protocol):
    state: str
    menu_return_state: str
    help_scroll: int
    title_menu_index: int
    game_over_menu_index: int
    selected_difficulty: str
    level_choices: list

    def persist_progression_snapshot(self) -> None: ...
    def play_sound(self, key: str) -> None: ...
    def cycle_badge(self) -> None: ...
    def cycle_skin(self) -> None: ...
    def cycle_patch_theme(self) -> None: ...
    def start_run(self) -> None: ...
    def reset(self) -> None: ...
    def choose_upgrade(self, key: str) -> None: ...


def handle_keydown(game: InputRuntime, key: int) -> bool:
    if game.state == "achievements":
        handle_achievements_input(game, key)
        return False
    if game.state in {"help", "about"}:
        handle_info_input(game, key)
        return False
    if key == pygame.K_ESCAPE:
        game.persist_progression_snapshot()
        return True
    if game.state in {"playing", "paused"} and key == pygame.K_p:
        game.state = "paused" if game.state == "playing" else "playing"
        game.play_sound("pause")
        return False
    if game.state == "title" and handle_title_input(game, key):
        return False
    if game.state in {"title", "game_over"} and handle_shared_menu_input(game, key):
        return False
    if game.state == "game_over" and handle_game_over_input(game, key):
        return False
    if game.state == "level_up":
        handle_level_up_input(game, key)
    return False


def handle_achievements_input(game: InputRuntime, key: int) -> None:
    if key == pygame.K_ESCAPE or key in (pygame.K_a, pygame.K_BACKSPACE):
        game.state = game.menu_return_state


def handle_info_input(game: InputRuntime, key: int) -> None:
    if key == pygame.K_ESCAPE:
        game.state = "title"
    elif game.state == "help" and key == pygame.K_DOWN:
        game.help_scroll += 1
    elif game.state == "help" and key == pygame.K_UP:
        game.help_scroll = max(game.help_scroll - 1, 0)


def handle_title_input(game: InputRuntime, key: int) -> bool:
    if key == pygame.K_UP:
        game.title_menu_index = (game.title_menu_index - 1) % 3
        return True
    if key == pygame.K_DOWN:
        game.title_menu_index = (game.title_menu_index + 1) % 3
        return True
    if key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
        activate_title_menu_item(game)
        return True
    return False


def handle_shared_menu_input(game: InputRuntime, key: int) -> bool:
    if key == pygame.K_a:
        game.menu_return_state = game.state
        game.state = "achievements"
        return True
    if key == pygame.K_b:
        game.cycle_badge()
        return True
    if key == pygame.K_s:
        game.cycle_skin()
        return True
    if key == pygame.K_t:
        game.cycle_patch_theme()
        return True
    if key in (pygame.K_1, pygame.K_KP1):
        game.selected_difficulty = "casual"
    elif key in (pygame.K_2, pygame.K_KP2):
        game.selected_difficulty = "normal"
    elif key in (pygame.K_3, pygame.K_KP3):
        game.selected_difficulty = "crunch"
    else:
        return False
    return True


def handle_game_over_input(game: InputRuntime, key: int) -> bool:
    if key == pygame.K_LEFT:
        game.game_over_menu_index = (game.game_over_menu_index - 1) % 3
        return True
    if key == pygame.K_RIGHT:
        game.game_over_menu_index = (game.game_over_menu_index + 1) % 3
        return True
    if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        activate_game_over_menu_item(game)
        return True
    if key == pygame.K_SPACE:
        game.start_run()
        return True
    return False


def handle_level_up_input(game: InputRuntime, key: int) -> None:
    if key in (pygame.K_1, pygame.K_KP1):
        pick_choice(game, 0)
    elif key in (pygame.K_2, pygame.K_KP2):
        pick_choice(game, 1)
    elif key in (pygame.K_3, pygame.K_KP3):
        pick_choice(game, 2)


def pick_choice(game: InputRuntime, index: int) -> None:
    if 0 <= index < len(game.level_choices):
        game.choose_upgrade(game.level_choices[index].key)
        game.level_choices = []
        game.state = "playing"


def activate_title_menu_item(game: InputRuntime) -> None:
    """Run the currently highlighted title-menu action."""
    if game.title_menu_index == 0:
        game.start_run()
    elif game.title_menu_index == 1:
        game.help_scroll = 0
        game.state = "help"
    elif game.title_menu_index == 2:
        game.state = "about"


def activate_game_over_menu_item(game: InputRuntime) -> None:
    """Run the currently highlighted game-over action."""
    if game.game_over_menu_index == 0:
        game.start_run()
    elif game.game_over_menu_index == 1:
        game.menu_return_state = "game_over"
        game.state = "achievements"
    elif game.game_over_menu_index == 2:
        game.reset()
