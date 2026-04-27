"""Player options and local data reset helpers."""

from __future__ import annotations

from ..storage import reset_save_data, save_progression


class OptionsSystemMixin:
    def setting_enabled(self, key: str) -> bool:
        return bool(self.progression.get("settings", {}).get(key, True))

    def set_setting(self, key: str, enabled: bool) -> None:
        self.progression.setdefault("settings", {})[key] = enabled
        save_progression(self.best_time, self.progression)

    def toggle_sound(self) -> None:
        self.set_setting("sound_enabled", not self.setting_enabled("sound_enabled"))

    def toggle_floating_text(self) -> None:
        self.set_setting(
            "floating_text_enabled",
            not self.setting_enabled("floating_text_enabled"),
        )

    def clear_local_data(self) -> None:
        """Reset save-backed progression and in-memory cosmetic selections."""
        self.best_time = 0.0
        self.progression = reset_save_data()
        self.selected_skin = self.progression["selected_skin"]
        self.selected_badge = self.progression["selected_badge"]
        self.selected_patch_theme = self.progression["selected_patch_theme"]
        self.selected_difficulty = "normal"
        self.menu_return_state = "title"
        self.title_menu_index = 0
        self.game_over_menu_index = 0
        self.reset()
        self.state = "options"
