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
from deadline_survivors.storage import load_progression


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
            "chain",
            "drone",
            "failsafe",
            "overclock",
        }:
            self.game.choose_upgrade(key)
        self.assertGreaterEqual(self.game.projectile_count, 2)
        self.assertGreaterEqual(self.game.pickup_radius, 100.0)
        self.assertTrue(self.game.pulse_unlocked)
        self.assertGreaterEqual(self.game.chain_count, 1)
        self.assertGreaterEqual(self.game.drone_count, 1)
        self.assertGreaterEqual(self.game.failsafe_level, 1)
        self.assertGreaterEqual(self.game.overclock_level, 1)

    def test_draw_works_in_all_main_states(self) -> None:
        for state in ("title", "playing", "level_up", "paused", "game_over", "achievements"):
            self.game.state = state
            if state == "game_over":
                self.game.new_achievements = ["first_deploy"]
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

    def test_boss_director_spawns_outage(self) -> None:
        self.game.start_run()
        self.game.time_survived = 80
        self.game.level = 9
        self.game.boss_timer = 0

        self.game.update_boss_director(1 / 60)

        self.assertTrue(any(enemy["type"].name == "Outage" for enemy in self.game.enemies))
        self.assertEqual("Production Outage", self.game.crisis_name)

    def test_outage_wave_and_support_create_pressure(self) -> None:
        self.game.start_run()
        self.game.spawn_outage_boss()
        outage = next(enemy for enemy in self.game.enemies if enemy["type"].name == "Outage")
        enemy_count_before = len(self.game.enemies)

        self.game.emit_outage_wave(outage)
        self.game.summon_outage_support(outage)

        self.assertGreater(len(self.game.hazards), 0)
        self.assertGreater(len(self.game.enemies), enemy_count_before)

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

    def test_chain_upgrade_spawns_follow_up_projectile(self) -> None:
        self.game.start_run()
        self.game.choose_upgrade("chain")
        self.game.enemies = [
            {
                "type": next(enemy for enemy in ENEMY_TYPES if enemy.name == "Bug"),
                "x": self.game.player_x + 60,
                "y": self.game.player_y,
                "hp": 50,
                "damage": 6.0,
                "dash_timer": 0.0,
                "dash_cooldown": 1.0,
                "dash_vx": 0.0,
                "dash_vy": 0.0,
                "split_depth": 0,
                "elite": False,
            },
            {
                "type": next(enemy for enemy in ENEMY_TYPES if enemy.name == "Bug"),
                "x": self.game.player_x + 110,
                "y": self.game.player_y,
                "hp": 50,
                "damage": 6.0,
                "dash_timer": 0.0,
                "dash_cooldown": 1.0,
                "dash_vx": 0.0,
                "dash_vy": 0.0,
                "split_depth": 0,
                "elite": False,
            },
        ]
        self.game.projectiles = [
            {
                "x": self.game.player_x + 60,
                "y": self.game.player_y,
                "vx": 0.0,
                "vy": 0.0,
                "damage": 10.0,
                "radius": 8,
                "color": (255, 255, 255),
                "pierce": 0,
                "source": "player",
                "chain": 1,
                "chain_range": 120.0,
            }
        ]

        self.game.update_projectiles(1 / 60)

        self.assertTrue(any(projectile.get("source") == "chain" for projectile in self.game.projectiles))

    def test_drone_upgrade_fires_helper_projectiles(self) -> None:
        self.game.start_run()
        self.game.choose_upgrade("drone")
        self.game.drone_timer = 0.0
        self.game.enemies = [
            {
                "type": next(enemy for enemy in ENEMY_TYPES if enemy.name == "Bug"),
                "x": self.game.player_x + 100,
                "y": self.game.player_y,
                "hp": 20,
                "damage": 6.0,
                "dash_timer": 0.0,
                "dash_cooldown": 1.0,
                "dash_vx": 0.0,
                "dash_vy": 0.0,
                "split_depth": 0,
                "elite": False,
            }
        ]

        self.game.update_drone(0.1)

        self.assertTrue(any(projectile.get("source") == "drone" for projectile in self.game.projectiles))

    def test_failsafe_upgrade_triggers_low_health_guard(self) -> None:
        self.game.start_run()
        self.game.choose_upgrade("failsafe")
        self.game.player_hp = 24
        self.game.enemies = [
            {
                "type": next(enemy for enemy in ENEMY_TYPES if enemy.name == "Bug"),
                "x": self.game.player_x + 20,
                "y": self.game.player_y,
                "hp": 20,
                "damage": 6.0,
                "dash_timer": 0.0,
                "dash_cooldown": 1.0,
                "dash_vx": 0.0,
                "dash_vy": 0.0,
                "split_depth": 0,
                "elite": False,
            }
        ]

        self.game.trigger_failsafe()

        self.assertGreater(self.game.player_hp, 24)
        self.assertGreater(self.game.grace_timer, 0)
        self.assertGreater(self.game.failsafe_cooldown, 0)

    def test_play_sound_is_safe_when_audio_is_unavailable(self) -> None:
        self.game.sound_enabled = False
        self.game.sounds = {}
        self.game.play_sound("patch")

    def test_difficulty_affects_spawned_enemy_stats(self) -> None:
        self.game.selected_difficulty = "casual"
        self.game.start_run()
        bug_type = next(enemy for enemy in ENEMY_TYPES if enemy.name == "Bug")
        self.game.add_enemy(bug_type, elite=False)
        casual_enemy = self.game.enemies[-1]

        self.game.selected_difficulty = "crunch"
        self.game.start_run()
        self.game.add_enemy(bug_type, elite=False)
        crunch_enemy = self.game.enemies[-1]

        self.assertLess(casual_enemy["hp"], crunch_enemy["hp"])
        self.assertLess(casual_enemy["damage"], crunch_enemy["damage"])

    def test_enemy_resolution_updates_stats(self) -> None:
        self.game.start_run()
        self.game.enemies = [
            {
                "type": next(enemy for enemy in ENEMY_TYPES if enemy.name == "Bug"),
                "x": self.game.player_x + 120,
                "y": self.game.player_y,
                "hp": 0,
                "damage": 6.0,
                "dash_timer": 0.0,
                "dash_cooldown": 1.0,
                "dash_vx": 0.0,
                "dash_vy": 0.0,
                "split_depth": 0,
                "elite": False,
            }
        ]

        self.game.update_enemies(1 / 60)

        self.assertEqual(1, self.game.stats["bugs_fixed"])

    def test_run_evaluation_prefers_outage_hunter(self) -> None:
        self.game.start_run()
        self.game.stats["outages_resolved"] = 2
        self.game.max_momentum = 0.9

        title, description, tags = self.game.current_run_evaluation()

        self.assertEqual("Outage Hunter", title)
        self.assertIn("production outages", description)
        self.assertIn("Boss Priority", tags)

    def test_run_evaluation_recognizes_pair_programming_build(self) -> None:
        self.game.start_run()
        self.game.drone_count = 2
        self.game.stats["bugs_fixed"] = 40

        title, _, tags = self.game.current_run_evaluation()

        self.assertEqual("Pair Programming Lead", title)
        self.assertIn("Support Build", tags)

    def test_unlock_achievement_marks_progression_once(self) -> None:
        self.game.start_run()

        self.game.unlock_achievement("first_deploy")
        self.game.unlock_achievement("first_deploy")

        self.assertTrue(self.game.progression["achievements"]["first_deploy"]["unlocked"])
        self.assertEqual(["first_deploy"], self.game.new_achievements)

    def test_finalize_run_progression_persists_totals_and_achievements(self) -> None:
        self.game.start_run()
        self.game.selected_difficulty = "crunch"
        self.game.time_survived = 601
        self.game.stats["bugs_fixed"] = 500
        self.game.stats["deploys"] = 5
        self.game.stats["outages_resolved"] = 1
        self.game.drone_count = 2
        self.game.max_chain_hits = 3

        self.game.finalize_run_progression()
        progression = load_progression()

        self.assertEqual(500, progression["totals"]["bugs_fixed"])
        self.assertEqual(5, progression["totals"]["deploys"])
        self.assertEqual(1, progression["totals"]["outages_resolved"])
        self.assertTrue(progression["achievements"]["crunch_survivor"]["unlocked"])
        self.assertTrue(progression["achievements"]["deploy_addict"]["unlocked"])
        self.assertTrue(progression["achievements"]["pair_flow"]["unlocked"])
        self.assertTrue(progression["achievements"]["review_cascade"]["unlocked"])
        self.assertTrue(progression["achievements"]["bug_tracker"]["unlocked"])

    def test_achievements_overlay_can_render_unlocked_and_locked_items(self) -> None:
        self.game.progression["achievements"]["first_deploy"]["unlocked"] = True
        self.game.new_achievements = ["first_deploy"]
        self.game.state = "achievements"

        self.game.draw()

    def test_achievement_unlocks_skin_and_cycle_persists_selection(self) -> None:
        self.assertEqual(["default"], self.game.unlocked_skins())

        self.game.progression["achievements"]["first_deploy"]["unlocked"] = True
        self.assertIn("nightshift", self.game.unlocked_skins())

        self.game.cycle_skin()
        progression = load_progression()

        self.assertEqual("nightshift", self.game.selected_skin)
        self.assertEqual("nightshift", progression["selected_skin"])


if __name__ == "__main__":
    unittest.main()
