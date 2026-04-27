from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import pygame

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from deadline_survivors.game import Game


class InputTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cwd = os.getcwd()
        os.chdir(self.temp_dir.name)
        self.home_patch = patch("pathlib.Path.home", return_value=Path(self.temp_dir.name) / "home")
        self.home_patch.start()
        self.game = Game()

    def tearDown(self) -> None:
        try:
            pygame.quit()
        finally:
            self.home_patch.stop()
            os.chdir(self.cwd)
            self.temp_dir.cleanup()

    def test_handle_keydown_title_menu_navigation_and_confirm(self) -> None:
        self.game.state = "title"

        self.assertFalse(self.game.handle_keydown(pygame.K_DOWN))
        self.assertEqual(1, self.game.title_menu_index)

        self.assertFalse(self.game.handle_keydown(pygame.K_UP))
        self.assertEqual(0, self.game.title_menu_index)

        self.assertFalse(self.game.handle_keydown(pygame.K_DOWN))
        self.assertFalse(self.game.handle_keydown(pygame.K_RETURN))
        self.assertEqual("help", self.game.state)

    def test_handle_keydown_help_about_and_achievements_return(self) -> None:
        self.game.state = "help"
        self.game.help_scroll = 0

        self.assertFalse(self.game.handle_keydown(pygame.K_DOWN))
        self.assertEqual(1, self.game.help_scroll)

        self.assertFalse(self.game.handle_keydown(pygame.K_UP))
        self.assertEqual(0, self.game.help_scroll)

        self.assertFalse(self.game.handle_keydown(pygame.K_ESCAPE))
        self.assertEqual("title", self.game.state)

        self.game.state = "about"
        self.assertFalse(self.game.handle_keydown(pygame.K_ESCAPE))
        self.assertEqual("title", self.game.state)

        self.game.menu_return_state = "game_over"
        self.game.state = "achievements"
        self.assertFalse(self.game.handle_keydown(pygame.K_BACKSPACE))
        self.assertEqual("game_over", self.game.state)

    def test_handle_keydown_shared_menu_shortcuts(self) -> None:
        self.game.state = "title"

        self.assertFalse(self.game.handle_keydown(pygame.K_1))
        self.assertEqual("casual", self.game.selected_difficulty)

        self.assertFalse(self.game.handle_keydown(pygame.K_2))
        self.assertEqual("normal", self.game.selected_difficulty)

        self.assertFalse(self.game.handle_keydown(pygame.K_3))
        self.assertEqual("crunch", self.game.selected_difficulty)

        self.assertFalse(self.game.handle_keydown(pygame.K_a))
        self.assertEqual("achievements", self.game.state)
        self.assertEqual("title", self.game.menu_return_state)

    def test_handle_keydown_game_over_menu_and_quick_restart(self) -> None:
        self.game.state = "game_over"

        self.assertFalse(self.game.handle_keydown(pygame.K_RIGHT))
        self.assertEqual(1, self.game.game_over_menu_index)

        self.assertFalse(self.game.handle_keydown(pygame.K_LEFT))
        self.assertEqual(0, self.game.game_over_menu_index)

        self.assertFalse(self.game.handle_keydown(pygame.K_SPACE))
        self.assertEqual("playing", self.game.state)

    def test_handle_keydown_level_up_and_pause_and_exit(self) -> None:
        from deadline_survivors.game import UPGRADES

        self.game.state = "level_up"
        self.game.level_choices = UPGRADES[:3]

        self.assertFalse(self.game.handle_keydown(pygame.K_2))
        self.assertEqual("playing", self.game.state)
        self.assertEqual([], self.game.level_choices)

        self.game.state = "playing"
        self.assertFalse(self.game.handle_keydown(pygame.K_p))
        self.assertEqual("paused", self.game.state)

        self.assertFalse(self.game.handle_keydown(pygame.K_p))
        self.assertEqual("playing", self.game.state)

        self.assertTrue(self.game.handle_keydown(pygame.K_ESCAPE))
