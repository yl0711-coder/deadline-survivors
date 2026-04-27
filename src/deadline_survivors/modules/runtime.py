from __future__ import annotations

from math import atan2, cos, dist, hypot, pi, sin
from random import choice, random
import sys

import pygame

from ..audio import AudioPlayer
from ..combat import fix_label_for_enemy, insight_value_for_enemy, stat_key_for_enemy
from ..content import (
    DIFFICULTIES,
    ENEMY_TYPES,
    OUTAGE_BOSS,
    PHASES,
)
from ..encounters import enemy_spawn_pool
from ..constants import (
    ACCENT,
    BLUE,
    FPS,
    GREEN,
    HEIGHT,
    OUTAGE_COLOR,
    PURPLE,
    RED,
    TITLE,
    WIDTH,
    XP_COLOR,
)
from ..models import (
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
from ..state_factory import make_enemy_state, make_hazard, make_outage_state, make_projectile
from ..storage import load_best_time, load_progression, save_best_time
from . import input as input_module
from .progression import ProgressionMixin
from .renderer import RendererMixin


def create_font(size: int, *, bold: bool = False) -> pygame.font.Font:
    """Create a bundled pygame font without querying platform font registries."""
    font = pygame.font.Font(None, size)
    font.set_bold(bold)
    return font


class Game(RendererMixin, ProgressionMixin):
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
        self.reset_menu_state()
        self.reset_run_progress_state()
        self.reset_player_state()
        self.reset_combat_state()
        self.reset_director_state()
        self.reset_build_state()
        self.reset_feedback_state()
        self.reset_run_stats()
        self.reset_runtime_collections()

    def reset_menu_state(self) -> None:
        self.state = "title"
        self.menu_return_state = "title"
        self.help_scroll = 0
        self.game_over_menu_index = 0

    def reset_run_progress_state(self) -> None:
        self.time_survived = 0.0
        self.level = 1
        self.xp = 0.0
        self.xp_to_level = self.xp_required_for_level(self.level)

    def reset_player_state(self) -> None:
        self.player_x = WIDTH / 2
        self.player_y = HEIGHT / 2
        self.player_dx = 0.0
        self.player_dy = 0.0
        self.player_radius = 18
        self.player_speed = 265.0
        self.player_hp = 100.0
        self.player_max_hp = 100.0

    def reset_combat_state(self) -> None:
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

    def reset_director_state(self) -> None:
        self.crisis_timer = 24.0
        self.boss_timer = 52.0
        self.crisis_name = ""
        self.crisis_banner_timer = 0.0
        self.hazard_timer = 12.0
        self.objective_timer = 14.0
        self.objective: ObjectiveState | None = None
        self.objective_successes = 0

    def reset_build_state(self) -> None:
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

    def reset_feedback_state(self) -> None:
        self.shake_timer = 0.0
        self.shake_strength = 0.0
        self.hit_flash = 0.0
        self.level_flash = 0.0
        self.kill_flash = 0.0
        self.death_burst_timer = 0.0
        self.death_burst_x = self.player_x
        self.death_burst_y = self.player_y

    def reset_run_stats(self) -> None:
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

    def reset_runtime_collections(self) -> None:
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

    def play_sound(self, key: str) -> None:
        self.audio.play(key)

    def trigger_screen_shake(self, duration: float, strength: float) -> None:
        self.shake_timer = max(self.shake_timer, duration)
        self.shake_strength = max(self.shake_strength, strength)

    def choose_upgrade(self, key: str) -> None:
        """Apply a run-long level-up upgrade."""
        scaling = self.run_scaling_bonus()
        handlers = {
            "damage": self.apply_damage_upgrade,
            "speed": self.apply_speed_upgrade,
            "projectiles": self.apply_projectiles_upgrade,
            "magnet": self.apply_magnet_upgrade,
            "shield": self.apply_shield_upgrade,
            "pierce": self.apply_pierce_upgrade,
            "pulse": self.apply_pulse_upgrade,
            "recovery": self.apply_recovery_upgrade,
            "chain": self.apply_chain_upgrade,
            "drone": self.apply_drone_upgrade,
            "failsafe": self.apply_failsafe_upgrade,
            "overclock": self.apply_overclock_upgrade,
        }
        handler = handlers.get(key)
        if handler:
            handler(scaling)
        self.play_sound("level")

    def apply_damage_upgrade(self, scaling: float) -> None:
        gain = int(8 * scaling)
        self.projectile_damage += gain
        self.spawn_floating_text(self.player_x, self.player_y - 44, f"+{gain} damage", ACCENT)

    def apply_speed_upgrade(self, scaling: float) -> None:
        del scaling
        self.player_speed *= 1.12 + min(0.07, (self.level - 1) * 0.006)
        self.spawn_floating_text(self.player_x, self.player_y - 44, "Move up", BLUE)

    def apply_projectiles_upgrade(self, scaling: float) -> None:
        del scaling
        if self.projectile_count < 5:
            self.projectile_count += 1
            self.spawn_floating_text(self.player_x, self.player_y - 44, "+1 patch", PURPLE)
            return
        self.attack_cooldown *= 0.94
        self.projectile_damage += 2
        self.spawn_floating_text(self.player_x, self.player_y - 44, "Multicast tuned", PURPLE)

    def apply_magnet_upgrade(self, scaling: float) -> None:
        self.pickup_radius += int(26 * scaling)
        self.spawn_floating_text(self.player_x, self.player_y - 44, "Radar up", XP_COLOR)

    def apply_shield_upgrade(self, scaling: float) -> None:
        max_hp_gain = int(24 * scaling)
        heal_gain = int(14 * scaling)
        self.player_max_hp += max_hp_gain
        self.player_hp = min(self.player_max_hp, self.player_hp + heal_gain)
        self.spawn_floating_text(self.player_x, self.player_y - 44, "Shield up", BLUE)

    def apply_pierce_upgrade(self, scaling: float) -> None:
        del scaling
        self.pierce += 1
        self.spawn_floating_text(self.player_x, self.player_y - 44, "Pierce +1", PURPLE)

    def apply_pulse_upgrade(self, scaling: float) -> None:
        self.pulse_unlocked = True
        self.pulse_timer = min(self.pulse_timer, 1.0)
        self.pulse_radius += int(22 * scaling)
        self.pulse_damage += int(8 * scaling)
        self.spawn_floating_text(self.player_x, self.player_y - 44, "Pulse online", PURPLE)

    def apply_recovery_upgrade(self, scaling: float) -> None:
        del scaling
        self.regen_interval = (
            6.0 if self.regen_interval == 0 else max(2.7, self.regen_interval * 0.82)
        )
        self.regen_timer = self.regen_interval
        self.spawn_floating_text(self.player_x, self.player_y - 44, "Recovery up", BLUE)

    def apply_chain_upgrade(self, scaling: float) -> None:
        del scaling
        self.chain_count += 1
        self.chain_range = 120 + self.chain_count * 20
        self.spawn_floating_text(self.player_x, self.player_y - 44, "Code review", PURPLE)

    def apply_drone_upgrade(self, scaling: float) -> None:
        del scaling
        self.drone_count += 1
        self.drone_cooldown = max(0.34, self.drone_cooldown * 0.86)
        self.drone_timer = min(self.drone_timer, 0.35)
        self.spawn_floating_text(self.player_x, self.player_y - 44, "Pair online", GREEN)

    def apply_failsafe_upgrade(self, scaling: float) -> None:
        del scaling
        self.failsafe_level += 1
        self.failsafe_cooldown = min(self.failsafe_cooldown, 3.0)
        self.spawn_floating_text(self.player_x, self.player_y - 44, "Guard armed", BLUE)

    def apply_overclock_upgrade(self, scaling: float) -> None:
        del scaling
        self.overclock_level += 1
        self.spawn_floating_text(self.player_x, self.player_y - 44, "Build overclocked", ACCENT)

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
        return input_module.handle_keydown(self, key)

    def handle_achievements_input(self, key: int) -> None:
        input_module.handle_achievements_input(self, key)

    def handle_info_input(self, key: int) -> None:
        input_module.handle_info_input(self, key)

    def handle_title_input(self, key: int) -> bool:
        return input_module.handle_title_input(self, key)

    def handle_shared_menu_input(self, key: int) -> bool:
        return input_module.handle_shared_menu_input(self, key)

    def handle_game_over_input(self, key: int) -> bool:
        return input_module.handle_game_over_input(self, key)

    def handle_level_up_input(self, key: int) -> None:
        input_module.handle_level_up_input(self, key)

    def pick_choice(self, index: int) -> None:
        input_module.pick_choice(self, index)

    def activate_title_menu_item(self) -> None:
        """Run the currently highlighted title-menu action."""
        input_module.activate_title_menu_item(self)

    def activate_game_over_menu_item(self) -> None:
        """Run the currently highlighted game-over action."""
        input_module.activate_game_over_menu_item(self)

    def update(self, dt: float) -> None:
        """Advance one gameplay frame while the run is active."""
        self.advance_frame_timers(dt)
        self.update_player_systems(dt)
        self.update_directors(dt)
        self.update_combat_systems(dt)
        self.finish_run_if_player_is_defeated()

    def advance_frame_timers(self, dt: float) -> None:
        """Advance short-lived gameplay timers for one active frame."""
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

    def update_player_systems(self, dt: float) -> None:
        """Update movement, build effects, and run objectives."""
        self.move_player(dt)
        self.update_momentum(dt)
        self.update_regen(dt)
        self.update_drone(dt)
        self.update_objective(dt)

    def update_directors(self, dt: float) -> None:
        """Update systems that add external pressure to the run."""
        self.update_crisis_director(dt)
        self.update_boss_director(dt)
        self.update_hazards(dt)
        self.spawn_enemy_if_ready()

    def spawn_enemy_if_ready(self) -> None:
        """Spawn the next enemy wave when the spawn timer expires."""
        if self.spawn_timer <= 0:
            self.spawn_enemy()
            phase = self.current_phase()
            spawn_base = phase.spawn_base * self.current_difficulty().spawn_interval_mult
            self.spawn_timer = max(0.18, spawn_base - min(self.time_survived / 72, 0.18))

    def update_combat_systems(self, dt: float) -> None:
        """Update attacks, collisions, pickups, and floating combat feedback."""
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

    def finish_run_if_player_is_defeated(self) -> None:
        """Finalize a run exactly once when player health reaches zero."""
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
        elite = self.should_spawn_elite(elite)
        x, y = self.enemy_spawn_position(near_player)
        hp = self.enemy_spawn_hp(enemy_type, elite)
        damage = enemy_type.damage * self.current_difficulty().enemy_damage_mult
        self.enemies.append(
            make_enemy_state(
                enemy_type,
                x,
                y,
                hp,
                damage,
                1.4 + random() * 0.9,
                self.enemy_split_depth(enemy_type),
                elite,
            )
        )

    def should_spawn_elite(self, elite: bool | None) -> bool:
        if elite is None:
            elite_chance = 0.0
            if self.level >= 8:
                elite_chance += 0.03
            if self.level >= 12:
                elite_chance += 0.05
            if self.current_phase().name == "Deadline Crunch":
                elite_chance += 0.04
            return random() < elite_chance
        return elite

    def enemy_spawn_position(self, near_player: bool) -> tuple[float, float]:
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
        return x, y

    def enemy_spawn_hp(self, enemy_type: EnemyType, elite: bool) -> float:
        level_pressure = max(0, self.level - 7) * 2.15
        elite_multiplier = 2.2 if elite else 1.0
        difficulty = self.current_difficulty()
        return (
            enemy_type.hp
            + level_pressure
            + self.time_survived * (0.35 + self.current_phase().pressure * 0.22)
        ) * difficulty.enemy_hp_mult * elite_multiplier

    def enemy_split_depth(self, enemy_type: EnemyType) -> int:
        return 1 if enemy_type.name == "Scope Creep" else 0

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
        handlers = {
            "heal": self.apply_heal_powerup,
            "bomb": self.apply_bomb_powerup,
            "haste": self.apply_haste_powerup,
        }
        handler = handlers.get(kind)
        if handler:
            handler(scaling)

    def apply_heal_powerup(self, scaling: float) -> None:
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

    def apply_bomb_powerup(self, scaling: float) -> None:
        defeated = self.damage_enemies_with_bomb(92.0 * scaling, scaling)
        self.kill_flash = 0.6
        self.play_sound("crisis")
        self.trigger_screen_shake(0.2, 5.5)
        self.spawn_floating_text(
            self.player_x,
            self.player_y - 52,
            f"Refactor x{defeated}",
            ACCENT,
        )

    def damage_enemies_with_bomb(self, bomb_damage: float, scaling: float) -> int:
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
                    self.spawn_floating_text(
                        enemy["x"] - 28,
                        enemy["y"] - 52,
                        "Outage damaged",
                        ACCENT,
                    )
        self.enemies = survivors
        return defeated

    def apply_haste_powerup(self, scaling: float) -> None:
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
