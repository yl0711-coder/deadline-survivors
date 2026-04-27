from __future__ import annotations

from math import atan2, cos, dist, hypot, pi, sin
from random import choice, random
import sys

import pygame

from .audio import AudioPlayer
from .combat import fix_label_for_enemy, insight_value_for_enemy, stat_key_for_enemy
from .content import (
    ACHIEVEMENT_DEFS,
    ACHIEVEMENT_GROUPS,
    DIFFICULTIES,
    ENEMY_TYPES,
    OUTAGE_BOSS,
    PATCH_THEMES,
    PHASES,
    PLAYER_BADGES,
    PLAYER_SKINS,
    UPGRADES,
)
from .encounters import enemy_spawn_pool
from .constants import (
    ACCENT,
    BG,
    BLUE,
    FPS,
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
    TITLE,
    WIDTH,
    XP_COLOR,
)
from .models import (
    Difficulty,
    EnemyState,
    EnemyType,
    FloatingTextState,
    HazardState,
    InsightShardState,
    ObjectiveState,
    Phase,
    PowerupState,
    ProjectileState,
    Upgrade,
)
from .state_factory import make_enemy_state, make_hazard, make_outage_state, make_projectile
from .storage import load_best_time, load_progression, save_best_time, save_progression
from .ui import draw_bar, draw_translucent_rect, wrap_text
from .ui_screens import draw_menu_option, draw_title_overlay, draw_title_scene


def create_font(size: int, *, bold: bool = False) -> pygame.font.Font:
    """Create a bundled pygame font without querying platform font registries."""
    font = pygame.font.Font(None, size)
    font.set_bold(bold)
    return font


class Game:
    def __init__(self) -> None:
        pygame.mixer.pre_init(44100, -16, 1, 512)
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = create_font(24)
        self.small_font = create_font(18)
        self.large_font = create_font(52, bold=True)
        self.best_time = load_best_time()
        self.progression = load_progression()
        self.selected_difficulty = "normal"
        self.selected_skin = self.progression.get("selected_skin", "default")
        self.selected_badge = self.progression.get("selected_badge", "none")
        self.selected_patch_theme = self.progression.get("selected_patch_theme", "default")
        self.audio = AudioPlayer()
        self.fire_sound_timer = 0.0
        self.shake_timer = 0.0
        self.shake_strength = 0.0
        self.menu_return_state = "title"
        self.title_menu_index = 0
        self.game_over_menu_index = 0
        self.help_scroll = 0
        self.reset()

    def reset(self) -> None:
        """Reset all run-local state before returning to title or starting."""
        self.state = "title"
        self.menu_return_state = "title"
        self.help_scroll = 0
        self.game_over_menu_index = 0
        self.time_survived = 0.0
        self.level = 1
        self.xp = 0.0
        self.xp_to_level = self.xp_required_for_level(self.level)
        self.player_x = WIDTH / 2
        self.player_y = HEIGHT / 2
        self.player_dx = 0.0
        self.player_dy = 0.0
        self.player_radius = 18
        self.player_speed = 265.0
        self.player_hp = 100.0
        self.player_max_hp = 100.0
        self.projectile_damage = 22.0
        self.projectile_speed = 470.0
        self.projectile_count = 1
        self.attack_cooldown = 0.48
        self.attack_timer = 0.08
        self.pickup_radius = 74.0
        self.contact_timer = 0.0
        self.grace_timer = 0.0
        self.spawn_timer = 1.2
        self.pierce = 0
        self.regen_interval = 0.0
        self.regen_timer = 0.0
        self.pulse_unlocked = False
        self.pulse_cooldown = 4.2
        self.pulse_timer = 1.8
        self.pulse_radius = 130.0
        self.pulse_damage = 22.0
        self.crisis_timer = 24.0
        self.boss_timer = 52.0
        self.crisis_name = ""
        self.crisis_banner_timer = 0.0
        self.hazard_timer = 12.0
        self.objective_timer = 14.0
        self.objective: ObjectiveState | None = None
        self.objective_successes = 0
        self.focus_timer = 0.0
        self.haste_timer = 0.0
        self.momentum = 0.0
        self.momentum_tier = "Idle"
        self.max_momentum = 0.0
        self.max_chain_hits = 1
        self.chain_count = 0
        self.chain_range = 0.0
        self.drone_count = 0
        self.drone_timer = 0.75
        self.drone_cooldown = 1.1
        self.failsafe_level = 0
        self.failsafe_cooldown = 0.0
        self.overclock_level = 0
        self.fire_sound_timer = 0.0
        self.shake_timer = 0.0
        self.shake_strength = 0.0
        self.stats = {
            "insight": 0.0,
            "bugs_fixed": 0,
            "meetings_dodged": 0,
            "alerts_silenced": 0,
            "scope_trimmed": 0,
            "outages_resolved": 0,
            "deploys": 0,
            "powerups": 0,
            "failsafe_triggers": 0,
        }
        self.hit_flash = 0.0
        self.level_flash = 0.0
        self.kill_flash = 0.0
        self.death_burst_timer = 0.0
        self.death_burst_x = self.player_x
        self.death_burst_y = self.player_y
        self.new_achievements: list[str] = []
        self.floating_texts: list[FloatingTextState] = []
        self.enemies: list[EnemyState] = []
        self.projectiles: list[ProjectileState] = []
        self.xp_shards: list[InsightShardState] = []
        self.hazards: list[HazardState] = []
        self.powerups: list[PowerupState] = []
        self.level_choices: list[Upgrade] = []

    def start_run(self) -> None:
        self.reset()
        self.state = "playing"

    def current_difficulty(self) -> Difficulty:
        return next(
            difficulty for difficulty in DIFFICULTIES if difficulty.key == self.selected_difficulty
        )

    def unlocked_skins(self) -> list[str]:
        skins = []
        for key, skin in PLAYER_SKINS.items():
            unlock_key = skin["unlock"]
            if unlock_key is None or self.progression["achievements"].get(unlock_key, {}).get("unlocked"):
                skins.append(key)
        return skins

    def current_skin(self) -> dict:
        if self.selected_skin not in self.unlocked_skins():
            self.selected_skin = "default"
            self.progression["selected_skin"] = self.selected_skin
        return PLAYER_SKINS[self.selected_skin]

    def cycle_skin(self) -> None:
        skins = self.unlocked_skins()
        current_index = skins.index(self.selected_skin) if self.selected_skin in skins else 0
        self.selected_skin = skins[(current_index + 1) % len(skins)]
        self.progression["selected_skin"] = self.selected_skin
        save_progression(self.best_time, self.progression)

    def unlocked_badges(self) -> list[str]:
        badges = []
        for key, badge in PLAYER_BADGES.items():
            unlock_key = badge["unlock"]
            if unlock_key is None or self.progression["achievements"].get(unlock_key, {}).get("unlocked"):
                badges.append(key)
        return badges

    def current_badge(self) -> dict:
        if self.selected_badge not in self.unlocked_badges():
            self.selected_badge = "none"
            self.progression["selected_badge"] = self.selected_badge
        return PLAYER_BADGES[self.selected_badge]

    def cycle_badge(self) -> None:
        badges = self.unlocked_badges()
        current_index = badges.index(self.selected_badge) if self.selected_badge in badges else 0
        self.selected_badge = badges[(current_index + 1) % len(badges)]
        self.progression["selected_badge"] = self.selected_badge
        save_progression(self.best_time, self.progression)

    def unlocked_patch_themes(self) -> list[str]:
        themes = []
        for key, theme in PATCH_THEMES.items():
            unlock_key = theme["unlock"]
            if unlock_key is None or self.progression["achievements"].get(unlock_key, {}).get("unlocked"):
                themes.append(key)
        return themes

    def current_patch_theme(self) -> dict:
        if self.selected_patch_theme not in self.unlocked_patch_themes():
            self.selected_patch_theme = "default"
            self.progression["selected_patch_theme"] = self.selected_patch_theme
        return PATCH_THEMES[self.selected_patch_theme]

    def cycle_patch_theme(self) -> None:
        themes = self.unlocked_patch_themes()
        current_index = (
            themes.index(self.selected_patch_theme) if self.selected_patch_theme in themes else 0
        )
        self.selected_patch_theme = themes[(current_index + 1) % len(themes)]
        self.progression["selected_patch_theme"] = self.selected_patch_theme
        save_progression(self.best_time, self.progression)

    def play_sound(self, key: str) -> None:
        self.audio.play(key)

    def trigger_screen_shake(self, duration: float, strength: float) -> None:
        self.shake_timer = max(self.shake_timer, duration)
        self.shake_strength = max(self.shake_strength, strength)

    def choose_upgrade(self, key: str) -> None:
        """Apply a run-long level-up upgrade."""
        scaling = self.run_scaling_bonus()
        if key == "damage":
            gain = int(8 * scaling)
            self.projectile_damage += gain
            self.spawn_floating_text(self.player_x, self.player_y - 44, f"+{gain} damage", ACCENT)
        elif key == "speed":
            self.player_speed *= 1.12 + min(0.07, (self.level - 1) * 0.006)
            self.spawn_floating_text(self.player_x, self.player_y - 44, "Move up", BLUE)
        elif key == "projectiles":
            if self.projectile_count < 5:
                self.projectile_count += 1
                self.spawn_floating_text(self.player_x, self.player_y - 44, "+1 patch", PURPLE)
            else:
                self.attack_cooldown *= 0.94
                self.projectile_damage += 2
                self.spawn_floating_text(
                    self.player_x,
                    self.player_y - 44,
                    "Multicast tuned",
                    PURPLE,
                )
        elif key == "magnet":
            self.pickup_radius += int(26 * scaling)
            self.spawn_floating_text(self.player_x, self.player_y - 44, "Radar up", XP_COLOR)
        elif key == "shield":
            max_hp_gain = int(24 * scaling)
            heal_gain = int(14 * scaling)
            self.player_max_hp += max_hp_gain
            self.player_hp = min(self.player_max_hp, self.player_hp + heal_gain)
            self.spawn_floating_text(self.player_x, self.player_y - 44, "Shield up", BLUE)
        elif key == "pierce":
            self.pierce += 1
            self.spawn_floating_text(self.player_x, self.player_y - 44, "Pierce +1", PURPLE)
        elif key == "pulse":
            self.pulse_unlocked = True
            self.pulse_timer = min(self.pulse_timer, 1.0)
            self.pulse_radius += int(22 * scaling)
            self.pulse_damage += int(8 * scaling)
            self.spawn_floating_text(self.player_x, self.player_y - 44, "Pulse online", PURPLE)
        elif key == "recovery":
            self.regen_interval = (
                6.0 if self.regen_interval == 0 else max(2.7, self.regen_interval * 0.82)
            )
            self.regen_timer = self.regen_interval
            self.spawn_floating_text(self.player_x, self.player_y - 44, "Recovery up", BLUE)
        elif key == "chain":
            self.chain_count += 1
            self.chain_range = 120 + self.chain_count * 20
            self.spawn_floating_text(self.player_x, self.player_y - 44, "Code review", PURPLE)
        elif key == "drone":
            self.drone_count += 1
            self.drone_cooldown = max(0.34, self.drone_cooldown * 0.86)
            self.drone_timer = min(self.drone_timer, 0.35)
            self.spawn_floating_text(self.player_x, self.player_y - 44, "Pair online", GREEN)
        elif key == "failsafe":
            self.failsafe_level += 1
            self.failsafe_cooldown = min(self.failsafe_cooldown, 3.0)
            self.spawn_floating_text(self.player_x, self.player_y - 44, "Guard armed", BLUE)
        elif key == "overclock":
            self.overclock_level += 1
            self.spawn_floating_text(self.player_x, self.player_y - 44, "Build overclocked", ACCENT)
        self.play_sound("level")

    def run(self) -> int:
        while True:
            dt = self.clock.tick(FPS) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.persist_progression_snapshot()
                    return 0
                if event.type == pygame.KEYDOWN:
                    if self.handle_keydown(event.key):
                        return 0

            if self.state == "playing":
                self.update(dt)
            elif self.state == "game_over":
                self.update_game_over_effects(dt)

            self.draw()
            pygame.display.flip()

    def handle_keydown(self, key: int) -> bool:
        if self.state == "achievements":
            self.handle_achievements_input(key)
            return False
        if self.state in {"help", "about"}:
            self.handle_info_input(key)
            return False
        if key == pygame.K_ESCAPE:
            self.persist_progression_snapshot()
            return True
        if self.state in {"playing", "paused"} and key == pygame.K_p:
            self.state = "paused" if self.state == "playing" else "playing"
            self.play_sound("pause")
            return False
        if self.state == "title" and self.handle_title_input(key):
            return False
        if self.state in {"title", "game_over"} and self.handle_shared_menu_input(key):
            return False
        if self.state == "game_over" and self.handle_game_over_input(key):
            return False
        if self.state == "level_up":
            self.handle_level_up_input(key)
        return False

    def handle_achievements_input(self, key: int) -> None:
        if key == pygame.K_ESCAPE or key in (pygame.K_a, pygame.K_BACKSPACE):
            self.state = self.menu_return_state

    def handle_info_input(self, key: int) -> None:
        if key == pygame.K_ESCAPE:
            self.state = "title"
        elif self.state == "help" and key == pygame.K_DOWN:
            self.help_scroll += 1
        elif self.state == "help" and key == pygame.K_UP:
            self.help_scroll = max(self.help_scroll - 1, 0)

    def handle_title_input(self, key: int) -> bool:
        if key == pygame.K_UP:
            self.title_menu_index = (self.title_menu_index - 1) % 3
            return True
        if key == pygame.K_DOWN:
            self.title_menu_index = (self.title_menu_index + 1) % 3
            return True
        if key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            self.activate_title_menu_item()
            return True
        return False

    def handle_shared_menu_input(self, key: int) -> bool:
        if key == pygame.K_a:
            self.menu_return_state = self.state
            self.state = "achievements"
            return True
        if key == pygame.K_b:
            self.cycle_badge()
            return True
        if key == pygame.K_s:
            self.cycle_skin()
            return True
        if key == pygame.K_t:
            self.cycle_patch_theme()
            return True
        if key in (pygame.K_1, pygame.K_KP1):
            self.selected_difficulty = "casual"
        elif key in (pygame.K_2, pygame.K_KP2):
            self.selected_difficulty = "normal"
        elif key in (pygame.K_3, pygame.K_KP3):
            self.selected_difficulty = "crunch"
        else:
            return False
        return True

    def handle_game_over_input(self, key: int) -> bool:
        if key == pygame.K_LEFT:
            self.game_over_menu_index = (self.game_over_menu_index - 1) % 3
            return True
        if key == pygame.K_RIGHT:
            self.game_over_menu_index = (self.game_over_menu_index + 1) % 3
            return True
        if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.activate_game_over_menu_item()
            return True
        if key == pygame.K_SPACE:
            self.start_run()
            return True
        return False

    def handle_level_up_input(self, key: int) -> None:
        if key in (pygame.K_1, pygame.K_KP1):
            self.pick_choice(0)
        elif key in (pygame.K_2, pygame.K_KP2):
            self.pick_choice(1)
        elif key in (pygame.K_3, pygame.K_KP3):
            self.pick_choice(2)

    def pick_choice(self, index: int) -> None:
        if 0 <= index < len(self.level_choices):
            self.choose_upgrade(self.level_choices[index].key)
            self.level_choices = []
            self.state = "playing"

    def activate_title_menu_item(self) -> None:
        """Run the currently highlighted title-menu action."""
        if self.title_menu_index == 0:
            self.start_run()
        elif self.title_menu_index == 1:
            self.help_scroll = 0
            self.state = "help"
        elif self.title_menu_index == 2:
            self.state = "about"

    def activate_game_over_menu_item(self) -> None:
        """Run the currently highlighted game-over action."""
        if self.game_over_menu_index == 0:
            self.start_run()
        elif self.game_over_menu_index == 1:
            self.menu_return_state = "game_over"
            self.state = "achievements"
        elif self.game_over_menu_index == 2:
            self.reset()

    def update(self, dt: float) -> None:
        """Advance one gameplay frame while the run is active."""
        self.time_survived += dt
        self.contact_timer = max(0.0, self.contact_timer - dt)
        self.grace_timer = max(0.0, self.grace_timer - dt)
        self.attack_timer -= dt
        self.spawn_timer -= dt
        self.hit_flash = max(0.0, self.hit_flash - dt * 2.6)
        self.level_flash = max(0.0, self.level_flash - dt * 1.8)
        self.kill_flash = max(0.0, self.kill_flash - dt * 4.2)
        self.crisis_banner_timer = max(0.0, self.crisis_banner_timer - dt)
        self.focus_timer = max(0.0, self.focus_timer - dt)
        self.haste_timer = max(0.0, self.haste_timer - dt)
        self.fire_sound_timer = max(0.0, self.fire_sound_timer - dt)
        self.shake_timer = max(0.0, self.shake_timer - dt)
        self.failsafe_cooldown = max(0.0, self.failsafe_cooldown - dt)
        if self.shake_timer <= 0:
            self.shake_strength = 0.0

        self.move_player(dt)
        self.update_momentum(dt)
        self.update_regen(dt)
        self.update_drone(dt)
        self.update_objective(dt)
        self.update_crisis_director(dt)
        self.update_boss_director(dt)
        self.update_hazards(dt)

        if self.spawn_timer <= 0:
            self.spawn_enemy()
            phase = self.current_phase()
            spawn_base = phase.spawn_base * self.current_difficulty().spawn_interval_mult
            self.spawn_timer = max(0.18, spawn_base - min(self.time_survived / 72, 0.18))

        if self.attack_timer <= 0:
            self.fire_projectiles()
            self.attack_timer = self.effective_attack_cooldown()
        if self.pulse_unlocked:
            self.update_pulse(dt)

        self.update_projectiles(dt)
        self.update_enemies(dt)
        self.update_xp(dt)
        self.update_powerups(dt)
        self.update_floating_texts(dt)
        self.check_level_up()

        if self.player_hp <= 0:
            self.state = "game_over"
            self.death_burst_timer = 1.0
            self.death_burst_x = self.player_x
            self.death_burst_y = self.player_y
            self.shake_timer = 0.0
            self.shake_strength = 0.0
            self.hit_flash = 0.0
            self.kill_flash = 0.0
            self.level_flash = 0.0
            self.floating_texts = []
            self.play_sound("fail")
            if self.time_survived > self.best_time:
                self.best_time = self.time_survived
                save_best_time(self.best_time)
            self.finalize_run_progression()

    def update_game_over_effects(self, dt: float) -> None:
        """Advance short-lived effects that remain visible after gameplay stops."""
        self.death_burst_timer = max(0.0, self.death_burst_timer - dt)

    def current_phase(self) -> Phase:
        elapsed = self.time_survived
        phase_start = 0.0
        for phase in PHASES:
            if elapsed < phase_start + phase.duration:
                return phase
            phase_start += phase.duration
        return PHASES[-1]

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

    def update_objective(self, dt: float) -> None:
        """Update optional deploy windows and their risk-reward progress."""
        if self.objective is None:
            if self.time_survived < 18 and self.level < 4:
                return
            self.objective_timer -= dt
            if self.objective_timer <= 0:
                self.spawn_objective()
            return

        objective = self.objective
        objective["ttl"] -= dt
        inside = (
            dist((self.player_x, self.player_y), (objective["x"], objective["y"]))
            <= objective["radius"]
        )
        if inside:
            objective["progress"] += dt * (1.0 + self.momentum * 0.25)
        else:
            objective["progress"] = max(0.0, objective["progress"] - dt * 0.35)

        if objective["progress"] >= objective["required"]:
            self.complete_objective(objective)
        elif objective["ttl"] <= 0:
            self.objective = None
            self.objective_timer = max(9.0, 18.0 - min(self.level, 16) * 0.45)

    def spawn_objective(self) -> None:
        angle = random() * pi * 2
        distance_from_player = 190 + random() * 260
        radius = 54.0
        x = max(radius, min(WIDTH - radius, self.player_x + cos(angle) * distance_from_player))
        y = max(radius, min(HEIGHT - radius, self.player_y + sin(angle) * distance_from_player))
        self.objective = {
            "name": "Deploy Window",
            "x": x,
            "y": y,
            "radius": radius,
            "progress": 0.0,
            "required": 2.15,
            "ttl": 16.0,
            "reward": 16.0 + self.level * 2.0,
        }
        self.spawn_floating_text(x - 42, y - 76, "Deploy window", GREEN)

    def complete_objective(self, objective: ObjectiveState) -> None:
        reward = objective["reward"]
        self.xp += reward
        self.stats["insight"] += reward
        self.focus_timer = 6.0
        self.objective_successes += 1
        self.stats["deploys"] += 1
        self.player_hp = min(self.player_max_hp, self.player_hp + 6)
        self.spawn_floating_text(
            objective["x"] - 36,
            objective["y"] - 72,
            f"+{int(reward)} insight",
            XP_COLOR,
        )
        self.spawn_floating_text(self.player_x, self.player_y - 48, "Focus mode", GREEN)
        self.play_sound("deploy")
        self.unlock_achievement("first_deploy")
        self.objective = None
        self.objective_timer = max(8.0, 20.0 - min(self.level, 18) * 0.5)

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

    def spawn_enemy(self) -> None:
        enemy_type = self.pick_enemy_type()
        self.add_enemy(enemy_type)

    def add_enemy(
        self,
        enemy_type: EnemyType,
        elite: bool | None = None,
        near_player: bool = False,
    ) -> None:
        if elite is None:
            elite_chance = 0.0
            if self.level >= 8:
                elite_chance += 0.03
            if self.level >= 12:
                elite_chance += 0.05
            if self.current_phase().name == "Deadline Crunch":
                elite_chance += 0.04
            elite = random() < elite_chance

        if near_player:
            angle = random() * pi * 2
            distance_from_player = 280 + random() * 140
            x = max(
                30,
                min(WIDTH - 30, self.player_x + cos(angle) * distance_from_player),
            )
            y = max(
                30,
                min(HEIGHT - 30, self.player_y + sin(angle) * distance_from_player),
            )
        else:
            side = choice(["top", "bottom", "left", "right"])
            if side == "top":
                x, y = random() * WIDTH, -30
            elif side == "bottom":
                x, y = random() * WIDTH, HEIGHT + 30
            elif side == "left":
                x, y = -30, random() * HEIGHT
            else:
                x, y = WIDTH + 30, random() * HEIGHT

        level_pressure = max(0, self.level - 7) * 2.15
        elite_multiplier = 2.2 if elite else 1.0
        difficulty = self.current_difficulty()
        self.enemies.append(
            make_enemy_state(
                enemy_type,
                x,
                y,
                (
                    enemy_type.hp
                    + level_pressure
                    + self.time_survived * (0.35 + self.current_phase().pressure * 0.22)
                )
                * difficulty.enemy_hp_mult
                * elite_multiplier,
                enemy_type.damage * difficulty.enemy_damage_mult,
                1.4 + random() * 0.9,
                1 if enemy_type.name == "Scope Creep" else 0,
                elite,
            )
        )

    def update_crisis_director(self, dt: float) -> None:
        """Occasionally inject a themed burst of enemies after the safe opening."""
        if self.time_survived < 55:
            return

        self.crisis_timer -= dt
        if self.crisis_timer > 0:
            return

        self.crisis_timer = max(14.0, 28.0 - min(self.level, 20) * 0.45)
        crisis = choice(["Standup Swarm", "Pager Storm", "Scope Review"])
        self.crisis_name = crisis
        self.crisis_banner_timer = 2.4
        self.spawn_floating_text(self.player_x, self.player_y - 70, crisis, RED)
        self.play_sound("crisis")
        self.trigger_screen_shake(0.2, 3.0)

        if crisis == "Standup Swarm":
            bug = next(enemy for enemy in ENEMY_TYPES if enemy.name == "Bug")
            meeting = next(enemy for enemy in ENEMY_TYPES if enemy.name == "Meeting")
            for _ in range(5):
                self.add_enemy(bug, elite=False, near_player=True)
            self.add_enemy(meeting, elite=self.level >= 10, near_player=True)
        elif crisis == "Pager Storm":
            alert = next(enemy for enemy in ENEMY_TYPES if enemy.name == "Alert")
            for index in range(4):
                self.add_enemy(alert, elite=index == 0 and self.level >= 12, near_player=True)
        else:
            scope = next(enemy for enemy in ENEMY_TYPES if enemy.name == "Scope Creep")
            meeting = next(enemy for enemy in ENEMY_TYPES if enemy.name == "Meeting")
            for _ in range(2):
                self.add_enemy(scope, elite=self.level >= 14 and random() < 0.5, near_player=True)
            self.add_enemy(meeting, elite=False, near_player=True)

    def update_boss_director(self, dt: float) -> None:
        if self.time_survived < 72 and self.level < 8:
            return
        if any(enemy["type"].name == "Outage" for enemy in self.enemies):
            return

        self.boss_timer -= dt
        if self.boss_timer > 0:
            return

        self.boss_timer = max(34.0, 58.0 - min(self.level, 18) * 1.15)
        self.spawn_outage_boss()

    def spawn_outage_boss(self) -> None:
        angle = random() * pi * 2
        distance_from_player = 320 + random() * 90
        x = max(42, min(WIDTH - 42, self.player_x + cos(angle) * distance_from_player))
        y = max(42, min(HEIGHT - 42, self.player_y + sin(angle) * distance_from_player))
        difficulty = self.current_difficulty()
        hp = (
            OUTAGE_BOSS.hp
            + max(0, self.level - 8) * 18
            + self.time_survived * 0.95
        ) * difficulty.enemy_hp_mult
        self.enemies.append(
            make_outage_state(
                OUTAGE_BOSS,
                x,
                y,
                hp,
                OUTAGE_BOSS.damage * difficulty.enemy_damage_mult,
            )
        )
        self.crisis_name = "Production Outage"
        self.crisis_banner_timer = 2.8
        self.play_sound("crisis")
        self.trigger_screen_shake(0.22, 4.8)
        self.spawn_floating_text(x - 46, y - 76, "Production Outage", RED)

    def update_hazards(self, dt: float) -> None:
        """Create red floor pressure so strong builds still need to move."""
        if self.time_survived >= 60 or self.level >= 10:
            self.hazard_timer -= dt
            if self.hazard_timer <= 0:
                self.spawn_hazard()
                pressure = min(
                    6.0,
                    max(0, self.level - 8) * 0.42 + self.current_phase().pressure * 2.4,
                )
                self.hazard_timer = max(4.4, 10.5 - pressure)

        active_hazards = []
        for hazard in self.hazards:
            hazard["warn"] -= dt
            if hazard["warn"] <= 0:
                hazard["duration"] -= dt
                if (
                    not hazard["hit"]
                    and self.grace_timer <= 0
                    and dist((self.player_x, self.player_y), (hazard["x"], hazard["y"]))
                    <= hazard["radius"] + self.player_radius
                ):
                    self.player_hp -= hazard["damage"]
                    self.grace_timer = 0.5
                    self.hit_flash = 0.45
                    hazard["hit"] = True
                    self.spawn_floating_text(
                        self.player_x,
                        self.player_y - 30,
                        f"-{int(hazard['damage'])} zone",
                        RED,
                    )
            if hazard["duration"] > 0:
                active_hazards.append(hazard)
        self.hazards = active_hazards

    def spawn_hazard(self) -> None:
        radius = min(98.0, 64.0 + max(0, self.level - 10) * 3.0)
        lead_x = self.player_dx * 68.0
        lead_y = self.player_dy * 68.0
        jitter_x = (random() - 0.5) * 60.0
        jitter_y = (random() - 0.5) * 60.0
        x = max(radius, min(WIDTH - radius, self.player_x + lead_x + jitter_x))
        y = max(radius, min(HEIGHT - radius, self.player_y + lead_y + jitter_y))
        damage = 12.0 + min(12.0, max(0, self.level - 10) * 1.0)
        self.hazards.append(
            make_hazard(x, y, radius, 1.05, 1.65, damage)
        )

    def pick_enemy_type(self) -> EnemyType:
        return choice(enemy_spawn_pool(ENEMY_TYPES, self.current_phase().name))

    def fire_projectiles(self) -> None:
        if not self.enemies:
            return

        sorted_enemies = sorted(
            self.enemies,
            key=lambda enemy: dist((self.player_x, self.player_y), (enemy["x"], enemy["y"])),
        )
        targets = sorted_enemies[: min(self.projectile_count, 6)]
        damage_multiplier = self.projectile_damage_multiplier()
        for target in targets:
            angle = atan2(target["y"] - self.player_y, target["x"] - self.player_x)
            self.projectiles.append(
                make_projectile(
                    self.player_x,
                    self.player_y,
                    cos(angle) * self.projectile_speed,
                    sin(angle) * self.projectile_speed,
                    self.projectile_damage
                    * damage_multiplier
                    * self.momentum_damage_multiplier(),
                    self.projectile_radius(),
                    self.projectile_color(),
                    self.pierce,
                    "player",
                    self.chain_count,
                    self.chain_range,
                )
            )
        if self.fire_sound_timer <= 0:
            self.play_sound("patch")
            self.fire_sound_timer = 0.08

    def effective_attack_cooldown(self) -> float:
        focus_bonus = 0.72 if self.focus_timer > 0 else 1.0
        haste_bonus = 0.62 if self.haste_timer > 0 else 1.0
        movement_bonus = 1.0 - self.momentum * 0.22
        return max(0.14, self.attack_cooldown * focus_bonus * haste_bonus * movement_bonus)

    def momentum_damage_multiplier(self) -> float:
        if self.momentum_tier == "Overdrive":
            return 1.12
        if self.momentum_tier == "Flow":
            return 1.05
        return 1.0

    def projectile_radius(self) -> int:
        if self.momentum_tier == "Overdrive":
            return 7
        if self.momentum_tier == "Flow":
            return 6
        return 5

    def projectile_color(self) -> tuple[int, int, int]:
        theme_color = self.current_patch_theme()["color"]
        if self.momentum_tier == "Overdrive":
            return self.mix_color(theme_color, GREEN, 0.72)
        if self.momentum_tier == "Flow":
            return self.mix_color(theme_color, ACCENT, 0.4)
        return theme_color

    def mix_color(
        self,
        base: tuple[int, int, int],
        accent: tuple[int, int, int],
        ratio: float,
    ) -> tuple[int, int, int]:
        ratio = max(0.0, min(1.0, ratio))
        return tuple(
            int(base[index] * (1.0 - ratio) + accent[index] * ratio) for index in range(3)
        )

    def update_projectiles(self, dt: float) -> None:
        next_projectiles = []
        spawned_projectiles = []
        for projectile in self.projectiles:
            projectile["x"] += projectile["vx"] * dt
            projectile["y"] += projectile["vy"] * dt
            if not (
                -40 <= projectile["x"] <= WIDTH + 40
                and -40 <= projectile["y"] <= HEIGHT + 40
            ):
                continue

            hit = False
            for enemy in self.enemies:
                if (
                    dist((projectile["x"], projectile["y"]), (enemy["x"], enemy["y"]))
                    <= projectile["radius"] + enemy["type"].radius
                ):
                    enemy["hp"] -= projectile["damage"]
                    self.trigger_screen_shake(0.05, 1.0)
                    self.spawn_floating_text(
                        enemy["x"],
                        enemy["y"] - 12,
                        str(int(projectile["damage"])),
                        ACCENT,
                    )
                    hit = True
                    if projectile["pierce"] > 0:
                        projectile["pierce"] -= 1
                        self.try_chain_projectile(projectile, enemy, spawned_projectiles)
                        hit = False
                    else:
                        self.try_chain_projectile(projectile, enemy, spawned_projectiles)
                        self.trigger_overclock_burst(projectile, enemy)
                        break
            if not hit:
                next_projectiles.append(projectile)
        self.projectiles = next_projectiles + spawned_projectiles

    def try_chain_projectile(
        self,
        projectile: ProjectileState,
        source_enemy: EnemyState,
        spawned_projectiles: list[ProjectileState],
    ) -> None:
        if projectile.get("chain", 0) <= 0:
            return
        target = self.find_chain_target(
            source_enemy,
            projectile.get("chain_range", self.chain_range),
        )
        if target is None:
            return
        remaining_chain = projectile["chain"] - 1
        chain_hits = projectile.get("chain_hits", 1) + 1
        self.max_chain_hits = max(self.max_chain_hits, chain_hits)
        angle = atan2(target["y"] - source_enemy["y"], target["x"] - source_enemy["x"])
        spawned_projectiles.append(
            make_projectile(
                source_enemy["x"],
                source_enemy["y"],
                cos(angle) * self.projectile_speed * 1.04,
                sin(angle) * self.projectile_speed * 1.04,
                projectile["damage"] * 0.82,
                max(4, projectile["radius"] - 1),
                PURPLE,
                0,
                "chain",
                max(0, remaining_chain),
                projectile.get("chain_range", self.chain_range),
                chain_hits,
            )
        )
        self.spawn_floating_text(source_enemy["x"], source_enemy["y"] - 26, "review", PURPLE)

    def find_chain_target(self, source_enemy: EnemyState, max_range: float) -> EnemyState | None:
        candidates = [
            enemy
            for enemy in self.enemies
            if enemy is not source_enemy
            and dist((source_enemy["x"], source_enemy["y"]), (enemy["x"], enemy["y"])) <= max_range
        ]
        if not candidates:
            return None
        return min(
            candidates,
            key=lambda enemy: dist((source_enemy["x"], source_enemy["y"]), (enemy["x"], enemy["y"])),
        )

    def trigger_overclock_burst(
        self,
        projectile: ProjectileState,
        source_enemy: EnemyState,
    ) -> None:
        if self.overclock_level <= 0 or self.momentum_tier != "Overdrive":
            return
        radius = 42 + self.overclock_level * 14
        damage = projectile["damage"] * (0.28 + self.overclock_level * 0.05)
        hit_count = 0
        for enemy in self.enemies:
            if enemy is source_enemy:
                continue
            if dist((source_enemy["x"], source_enemy["y"]), (enemy["x"], enemy["y"])) <= radius:
                enemy["hp"] -= damage
                hit_count += 1
        if hit_count:
            self.kill_flash = max(self.kill_flash, 0.12)
            self.trigger_screen_shake(0.06, 1.6)
            self.spawn_floating_text(source_enemy["x"] - 14, source_enemy["y"] - 34, "burst", ACCENT)

    def update_enemies(self, dt: float) -> None:
        alive = []
        for enemy in self.enemies:
            self.advance_enemy(enemy, dt)

            if (
                dist((self.player_x, self.player_y), (enemy["x"], enemy["y"]))
                <= self.player_radius + enemy["type"].radius
            ):
                if self.contact_timer <= 0 and self.grace_timer <= 0:
                    self.player_hp -= enemy.get("damage", enemy["type"].damage)
                    self.contact_timer = 0.25
                    self.grace_timer = 0.55
                    self.hit_flash = 0.42
                    self.play_sound("hit")
                    self.trigger_screen_shake(0.14, 4.0)
                    self.spawn_floating_text(
                        self.player_x,
                        self.player_y - 28,
                        f"-{int(enemy.get('damage', enemy['type'].damage))}",
                        RED,
                    )
                    self.trigger_failsafe()

            if enemy["hp"] <= 0:
                self.resolve_enemy(enemy)
                self.kill_flash = 0.18
            else:
                alive.append(enemy)

        self.enemies = alive

    def resolve_enemy(
        self,
        enemy: EnemyState,
        insight_multiplier: float = 1.0,
        allow_powerup_drop: bool = True,
        allow_split: bool = True,
    ) -> None:
        """Apply all rewards and side effects for a truly defeated enemy."""
        self.drop_enemy_insight(enemy, insight_multiplier)
        self.spawn_fix_text(enemy)
        if allow_powerup_drop:
            self.maybe_drop_powerup(enemy)
        self.track_enemy_resolution(enemy)
        if allow_split and enemy["type"].name == "Scope Creep" and enemy.get("split_depth", 0) > 0:
            self.spawn_scope_split(enemy)

    def enemy_insight_value(self, enemy: EnemyState) -> float:
        """Return the base insight reward for resolving each enemy type."""
        return insight_value_for_enemy(enemy["type"].name)

    def drop_enemy_insight(self, enemy: EnemyState, multiplier: float = 1.0) -> None:
        """Drop an insight shard at an enemy position."""
        self.xp_shards.append(
            {
                "x": enemy["x"],
                "y": enemy["y"],
                "value": self.enemy_insight_value(enemy) * multiplier,
            }
        )

    def trigger_failsafe(self) -> None:
        if self.failsafe_level <= 0 or self.failsafe_cooldown > 0:
            return
        threshold = self.player_max_hp * max(0.2, 0.38 - self.failsafe_level * 0.03)
        if self.player_hp > threshold:
            return

        self.failsafe_cooldown = max(15.0, 21.0 - self.failsafe_level * 2.0)
        self.grace_timer = max(self.grace_timer, 1.1)
        self.stats["failsafe_triggers"] += 1
        recovered = 12 + self.failsafe_level * 5
        self.player_hp = min(self.player_max_hp, self.player_hp + recovered)
        blast_radius = 120 + self.failsafe_level * 18
        blast_damage = 18 + self.failsafe_level * 8
        hit_count = 0
        for enemy in self.enemies:
            if dist((self.player_x, self.player_y), (enemy["x"], enemy["y"])) <= blast_radius:
                enemy["hp"] -= blast_damage
                hit_count += 1
        self.play_sound("crisis")
        self.trigger_screen_shake(0.16, 4.6)
        self.spawn_floating_text(self.player_x, self.player_y - 54, "Rollback Guard", BLUE)
        if hit_count:
            self.spawn_floating_text(
                self.player_x,
                self.player_y - 28,
                f"stabilized x{hit_count}",
                ACCENT,
            )

    def spawn_fix_text(self, enemy: EnemyState) -> None:
        self.spawn_floating_text(
            enemy["x"] - enemy["type"].radius,
            enemy["y"] - enemy["type"].radius - 10,
            fix_label_for_enemy(enemy["type"].name),
            XP_COLOR,
        )

    def track_enemy_resolution(self, enemy: EnemyState) -> None:
        stat_key = stat_key_for_enemy(enemy["type"].name)
        if stat_key is not None:
            self.stats[stat_key] += 1
        if enemy["type"].name == "Outage":
            self.unlock_achievement("first_outage")

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

    def advance_enemy(self, enemy: EnemyState, dt: float) -> None:
        enemy_type = enemy["type"]
        if enemy_type.name == "Outage":
            self.advance_outage(enemy, dt)
            return
        if enemy_type.name == "Meeting":
            target_x = self.player_x + self.player_dx * self.player_speed * 0.55
            target_y = self.player_y + self.player_dy * self.player_speed * 0.55
            angle = atan2(target_y - enemy["y"], target_x - enemy["x"])
            move_speed = enemy_type.speed * 0.92
            enemy["x"] += cos(angle) * move_speed * dt
            enemy["y"] += sin(angle) * move_speed * dt
            return

        if enemy_type.name == "Alert":
            enemy["dash_cooldown"] -= dt
            if enemy["dash_timer"] > 0:
                enemy["dash_timer"] -= dt
                enemy["x"] += enemy["dash_vx"] * dt
                enemy["y"] += enemy["dash_vy"] * dt
                return

            distance_to_player = dist((self.player_x, self.player_y), (enemy["x"], enemy["y"]))
            if enemy["dash_cooldown"] <= 0 and distance_to_player < 220:
                angle = atan2(self.player_y - enemy["y"], self.player_x - enemy["x"])
                enemy["dash_vx"] = cos(angle) * enemy_type.speed * 2.45
                enemy["dash_vy"] = sin(angle) * enemy_type.speed * 2.45
                enemy["dash_timer"] = 0.28
                enemy["dash_cooldown"] = 1.7 + random() * 0.8
                return

        angle = atan2(self.player_y - enemy["y"], self.player_x - enemy["x"])
        enemy["x"] += cos(angle) * enemy_type.speed * dt
        enemy["y"] += sin(angle) * enemy_type.speed * dt

    def advance_outage(self, enemy: EnemyState, dt: float) -> None:
        enemy_type = enemy["type"]
        hp_ratio = enemy["hp"] / max(1.0, enemy.get("max_hp", enemy["hp"]))
        if hp_ratio <= 0.5 and not enemy["rage"]:
            enemy["rage"] = True
            enemy["pulse_timer"] = min(enemy["pulse_timer"], 1.1)
            enemy["summon_timer"] = min(enemy["summon_timer"], 2.3)
            self.spawn_floating_text(enemy["x"] - 22, enemy["y"] - 48, "Outage escalates", RED)

        distance_to_player = dist((self.player_x, self.player_y), (enemy["x"], enemy["y"]))
        preferred_distance = 170
        angle = atan2(self.player_y - enemy["y"], self.player_x - enemy["x"])
        speed = enemy_type.speed * (1.18 if enemy["rage"] else 1.0)
        move_direction = 1.0 if distance_to_player > preferred_distance else -0.72
        enemy["x"] += cos(angle) * speed * move_direction * dt
        enemy["y"] += sin(angle) * speed * move_direction * dt

        enemy["pulse_timer"] -= dt
        if enemy["pulse_timer"] <= 0:
            self.emit_outage_wave(enemy)
            enemy["pulse_timer"] = 1.65 if enemy["rage"] else 2.55

        enemy["summon_timer"] -= dt
        if enemy["summon_timer"] <= 0:
            self.summon_outage_support(enemy)
            enemy["summon_timer"] = 3.1 if enemy["rage"] else 5.0

    def emit_outage_wave(self, enemy: EnemyState) -> None:
        self.trigger_screen_shake(0.1, 2.6)
        self.spawn_floating_text(enemy["x"] - 18, enemy["y"] - 52, "Incident wave", OUTAGE_COLOR)
        for index in range(6):
            angle = index * (2 * pi / 6)
            radius = 54.0
            x = max(radius, min(WIDTH - radius, enemy["x"] + cos(angle) * 92))
            y = max(radius, min(HEIGHT - radius, enemy["y"] + sin(angle) * 92))
            self.hazards.append(
                make_hazard(
                    x,
                    y,
                    radius,
                    0.85,
                    1.2,
                    12.0 if not enemy["rage"] else 16.0,
                )
            )

    def summon_outage_support(self, enemy: EnemyState) -> None:
        alert = next(enemy_type for enemy_type in ENEMY_TYPES if enemy_type.name == "Alert")
        bug = next(enemy_type for enemy_type in ENEMY_TYPES if enemy_type.name == "Bug")
        self.spawn_floating_text(enemy["x"] - 26, enemy["y"] - 28, "Escalation", ACCENT)
        self.add_enemy(alert, elite=False, near_player=True)
        self.add_enemy(choice([alert, bug]), elite=False, near_player=True)

    def projectile_damage_multiplier(self) -> float:
        if self.projectile_count <= 1:
            return 1.0
        return max(0.45, 1.0 - (self.projectile_count - 1) * 0.18)

    def spawn_scope_split(self, enemy: EnemyState) -> None:
        for offset in (-16, 16):
            self.enemies.append(
                make_enemy_state(
                    EnemyType("Bugling", 12, 122, 16, 8, (218, 170, 255), 0.0),
                    enemy["x"] + offset,
                    enemy["y"] - offset * 0.25,
                    (
                        16 + self.time_survived * 0.18
                    ) * self.current_difficulty().enemy_hp_mult,
                    8 * self.current_difficulty().enemy_damage_mult,
                    99.0,
                    0,
                    False,
                )
            )

    def update_xp(self, dt: float) -> None:
        remaining = []
        for shard in self.xp_shards:
            distance = dist((self.player_x, self.player_y), (shard["x"], shard["y"]))
            pickup_radius = self.effective_pickup_radius()
            if distance <= pickup_radius and distance > 1:
                angle = atan2(self.player_y - shard["y"], self.player_x - shard["x"])
                speed = 260 + (pickup_radius - min(distance, pickup_radius)) * 5
                shard["x"] += cos(angle) * speed * dt
                shard["y"] += sin(angle) * speed * dt

            if (
                dist((self.player_x, self.player_y), (shard["x"], shard["y"]))
                <= self.player_radius + 8
            ):
                gained = shard["value"] * self.xp_multiplier()
                self.xp += gained
                self.stats["insight"] += gained
                if shard["value"] >= 8:
                    self.spawn_floating_text(
                        shard["x"],
                        shard["y"] - 10,
                        f"+{int(gained)} insight",
                        XP_COLOR,
                    )
            else:
                remaining.append(shard)
        self.xp_shards = remaining

    def xp_multiplier(self) -> float:
        focus_bonus = 0.18 if self.focus_timer > 0 else 0.0
        return 1.0 + self.momentum * 0.45 + focus_bonus

    def run_scaling_bonus(self) -> float:
        """Scale some rewards gently so late-run tools keep pace with pressure."""
        return 1.0 + min(0.45, max(0, self.level - 1) * 0.035)

    def effective_pickup_radius(self) -> float:
        focus_bonus = 18.0 if self.focus_timer > 0 else 0.0
        return self.pickup_radius * (1.0 + self.momentum * 0.35) + focus_bonus

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
        if kind == "heal":
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
        elif kind == "bomb":
            bomb_damage = 92.0 * scaling
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
                        self.spawn_floating_text(enemy["x"] - 28, enemy["y"] - 52, "Outage damaged", ACCENT)
            self.enemies = survivors
            self.kill_flash = 0.6
            self.play_sound("crisis")
            self.trigger_screen_shake(0.2, 5.5)
            self.spawn_floating_text(
                self.player_x,
                self.player_y - 52,
                f"Refactor x{defeated}",
                ACCENT,
            )
        elif kind == "haste":
            self.haste_timer = min(12.0, 7.0 * scaling)
            self.play_sound("pickup")
            self.spawn_floating_text(self.player_x, self.player_y - 44, "CI Boost", BLUE)

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

    def check_level_up(self) -> None:
        """Enter the upgrade choice state when enough insight has been collected."""
        if self.xp < self.xp_to_level:
            return

        self.xp -= self.xp_to_level
        self.level += 1
        self.xp_to_level = self.xp_required_for_level(self.level)
        self.state = "level_up"
        self.level_choices = self.pick_level_choices()
        self.level_flash = 0.4
        self.spawn_floating_text(self.player_x, self.player_y - 54, f"Level {self.level}", ACCENT)

    def xp_required_for_level(self, level: int) -> float:
        """Return insight needed to advance from current level to the next level.

        The curve is intentionally steeper than enemy insight growth so individual
        shards become a smaller percentage of the bar at higher levels.
        """
        level_index = max(1, level)
        return float(round(70 + (level_index - 1) * 30 + (level_index - 1) ** 2 * 7))

    def pick_level_choices(self) -> list[Upgrade]:
        """Pick three distinct upgrade choices with light contextual weighting."""
        weighted: list[Upgrade] = []
        for upgrade in UPGRADES:
            weight = 1
            if upgrade.key in {"damage", "projectiles", "speed"} and self.level <= 3:
                weight += 2
            if upgrade.key == "projectiles" and self.projectile_count >= 5:
                weight = 1
            if upgrade.key == "shield" and self.player_hp < self.player_max_hp * 0.45:
                weight += 2
            if upgrade.key == "pulse" and self.level >= 3:
                weight += 1
            if upgrade.key == "recovery" and self.level >= 4:
                weight += 1
            if upgrade.key == "pierce" and self.level >= 4:
                weight += 1
            if upgrade.key == "chain" and self.level >= 3:
                weight += 2
            if upgrade.key == "drone" and self.level >= 4:
                weight += 2
            if upgrade.key == "failsafe" and self.player_hp < self.player_max_hp * 0.55:
                weight += 2
            if upgrade.key == "overclock" and self.level >= 5:
                weight += 2
            weighted.extend([upgrade] * weight)

        choices: list[Upgrade] = []
        pool = weighted[:]
        while pool and len(choices) < 3:
            candidate = choice(pool)
            if candidate not in choices:
                choices.append(candidate)
            pool = [item for item in pool if item.key != candidate.key]

        while len(choices) < 3:
            fallback = choice(UPGRADES)
            if fallback not in choices:
                choices.append(fallback)

        return choices

    def current_run_evaluation(self) -> tuple[str, str, list[str]]:
        tags: list[str] = []
        if self.max_momentum >= 0.8:
            tags.append("High Momentum")
        if self.stats["deploys"] >= 3:
            tags.append("Deploy Focus")
        if self.stats["outages_resolved"] >= 1:
            tags.append("Boss Priority")
        if self.stats["failsafe_triggers"] >= 1:
            tags.append("Low HP Survivor")
        if self.drone_count >= 2:
            tags.append("Support Build")
        elif self.chain_count >= 2:
            tags.append("Chain Build")
        elif self.pulse_unlocked or self.overclock_level > 0:
            tags.append("Wave Cleaner")

        if self.stats["outages_resolved"] >= 2:
            return (
                "Outage Hunter",
                "You treated production outages as the main objective and kept the run under control.",
                tags[:2] or ["Boss Priority"],
            )
        if self.stats["deploys"] >= 4:
            return (
                "Deploy Specialist",
                "You kept rotating into risky deploy windows and turned map pressure into growth.",
                tags[:2] or ["Deploy Focus"],
            )
        if self.drone_count >= 2:
            return (
                "Pair Programming Lead",
                "This run leaned on support patches and felt more like coordinated repair work.",
                tags[:2] or ["Support Build"],
            )
        if self.chain_count >= 2 and (self.pierce > 0 or self.overclock_level > 0):
            return (
                "Code Review Machine",
                "One patch kept turning into more fixes as the build spread through clustered problems.",
                tags[:2] or ["Chain Build"],
            )
        if self.stats["failsafe_triggers"] >= 2 or (
            self.stats["failsafe_triggers"] >= 1 and self.time_survived >= 240
        ):
            return (
                "Last-Minute Hero",
                "This run survived repeated emergencies and kept shipping patches after near collapses.",
                tags[:2] or ["Low HP Survivor"],
            )
        if self.max_momentum >= 0.85 and self.stats["deploys"] >= 2:
            return (
                "Patch Sprinter",
                "You kept the run moving, stayed in flow, and converted mobility into steady growth.",
                tags[:2] or ["High Momentum"],
            )
        if self.run_resolved_count() >= 90 and (self.pulse_unlocked or self.overclock_level > 0):
            return (
                "Incident Cleaner",
                "The build focused on cleaning waves quickly instead of only escaping them.",
                tags[:2] or ["Wave Cleaner"],
            )
        return (
            "Steady Maintainer",
            "You kept the system running without overcommitting to a single high-risk route.",
            tags[:2] or ["Balanced Run"],
        )

    def run_resolved_count(self) -> int:
        """Return all enemy-pressure resolved during the current run."""
        return (
            self.stats["bugs_fixed"]
            + self.stats["meetings_dodged"]
            + self.stats["alerts_silenced"]
            + self.stats["scope_trimmed"]
            + self.stats["outages_resolved"]
        )

    def total_resolved_count(self) -> int:
        """Return all cumulative enemy-pressure resolved across saved runs."""
        totals = self.progression["totals"]
        return (
            totals["bugs_fixed"]
            + totals["meetings_dodged"]
            + totals["alerts_silenced"]
            + totals["scope_trimmed"]
            + totals["outages_resolved"]
        )

    def unlock_achievement(self, key: str) -> None:
        entry = self.progression["achievements"].get(key)
        if entry is None or entry.get("unlocked"):
            return
        entry["unlocked"] = True
        self.new_achievements.append(key)
        self.spawn_floating_text(
            self.player_x - 36,
            self.player_y - 82,
            ACHIEVEMENT_DEFS.get(key, key),
            ACCENT,
        )

    def finalize_run_progression(self) -> None:
        totals = self.progression["totals"]
        totals["bugs_fixed"] += self.stats["bugs_fixed"]
        totals["meetings_dodged"] += self.stats["meetings_dodged"]
        totals["alerts_silenced"] += self.stats["alerts_silenced"]
        totals["scope_trimmed"] += self.stats["scope_trimmed"]
        totals["outages_resolved"] += self.stats["outages_resolved"]
        totals["deploys"] += self.stats["deploys"]
        totals["runs_played"] += 1
        totals["best_time"] = max(float(totals["best_time"]), self.time_survived, self.best_time)

        self.apply_run_based_achievement_checks(include_cumulative=True)

        save_progression(self.best_time, self.progression)

    def apply_run_based_achievement_checks(self, include_cumulative: bool) -> None:
        if self.selected_difficulty == "crunch" and self.time_survived >= 600:
            self.unlock_achievement("crunch_survivor")
        if self.stats["deploys"] >= 5:
            self.unlock_achievement("deploy_addict")
        if self.drone_count >= 2:
            self.unlock_achievement("pair_flow")
        if self.max_chain_hits >= 3:
            self.unlock_achievement("review_cascade")
        if include_cumulative and self.progression["totals"]["bugs_fixed"] >= 500:
            self.unlock_achievement("bug_tracker")

    def persist_progression_snapshot(self) -> None:
        self.best_time = max(self.best_time, self.time_survived)
        self.progression["totals"]["best_time"] = max(
            float(self.progression["totals"]["best_time"]),
            self.best_time,
        )
        self.apply_run_based_achievement_checks(include_cumulative=False)
        save_progression(self.best_time, self.progression)

    def achievement_progress_text(self, key: str) -> str:
        totals = self.progression["totals"]
        if key == "crunch_survivor":
            if self.progression["achievements"][key].get("unlocked"):
                return "Done"
            if self.selected_difficulty == "crunch":
                return f"{min(self.time_survived, 600):0.0f}/600s"
            return "0/600s"
        if key == "deploy_addict":
            if self.progression["achievements"][key].get("unlocked"):
                return "Done"
            return f"{min(self.stats['deploys'], 5)}/5 in one run"
        if key == "pair_flow":
            if self.progression["achievements"][key].get("unlocked"):
                return "Done"
            return f"{min(self.drone_count, 2)}/2 pairs"
        if key == "review_cascade":
            if self.progression["achievements"][key].get("unlocked"):
                return "Done"
            return f"{min(self.max_chain_hits, 3)}/3 hits"
        if key == "bug_tracker":
            if self.progression["achievements"][key].get("unlocked"):
                return "Done"
            return f"{min(totals['bugs_fixed'], 500)}/500"
        return "Done" if self.progression["achievements"][key].get("unlocked") else "Not yet"

    def achievement_progress_ratio(self, key: str) -> float:
        totals = self.progression["totals"]
        if self.progression["achievements"][key].get("unlocked"):
            return 1.0
        if key == "crunch_survivor":
            if self.selected_difficulty != "crunch":
                return 0.0
            return min(1.0, self.time_survived / 600.0)
        if key == "deploy_addict":
            return min(1.0, self.stats["deploys"] / 5.0)
        if key == "pair_flow":
            return min(1.0, self.drone_count / 2.0)
        if key == "review_cascade":
            return min(1.0, self.max_chain_hits / 3.0)
        if key == "bug_tracker":
            return min(1.0, totals["bugs_fixed"] / 500.0)
        return 0.0

    def achievement_is_recent(self, key: str) -> bool:
        return key in self.new_achievements

    def next_achievement_hint(self) -> tuple[str, str] | None:
        locked = []
        for _, _, _, rows in ACHIEVEMENT_GROUPS:
            for key, description in rows:
                if not self.progression["achievements"][key].get("unlocked"):
                    locked.append((self.achievement_progress_ratio(key), key, description))
        if not locked:
            return None
        locked.sort(reverse=True)
        _, key, description = locked[0]
        return (ACHIEVEMENT_DEFS[key], description)

    def draw(self) -> None:
        shake_x = 0
        shake_y = 0
        if self.state != "game_over" and self.shake_timer > 0 and self.shake_strength > 0:
            shake_x = int((random() - 0.5) * 2 * self.shake_strength)
            shake_y = int((random() - 0.5) * 2 * self.shake_strength)

        self.screen.fill(BG)
        self.draw_grid()
        self.draw_objective()
        self.draw_hazards()

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

        for shard in self.xp_shards:
            pygame.draw.circle(self.screen, XP_COLOR, (int(shard["x"]), int(shard["y"])), 6)

        self.draw_powerups()
        self.draw_drones()

        for projectile in self.projectiles:
            pygame.draw.circle(
                self.screen,
                projectile.get("color", PROJECTILE_COLOR),
                (int(projectile["x"]), int(projectile["y"])),
                int(projectile["radius"]),
            )

        for enemy in self.enemies:
            pygame.draw.circle(
                self.screen,
                enemy["type"].color,
                (int(enemy["x"]), int(enemy["y"])),
                int(enemy["type"].radius),
            )
            if enemy.get("elite"):
                pygame.draw.circle(
                    self.screen,
                    ACCENT,
                    (int(enemy["x"]), int(enemy["y"])),
                    int(enemy["type"].radius + 6),
                    2,
                )
            if enemy["type"].name == "Meeting":
                pygame.draw.circle(
                    self.screen,
                    (230, 240, 255),
                    (int(enemy["x"]), int(enemy["y"])),
                    6,
                )
            elif enemy["type"].name == "Alert":
                pygame.draw.circle(
                    self.screen,
                    (255, 233, 205),
                    (int(enemy["x"]), int(enemy["y"])),
                    4,
                )
                if enemy.get("dash_timer", 0) > 0:
                    pygame.draw.circle(
                        self.screen,
                        (255, 255, 255),
                        (int(enemy["x"]), int(enemy["y"])),
                        int(enemy["type"].radius + 4),
                        2,
                    )
            elif enemy["type"].name == "Scope Creep":
                pygame.draw.circle(
                    self.screen,
                    (245, 228, 255),
                    (int(enemy["x"]), int(enemy["y"])),
                    5,
                )
            elif enemy["type"].name == "Outage":
                pygame.draw.circle(
                    self.screen,
                    PANEL,
                    (int(enemy["x"]), int(enemy["y"])),
                    12,
                )
                pygame.draw.circle(
                    self.screen,
                    TEXT,
                    (int(enemy["x"]), int(enemy["y"])),
                    6,
                    2,
                )
                if enemy.get("rage"):
                    pygame.draw.circle(
                        self.screen,
                        RED,
                        (int(enemy["x"]), int(enemy["y"])),
                        int(enemy["type"].radius + 10),
                        2,
                    )
            elif enemy["type"].name == "Bugling":
                pygame.draw.circle(
                    self.screen,
                    (255, 248, 255),
                    (int(enemy["x"]), int(enemy["y"])),
                    3,
                )

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

        if self.state not in {"title", "achievements", "game_over"}:
            self.draw_hud()
            self.draw_floating_texts()

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

        shadow = pygame.Rect(x - 18, y + 24, 36, 9)
        pygame.draw.ellipse(self.screen, (8, 10, 14), shadow)

        left_leg = pygame.Rect(x - 11 + lean_x, y + 14, 8, 18)
        right_leg = pygame.Rect(x + 3 + lean_x, y + 14, 8, 18)
        pygame.draw.rect(self.screen, (63, 92, 145), left_leg, border_radius=4)
        pygame.draw.rect(self.screen, (63, 92, 145), right_leg, border_radius=4)

        body = pygame.Rect(x - 15 + lean_x, y - 4 + lean_y, 30, 27)
        pygame.draw.rect(self.screen, skin["body"], body, border_radius=9)
        pygame.draw.rect(self.screen, skin["outline"], body, 2, border_radius=9)

        pygame.draw.line(self.screen, skin["arms"], (x - 13, y + 3), (x - 24, y + 12), 4)
        pygame.draw.line(self.screen, skin["arms"], (x + 13, y + 3), (x + 24, y + 12), 4)

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
        panel = pygame.Rect(18, 18, 372, 144)
        draw_translucent_rect(self.screen, panel, PANEL, 150, 16)
        pygame.draw.rect(self.screen, GRID, panel, 1, border_radius=16)

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
        if self.objective is not None:
            objective_y = 82 if outage is not None else 58
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

        start = min(self.help_scroll, max(0, len(lines) - 16))
        self.help_scroll = start
        visible = lines[start : start + 16]
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

        ratio = start / max(1, len(lines) - 16)
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
        rect = pygame.Rect(x, y, 440, 142)
        pygame.draw.rect(self.screen, BG, rect, border_radius=16)
        pygame.draw.rect(self.screen, group_color, (x, y, rect.width, 5), border_radius=16)
        pygame.draw.rect(self.screen, GRID, rect, 1, border_radius=16)
        pygame.draw.circle(self.screen, group_color, (x + 22, y + 28), 8)
        self.blit(self.font, group_name, group_color, x + 40, y + 14)
        self.blit(self.small_font, f"{unlocked_in_group}/{len(rows)}", MUTED, x + 374, y + 20)
        self.blit(self.small_font, group_summary, MUTED, x + 20, y + 48)

        for row_index, (key, _) in enumerate(rows):
            row_y = y + 74 + row_index * 22
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
        summary_rect = pygame.Rect(250, 204, 780, 154)
        stats_rect = pygame.Rect(250, 376, 780, 112)
        menu_rect = pygame.Rect(250, 506, 780, 94)
        for rect in (summary_rect, stats_rect, menu_rect):
            pygame.draw.rect(self.screen, BG, rect, border_radius=18)
            pygame.draw.rect(self.screen, GRID, rect, 1, border_radius=18)

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

def main() -> int:
    try:
        game = Game()
    except pygame.error as exc:
        print(f"Failed to start Deadline Survivors: {exc}", file=sys.stderr)
        return 1

    if "--smoke-test" in sys.argv:
        pygame.quit()
        return 0

    return game.run()
