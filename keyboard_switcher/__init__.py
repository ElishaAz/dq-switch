from typing import Type

from .keyboard_switcher import KeyboardSwitcher as KeyboardSwitcher

from os import environ

def get_keyboard_switcher(environment: str = environ.get('XDG_CURRENT_DESKTOP')) -> Type[KeyboardSwitcher]:
    environment = environment.lower()
    if 'kde' in  environment:
        from .keyboard_switcher_kde import KeyboardSwitcherKDE
        return KeyboardSwitcherKDE
    if 'gnome' in  environment:
        from .keyboard_switcher_gnome import KeyboardSwitcherGnome
        return KeyboardSwitcherGnome
    if 'hyprland' in  environment:
        from .keyboard_switcher_hyprland import KeyboardSwitcherHyprland
        return KeyboardSwitcherHyprland

    raise ValueError(f"Unsupported environment: {environment}")
