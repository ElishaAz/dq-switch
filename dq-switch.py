#!/usr/bin/env python3
import os
import threading
from argparse import ArgumentParser
from configparser import ConfigParser
from typing import Dict, Union, Tuple, Set

import evdev_listener
from keyboard_switcher import KeyboardSwitcher, get_keyboard_switcher


def _list_from_config(string: str):
    if string is None:
        return []
    return [x.strip() for x in string.split('\n') if len(x.strip()) != 0]


class Main:
    def __init__(self, config: ConfigParser, verbose: bool):
        self.verbose = verbose
        self.main_keyboard = config["Main"].getint("Main")
        self.alt_keyboard = config["Main"].getint("Alternative")
        self.desktop = config["Main"].get("Desktop", os.environ.get('XDG_CURRENT_DESKTOP'))
        self.meta_delay = config["Main"].getfloat("MetaDelay", 0.0)
        self.device_glob = config["Main"].get("Device", "/dev/input/by-path/*-event-kbd")
        self.ALWAYS_DEFAULT = _list_from_config(config["Apps"].get("AlwaysMain"))
        self.ALWAYS_ALTERNATIVE = _list_from_config(config["Apps"].get("AlwaysAlternative"))

        self.switcher: KeyboardSwitcher = get_keyboard_switcher(self.desktop)(self.main_keyboard, self.alt_keyboard)

        self.F2_DOWN = False
        self.F4_DOWN = False

        self.switcher_is_on = True
        self.keys: Set[Tuple[int, int]] = set()
        self.meta_delay_timers: Dict[Tuple[int, int], threading.Timer] = dict()

        self.switcher.switch_to_default()

    def on_press(self, key, keyboard_id):
        if self.verbose: print(F"on_press({key}, {keyboard_id})")

        if key == evdev_listener.KEY_F2: self.F2_DOWN = True
        if key == evdev_listener.KEY_F4: self.F4_DOWN = True

        if self.F2_DOWN and self.F4_DOWN:
            return True

        if key in evdev_listener.ALL_KEYS:
            if (key in evdev_listener.META_KEYS and self.meta_delay > 0
                    and not (key, keyboard_id) in self.meta_delay_timers.keys()):
                timer = threading.Timer(self.meta_delay, self.meta_thread, args=(key, keyboard_id))
                self.meta_delay_timers[(key, keyboard_id)] = timer
                timer.start()
            else:
                self.keys.add((key, keyboard_id))

        self.update_active_keyboard()

        return False

    def on_release(self, key, keyboard_id):
        if self.verbose: print(F"on_release({key}, {keyboard_id})")

        if key == evdev_listener.KEY_F2: self.F2_DOWN = False
        if key == evdev_listener.KEY_F4: self.F4_DOWN = False

        if (key, keyboard_id) in self.meta_delay_timers.keys():
            timer = self.meta_delay_timers.pop((key, keyboard_id))
            timer.cancel()

        if (key, keyboard_id) in self.keys:
            self.keys.remove((key, keyboard_id))

        self.update_active_keyboard()

    def on_device(self, keyboard_id, path, added):
        if self.verbose: print(F"on_device({keyboard_id}, {path}, {added})")

        if not added:  # Removed
            to_remove = [(k, kbd) for k, kbd in self.keys if kbd == keyboard_id]
            for k in to_remove:
                self.keys.remove(k)
            if len(to_remove) > 0:
                self.update_active_keyboard()

    def meta_thread(self, key, keyboard_id):
        self.keys.add((key, keyboard_id))
        self.update_active_keyboard()

    def update_active_keyboard(self):
        if not self.switcher.is_switchable(): return

        need_alternative = len(self.keys) > 0
        if self.switcher.alternative_is_on() and not need_alternative:
            if self.verbose: print("Switching to default")
            self.switcher.switch_to_default()
        if not self.switcher.alternative_is_on() and need_alternative:
            if self.verbose: print("Switching to alternative")
            self.switcher.switch_to_alternative()

    def handler(self, state: Dict[str, Union[int, str, None]]):
        if state['process_name'] in self.ALWAYS_DEFAULT:
            self.switcher_is_on = False
            self.switcher.switch_to_default()
        elif state['process_name'] in self.ALWAYS_ALTERNATIVE:
            self.switcher_is_on = False
            self.switcher.switch_to_alternative()
        elif not self.switcher_is_on:
            self.switcher_is_on = True
            self.switcher.switch_to_default()

    def main(self):
        listener = evdev_listener.EVDevListener(self.device_glob, self.on_release, self.on_press, self.on_device)
        listener.main()


def main():
    parser = ArgumentParser(prog="dq-switch", description="Dvorak QWERTY switcher")

    parser.add_argument('-m', '--main', type=int,
                        help="The main keyboard layout. This will override any value in the config file.")
    parser.add_argument('-a', '--alternative', type=int,
                        help="The alternative keyboard layout. "
                             "This layout will be enabled whenever Ctl, Alt or Meta are pressed. "
                             "This will override any value in the config file.")
    parser.add_argument('-d', '--desktop', type=str,
                        help="The desktop environment. Either 'KDE' or 'GNOME'. "
                             "This will override any value in the config file. Default is auto-detect.")
    parser.add_argument('-c', '--config', type=str,
                        help="Path to the config file. Defaults to the config file in the same directory as dq-switch.py")
    parser.add_argument('-v', '--verbose', action='store_true', )

    args = parser.parse_args()
    print(args)

    config_path = args.config or os.path.join(os.path.dirname(os.path.realpath(__file__)), 'dq-switch.cfg')
    print(config_path)
    config = ConfigParser()
    if os.path.isfile(config_path):
        with open(config_path, 'r') as f:
            config.read_file(f)

    if not "Main" in config:
        config.add_section("Main")
    if args.main is not None:
        config.set("Main", "Main", str(args.main))
    if args.alternative is not None:
        config.set("Main", "Alternative", str(args.alternative))
    if args.desktop is not None:
        config.set("Main", "Desktop", str(args.desktop))

    main = Main(config, args.verbose)
    main.main()


if __name__ == '__main__':
    main()
