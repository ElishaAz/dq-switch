from abc import ABC, abstractmethod
from typing import Optional


class KeyboardSwitcher(ABC):
    def __init__(self, default_keyboard: int, alternative_keyboard: int):
        self.alternative_keyboard = alternative_keyboard
        self.default_keyboard = default_keyboard

        self.alternative_on = False

    def switch_to_default(self):
        self.switch_keyboard(self.default_keyboard)
        self.alternative_on = False

    def switch_to_alternative(self):
        self.switch_keyboard(self.alternative_keyboard)
        self.alternative_on = True

    def alternative_is_on(self):
        return self.alternative_on

    def is_switchable(self):
        return self.get_current_keyboard() in (self.default_keyboard, self.alternative_keyboard)

    @abstractmethod
    def switch_keyboard(self, id: int):
        pass

    @abstractmethod
    def get_current_keyboard(self) -> Optional[int]:
        pass