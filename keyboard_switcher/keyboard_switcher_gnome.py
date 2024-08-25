import os
from typing import Optional

from keyboard_switcher.keyboard_switcher import KeyboardSwitcher


class KeyboardSwitcherGnome(KeyboardSwitcher):
    def __init__(self, default_keyboard: int, alternative_keyboard: int):
        super().__init__(default_keyboard, alternative_keyboard)

    def switch_keyboard(self, id: int):
        os.system(F"gdbus call "
                  F"--session --dest org.gnome.Shell "
                  F"--object-path /org/gnome/Shell/Extensions/SwitchToKeyboardLayout "
                  F"--method org.gnome.Shell.Extensions.SwitchToKeyboardLayout.Call {id} > /dev/null")

    def get_current_keyboard(self) -> Optional[int]:
        proc = os.popen(F"gdbus call "
                        F"--session --dest org.gnome.Shell "
                        F"--object-path /org/gnome/Shell/Extensions/SwitchToKeyboardLayout "
                        F"--method org.gnome.Shell.Extensions.SwitchToKeyboardLayout.Get")
        val = proc.readline()[1:-3]
        if val == '':
            return None
        return int(val)
