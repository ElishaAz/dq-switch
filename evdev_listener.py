from typing import Callable, Optional

from evdev import InputDevice, InputEvent
from select import select
from glob import glob

KEY_LEFTCTRL = 29
KEY_RIGHTCTRL = 97
KEY_LEFTALT = 56
KEY_RIGHTALT = 100
KEY_LEFTMETA = 125
KEY_RIGHTMETA = 126

KEY_F2 = 60
KEY_F4 = 62

ALL_KEYS = (KEY_LEFTCTRL, KEY_RIGHTCTRL, KEY_LEFTALT, KEY_RIGHTALT, KEY_LEFTMETA, KEY_RIGHTMETA)

KEY_PRESSED = 1
KEY_RELEASED = 0

EV_KEY = 0x01


class EVDevListener:
    def __init__(self, device_glob: str, keyup_listener: Callable[[int, int],Optional[bool]], keydown_listener: Callable[[int, int],Optional[bool]]):
        self.keyup_listener = keyup_listener
        self.keydown_listener = keydown_listener
        devices = map(InputDevice, glob(device_glob, recursive=True))
        self.devices = {dev.fd: dev for dev in devices if dev.info}
        self.run = True

    def main(self):
        while self.run:
            r, w, x = select(self.devices, [], [])
            for fd in r:
                event: InputEvent
                for event in self.devices[fd].read():
                    if event.type == EV_KEY:
                        if event.value == KEY_PRESSED:
                            if self.keydown_listener(event.code, fd):
                                self.run = False
                                break
                        elif event.value == KEY_RELEASED:
                            if self.keyup_listener(event.code, fd):
                                self.run = False
                                break
                if not self.run:
                    break
