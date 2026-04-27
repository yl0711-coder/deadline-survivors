"""Run-local state initialization for a new game attempt."""

from __future__ import annotations

from ..constants import HEIGHT, WIDTH
from ..models import (
    EnemyState,
    FloatingTextState,
    HazardState,
    InsightShardState,
    ObjectiveState,
    PowerupState,
    ProjectileState,
    Upgrade,
)


class RunStateMixin:
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
