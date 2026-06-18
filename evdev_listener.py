import errno
import time
from glob import glob
from select import select
from typing import Callable, Optional

from evdev import InputDevice, InputEvent
from inotify_simple import INotify, flags

KEY_LEFTCTRL = 29
KEY_RIGHTCTRL = 97
KEY_LEFTALT = 56
KEY_RIGHTALT = 100
KEY_LEFTMETA = 125
KEY_RIGHTMETA = 126

KEY_F2 = 60
KEY_F4 = 62

ALL_KEYS = (KEY_LEFTCTRL, KEY_RIGHTCTRL, KEY_LEFTALT, KEY_RIGHTALT, KEY_LEFTMETA, KEY_RIGHTMETA)
META_KEYS = (KEY_LEFTMETA, KEY_RIGHTMETA)

KEY_PRESSED = 1
KEY_RELEASED = 0

EV_KEY = 0x01


class EVDevListener:
    def __init__(self, device_glob: str, keyup_listener: Callable[[int, int], Optional[bool]],
                 keydown_listener: Callable[[int, int], Optional[bool]],
                 device_listener: Callable[[int, str, bool], Optional[bool]]):
        self.keyup_listener = keyup_listener
        self.keydown_listener = keydown_listener
        self.device_listener = device_listener
        self.device_glob = device_glob
        input_devices = map(InputDevice, glob(self.device_glob, recursive=True))
        self.devices = {dev.fd: dev for dev in input_devices if dev.info}
        self.run = True

        for fd, device in self.devices.items():
            if self.device_listener(fd, device.path, True):
                self.run = False

        self.inotify = INotify()
        wd = self.inotify.add_watch("/dev/input", flags.CREATE | flags.MOVED_TO | flags.DELETE)

        self.select_fds = list(self.devices.keys()) + [self.inotify.fd]

    def reload_devices(self):
        old_paths = {dev.path: dev for dev in self.devices.values()}
        new_paths = set(glob(self.device_glob, recursive=True))

        removed = old_paths.keys() - new_paths
        added = new_paths - old_paths.keys()

        for path in removed:
            device = old_paths[path]
            fd = device.fd

            self.devices[fd].close()
            del self.devices[fd]

            if self.device_listener(fd, device.path, False):
                self.run = False
                return

        added_devices = [InputDevice(path) for path in added]
        self.devices.update({dev.fd: dev for dev in added_devices})
        self.select_fds = list(self.devices.keys()) + [self.inotify.fd]

        for device in added_devices:
            if self.device_listener(device.fd, device.path, True):
                self.run = False
                return

    def main(self):
        while self.run:
            r, w, x = select(self.select_fds, [], [])
            for fd in r:
                if fd == self.inotify.fd:
                    if any(event.mask & (flags.CREATE | flags.MOVED_TO | flags.DELETE) for event in
                           self.inotify.read(fd)):
                        time.sleep(0.1) # we need to wait a bit for udev to add the device
                        self.reload_devices()
                    break

                event: InputEvent
                try:
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
                except OSError as e:
                    if e.errno == errno.ENODEV:
                        # Device disconnected, will be caught by inotify
                        pass
                    else:
                        raise

                if not self.run:
                    break
