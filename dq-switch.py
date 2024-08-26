#!/usr/bin/env python3
import os
import threading
import time
from typing import Dict, Union, Tuple

from keyboard_switcher import KeyboardSwitcher, get_keyboard_switcher
import evdev_listener
from configparser import ConfigParser
from argparse import ArgumentParser

def _list_from_config(string: str):
    if string is None:
        return []
    return [x.strip() for x in string.split('\n') if len(x.strip()) != 0]

class Main:

    def __init__(self, config: ConfigParser):

        self.main_keyboard = config["Main"].getint("Main")
        self.alt_keyboard = config["Main"].getint("Alternative")

        self.desktop = config["Main"].get("Desktop", os.environ.get('XDG_CURRENT_DESKTOP'))

        self.switcher: KeyboardSwitcher = get_keyboard_switcher(self.desktop)(self.main_keyboard, self.alt_keyboard)

        self.meta_delay = config["Main"].getfloat("MetaDelay",0.0)

        self.device_glob = config["Main"].get("Device", "/dev/input/by-path/*-event-kbd")

        self.F2_DOWN = False
        self.F4_DOWN = False

        self.ALWAYS_DEFAULT = _list_from_config(config["Apps"].get("AlwaysMain"))
        self.ALWAYS_ALTERNATIVE = _list_from_config(config["Apps"].get("AlwaysAlternative"))

        self.AUTOSWITCHER_IS_ON = True

        # self.keys = \
        #     {
        #         keyboard.Key.ctrl: False,
        #         keyboard.Key.alt: False,
        #         keyboard.Key.cmd: False,
        #         keyboard.Key.ctrl_r: False,
        #         keyboard.Key.alt_r: False
        #     }
        self.keys: Dict[Tuple[int, int], bool] = dict()

        self.switcher.switch_to_default()

    def meta_thread(self, key, keyboard_id):
        time.sleep(0.1)
        if self.keys[(key, keyboard_id)] and not self.switcher.alternative_is_on():
            self.switcher.switch_to_alternative()

    def on_press_new(self, key, keyboard_id):
        if key == evdev_listener.KEY_F2: self.F2_DOWN = True
        if key == evdev_listener.KEY_F4: self.F4_DOWN = True

        if self.F2_DOWN and self.F4_DOWN:
            return False

        if not self.AUTOSWITCHER_IS_ON: return

        if key in evdev_listener.ALL_KEYS:
            self.keys[(key, keyboard_id)] = True
            if key in (evdev_listener.KEY_LEFTMETA, evdev_listener.KEY_RIGHTMETA) and self.meta_delay > 0:
                threading.Timer(self.meta_delay, self.meta_thread, args=(key, keyboard_id)).start()
            elif not self.switcher.alternative_is_on() and self.switcher.is_switchable():
                self.switcher.switch_to_alternative()

    def on_release_new(self, key, keyboard_id):
        if key == evdev_listener.KEY_F2: self.F2_DOWN = False
        if key == evdev_listener.KEY_F4: self.F4_DOWN = False

        if not self.AUTOSWITCHER_IS_ON: return

        if (key, keyboard_id) in self.keys.keys():
            self.keys[(key, keyboard_id)] = False

        if self.switcher.alternative_is_on():
            switch_back = True
            for k in self.keys.values():
                if k:
                    switch_back = False
                    break
            if switch_back and self.switcher.is_switchable():
                self.switcher.switch_to_default()

    # def on_press(self, key):
    #
    #     if key == keyboard.Key.f2: self.F2_DOWN = True
    #     if key == keyboard.Key.f4: self.F4_DOWN = True
    #
    #     if self.F2_DOWN and self.F4_DOWN:
    #         return False
    #
    #     if not self.AUTOSWITCHER_IS_ON: return
    #
    #     if key == keyboard.Key.cmd:
    #         self.keys[keyboard.Key.cmd] = True
    #         threading.Thread(target=self.cmd_thread).start()
    #     elif key in self.keys.keys():
    #         self.keys[key] = True
    #         if not self.switcher.alternative_is_on() and self.switcher.is_switchable():
    #             self.switcher.switch_to_alternative()
    #
    # def on_release(self, key):
    #
    #     if key == keyboard.Key.f2: self.F2_DOWN = False
    #     if key == keyboard.Key.f4: self.F4_DOWN = False
    #
    #     if not self.AUTOSWITCHER_IS_ON: return
    #
    #     if key in self.keys.keys():
    #         self.keys[key] = False
    #
    #     if self.switcher.alternative_is_on():
    #         switch_back = True
    #         for k in self.keys.values():
    #             if k:
    #                 switch_back = False
    #                 break
    #         if switch_back and self.switcher.is_switchable():
    #             self.switcher.switch_to_default()

    def handler(self, state: Dict[str, Union[int, str, None]]):
        if state['process_name'] in self.ALWAYS_DEFAULT:
            self.AUTOSWITCHER_IS_ON = False
            self.switcher.switch_to_default()
        elif state['process_name'] in self.ALWAYS_ALTERNATIVE:
            self.AUTOSWITCHER_IS_ON = False
            self.switcher.switch_to_alternative()
        elif not self.AUTOSWITCHER_IS_ON:
            self.AUTOSWITCHER_IS_ON = True
            self.switcher.switch_to_default()

    def main(self):
        # with keyboard.Listener(
        #         on_press=self.on_press,
        #         on_release=self.on_release) as listener:
        #     with WindowInfo(self.handler) as wi:
        #         listener.join()
        #     wi.thread.join()

        listener = evdev_listener.EVDevListener(self.device_glob, self.on_release_new, self.on_press_new)
        listener.main()



def main():
    parser = ArgumentParser(prog="dq-switch", description="Dvorak QWERTY switcher")

    parser.add_argument('-m','--main',type=int, help="The main keyboard layout. This will override any value in the config file.")
    parser.add_argument('-a','--alternative',type=int, help="The alternative keyboard layout. This layout will be enabled whenever Ctl, Alt or Meta are pressed. This will override any value in the config file.")
    parser.add_argument('-d','--desktop',type=str, help="The desktop environment. Either 'KDE' or 'GNOME'. This will override any value in the config file. Default is auto-detect.")
    parser.add_argument('-c','--config',type=str, help="Path to the config file. Defaults to the config file in the same directory as dq-switch.py")

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

    # print config
    # s = StringIO()
    # config.write(s)
    # print(s.getvalue())

    main = Main(config)
    main.main()


if __name__ == '__main__':
    main()
