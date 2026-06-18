import os
from typing import Optional

from keyboard_switcher.keyboard_switcher import KeyboardSwitcher


class KeyboardSwitcherSway(KeyboardSwitcher):
    def __init__(self, default_keyboard: int, alternative_keyboard: int):
        super().__init__(default_keyboard, alternative_keyboard)
        self.current = 0

    def switch_keyboard(self, id: int):
        os.system(F"swaymsg input 'type:keyboard' xkb_switch_layout {id}")
        self.current = id

    def get_current_keyboard(self) -> Optional[int]:
        # TODO: read current layout using `swaymsg -r -t get_inputs`
        return self.current
