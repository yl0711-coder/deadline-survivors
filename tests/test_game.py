from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from deadline_survivors.game import ENEMY_TYPES, Game


class GameTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cwd = os.getcwd()
        os.chdir(self.temp_dir.name)
        self.home_patch = patch("pathlib.Path.home", return_value=Path(self.temp_dir.name) / "home")
        self.home_patch.start()
        self.game = Game()

    def tearDown(self) -> None:
        try:
            import pygame

            pygame.quit()
        finally:
            self.home_patch.stop()
            os.chdir(self.cwd)
            self.temp_dir.cleanup()

    def test_initial_state(self) -> None:
        self.assertEqual("title", self.game.state)
        self.assertEqual(1, self.game.level)
        self.assertEqual(0.0, self.game.time_survived)

    def test_all_upgrade_paths_are_callable(self) -> None:
        self.game.start_run()
        for key in {
            "damage",
            "speed",
            "projectiles",
            "magnet",
            "shield",
            "pierce",
            "pulse",
            "recovery",
        }:
            self.game.choose_upgrade(key)
        self.assertGreaterEqual(self.game.projectile_count, 2)
        self.assertGreaterEqual(self.game.pickup_radius, 100.0)
        self.assertTrue(self.game.pulse_unlocked)

    def test_draw_works_in_all_main_states(self) -> None:
        for state in ("title", "playing", "level_up", "game_over"):
            self.game.state = state
            if state == "level_up":
                self.game.level_choices = self.game.level_choices or []
                if not self.game.level_choices:
                    from deadline_survivors.game import UPGRADES

                    self.game.level_choices = UPGRADES[:3]
            self.game.draw()

    def test_short_update_loop_runs(self) -> None:
        self.game.start_run()
        for _ in range(240):
            self.game.update(1 / 60)
        self.assertGreater(self.game.time_survived, 3.5)
        self.assertIn(self.game.state, {"playing", "level_up", "game_over"})

    def test_level_up_state_is_reachable(self) -> None:
        self.game.start_run()
        self.game.xp = self.game.xp_to_level
        self.game.check_level_up()
        self.assertEqual("level_up", self.game.state)
        self.assertEqual(3, len(self.game.level_choices))

    def test_long_headless_run_reaches_later_phase_or_game_over(self) -> None:
        self.game.start_run()
        for _ in range(2400):
            if self.game.state == "game_over":
                break
            if self.game.state == "level_up":
                self.game.pick_choice(0)
            self.game.update(1 / 60)

        self.assertGreaterEqual(self.game.time_survived, 20.0)
        self.assertIn(
            self.game.current_phase().name,
            {"Incident Queue", "Alert Storm", "Deadline Crunch"},
        )
        self.assertIn(self.game.state, {"playing", "level_up", "game_over"})

    def test_scope_creep_splits_on_death(self) -> None:
        self.game.start_run()
        self.game.enemies = [
            {
                "type": next(enemy for enemy in ENEMY_TYPES if enemy.name == "Scope Creep"),
                "x": self.game.player_x + 120,
                "y": self.game.player_y,
                "hp": 0,
                "dash_timer": 0.0,
                "dash_cooldown": 1.0,
                "dash_vx": 0.0,
                "dash_vy": 0.0,
                "split_depth": 1,
            }
        ]
        self.game.update_enemies(1 / 60)
        self.assertTrue(any(enemy["type"].name == "Bugling" for enemy in self.game.enemies))

    def test_alert_can_enter_dash_state(self) -> None:
        self.game.start_run()
        alert_type = next(enemy for enemy in ENEMY_TYPES if enemy.name == "Alert")
        self.game.enemies = [
            {
                "type": alert_type,
                "x": self.game.player_x + 100,
                "y": self.game.player_y,
                "hp": 10,
                "dash_timer": 0.0,
                "dash_cooldown": 0.0,
                "dash_vx": 0.0,
                "dash_vy": 0.0,
                "split_depth": 0,
            }
        ]
        self.game.update_enemies(1 / 60)
        self.assertGreater(self.game.enemies[0]["dash_timer"], 0.0)

    def test_crisis_director_spawns_extra_pressure(self) -> None:
        self.game.start_run()
        self.game.time_survived = 60
        self.game.crisis_timer = 0
        self.game.update_crisis_director(1 / 60)
        self.assertGreaterEqual(len(self.game.enemies), 3)
        self.assertGreater(self.game.crisis_banner_timer, 0)
        self.assertIn(self.game.crisis_name, {"Standup Swarm", "Pager Storm", "Scope Review"})

    def test_projectile_damage_has_multicast_diminishing_returns(self) -> None:
        self.game.start_run()
        self.game.projectile_count = 6
        self.game.enemies = [
            {
                "type": next(enemy for enemy in ENEMY_TYPES if enemy.name == "Bug"),
                "x": self.game.player_x + 120,
                "y": self.game.player_y,
                "hp": 20,
                "dash_timer": 0.0,
                "dash_cooldown": 1.0,
                "dash_vx": 0.0,
                "dash_vy": 0.0,
                "split_depth": 0,
                "elite": False,
            }
        ]
        self.game.fire_projectiles()
        self.assertLess(self.game.projectiles[0]["damage"], self.game.projectile_damage)
        self.assertLessEqual(self.game.projectiles[0]["damage"], self.game.projectile_damage * 0.55)

    def test_deadline_zone_spawns_after_early_game(self) -> None:
        self.game.start_run()
        self.game.time_survived = 61
        self.game.hazard_timer = 0
        self.game.update_hazards(1 / 60)

        self.assertEqual(1, len(self.game.hazards))
        self.assertGreater(self.game.hazard_timer, 0)

    def test_deadline_zone_damages_stationary_player(self) -> None:
        self.game.start_run()
        self.game.player_hp = 100
        self.game.hazards = [
            {
                "x": self.game.player_x,
                "y": self.game.player_y,
                "radius": 90,
                "warn": 0.0,
                "duration": 1.0,
                "damage": 20.0,
                "hit": False,
            }
        ]

        self.game.update_hazards(1 / 60)

        self.assertEqual(80.0, self.game.player_hp)
        self.assertTrue(self.game.hazards[0]["hit"])

    def test_deploy_window_completion_grants_reward_and_focus(self) -> None:
        self.game.start_run()
        self.game.objective = {
            "name": "Deploy Window",
            "x": self.game.player_x,
            "y": self.game.player_y,
            "radius": 60,
            "progress": 2.1,
            "required": 2.15,
            "ttl": 10.0,
            "reward": 20.0,
        }

        self.game.update_objective(0.1)

        self.assertIsNone(self.game.objective)
        self.assertEqual(20.0, self.game.xp)
        self.assertGreater(self.game.focus_timer, 0)

    def test_momentum_improves_xp_multiplier_and_attack_cooldown(self) -> None:
        self.game.start_run()
        base_cooldown = self.game.effective_attack_cooldown()
        base_multiplier = self.game.xp_multiplier()
        base_pickup_radius = self.game.effective_pickup_radius()
        base_projectile_radius = self.game.projectile_radius()

        self.game.momentum = 1.0
        self.game.momentum_tier = self.game.current_momentum_tier()
        self.game.focus_timer = 6.0

        self.assertLess(self.game.effective_attack_cooldown(), base_cooldown)
        self.assertGreater(self.game.xp_multiplier(), base_multiplier)
        self.assertGreater(self.game.effective_pickup_radius(), base_pickup_radius)
        self.assertGreater(self.game.projectile_radius(), base_projectile_radius)
        self.assertGreater(self.game.momentum_damage_multiplier(), 1.0)

    def test_powerups_apply_heal_bomb_and_haste(self) -> None:
        self.game.start_run()
        self.game.player_hp = 40
        self.game.apply_powerup("heal")
        self.assertEqual(68, self.game.player_hp)

        self.game.apply_powerup("haste")
        self.assertGreater(self.game.haste_timer, 0)

        self.game.enemies = [
            {
                "type": next(enemy for enemy in ENEMY_TYPES if enemy.name == "Bug"),
                "x": self.game.player_x + 80,
                "y": self.game.player_y,
                "hp": 20,
                "dash_timer": 0.0,
                "dash_cooldown": 1.0,
                "dash_vx": 0.0,
                "dash_vy": 0.0,
                "split_depth": 0,
                "elite": False,
            }
        ]
        self.game.apply_powerup("bomb")
        self.assertEqual([], self.game.enemies)
        self.assertGreater(len(self.game.xp_shards), 0)

    def test_powerup_pickup_is_consumed_on_contact(self) -> None:
        self.game.start_run()
        self.game.spawn_powerup("haste", self.game.player_x, self.game.player_y)
        self.game.update_powerups(1 / 60)

        self.assertEqual([], self.game.powerups)
        self.assertGreater(self.game.haste_timer, 0)


if __name__ == "__main__":
    unittest.main()
