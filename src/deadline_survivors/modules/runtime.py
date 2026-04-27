from __future__ import annotations

import sys

import pygame

from ..audio import AudioPlayer
from ..content import (
    DIFFICULTIES,
    PHASES,
)
from ..constants import FPS, HEIGHT, TITLE, WIDTH
from ..models import Difficulty, Phase
from ..storage import load_best_time, load_progression, save_best_time
from . import input as input_module
from .combat_system import CombatMixin
from .director_system import DirectorMixin
from .player_system import PlayerSystemMixin
from .progression import ProgressionMixin
from .renderer import RendererMixin
from .run_state import RunStateMixin


def create_font(size: int, *, bold: bool = False) -> pygame.font.Font:
    """Create a bundled pygame font without querying platform font registries."""
    font = pygame.font.Font(None, size)
    font.set_bold(bold)
    return font


class Game(
    RendererMixin,
    ProgressionMixin,
    CombatMixin,
    DirectorMixin,
    PlayerSystemMixin,
    RunStateMixin,
):
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
        input_module.handle_progress_overlay_input(self, key)

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
