import os
from typing import Optional

from keyboard_switcher.keyboard_switcher import KeyboardSwitcher


class KeyboardSwitcherHyprland(KeyboardSwitcher):
    def __init__(self, default_keyboard: int, alternative_keyboard: int):
        super().__init__(default_keyboard, alternative_keyboard)
        self.current = 0

    def switch_keyboard(self, id: int):
        os.system(F"hyprctl switchxkblayout all {id} > /dev/null")
        self.current = id

    def get_current_keyboard(self) -> Optional[int]:
        return self.current
