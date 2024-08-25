import os
from typing import Optional

from keyboard_switcher.keyboard_switcher import KeyboardSwitcher


class KeyboardSwitcherKDE(KeyboardSwitcher):
    def __init__(self, default_keyboard: int, alternative_keyboard: int):
        super().__init__(default_keyboard, alternative_keyboard)

    def switch_keyboard(self, id: int):
        os.system(F"qdbus org.kde.keyboard /Layouts org.kde.KeyboardLayouts.setLayout {id} > /dev/null")

    def get_current_keyboard(self) -> Optional[int]:
        proc = os.popen(F"qdbus org.kde.keyboard /Layouts org.kde.KeyboardLayouts.getLayout")
        val = proc.readline()
        if val == '':
            return None
        return int(val)
