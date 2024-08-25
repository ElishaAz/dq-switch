#!/usr/bin/python
import threading
from contextlib import contextmanager
from typing import Callable, Dict, Union

import Xlib
import Xlib.display
import psutil as psutil


class WindowInfo:
    def __init__(self, handler: Callable[[Dict[str, Union[int, str, None]]], None]):
        self.handler = handler
        self.disp = Xlib.display.Display()
        self.NET_ACTIVE_WINDOW = self.disp.intern_atom('_NET_ACTIVE_WINDOW')
        self.NET_WM_NAME = self.disp.intern_atom('_NET_WM_NAME')  # UTF-8
        self.NET_WM_PID = self.disp.intern_atom('_NET_WM_PID')
        self.WM_NAME = self.disp.intern_atom('WM_NAME')  # Legacy encoding

        self.root = self.disp.screen().root
        self.root.change_attributes(event_mask=Xlib.X.PropertyChangeMask)
        self.last_seen = {'xid': None, 'title': None, 'pid': None, 'process_name': None}

        self.should_run = False

    def run(self):
        self.should_run = True
        self._main_loop()

    def stop(self):
        self.should_run = False

    def __enter__(self):
        self.should_run = True
        self.thread = threading.Thread(target=self._main_loop)
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.should_run = False

    @contextmanager
    def window_obj(self, win_id):
        """Simplify dealing with BadWindow (make it either valid or None)"""
        window_obj = None
        if win_id:
            try:
                window_obj = self.disp.create_resource_object('window', win_id)
            except Xlib.error.XError:
                pass
        yield window_obj

    def get_active_window(self):
        win_id = self.root.get_full_property(self.NET_ACTIVE_WINDOW,
                                             Xlib.X.AnyPropertyType).value[0]

        focus_changed = (win_id != self.last_seen['xid'])
        if focus_changed:
            with self.window_obj(self.last_seen['xid']) as old_win:
                if old_win:
                    old_win.change_attributes(event_mask=Xlib.X.NoEventMask)

            self.last_seen['xid'] = win_id
            with self.window_obj(win_id) as new_win:
                if new_win:
                    new_win.change_attributes(event_mask=Xlib.X.PropertyChangeMask)

        return win_id, focus_changed

    def _get_window_name_inner(self, win_obj):
        """Simplify dealing with _NET_WM_NAME (UTF-8) vs. WM_NAME (legacy)"""
        for atom in (self.NET_WM_NAME, self.WM_NAME):
            try:
                window_name = win_obj.get_full_property(atom, Xlib.X.AnyPropertyType)
            except UnicodeDecodeError:  # Apparently a Debian distro package bug
                title = "<could not decode characters>"
            else:
                if window_name:
                    win_name = window_name.value
                    if isinstance(win_name, bytes):
                        # Apparently COMPOUND_TEXT is so arcane that this is how
                        # tools like xprop deal with receiving it these days
                        win_name = win_name.decode('latin1', 'replace')
                    return win_name
                else:
                    title = "<unnamed window>"

        return "{} (XID: {})".format(title, win_obj.id)

    def _get_window_pid(self, win_obj):
        atom = self.NET_WM_PID
        pid = win_obj.get_full_property(atom, Xlib.X.AnyPropertyType)

        pid = None if pid is None else pid.value[0]

        pid_changed = (pid != self.last_seen['pid'])
        self.last_seen['pid'] = pid

        return pid, pid_changed

    def get_window_pid(self, win_id):
        if not win_id:
            self.last_seen['pid'] = None
            return self.last_seen['pid']

        pid_changed = False
        with self.window_obj(win_id) as wobj:
            if wobj:
                pid = self._get_window_pid(wobj)[0]
                pid_changed = (pid != self.last_seen['pid'])
                self.last_seen['pid'] = pid

        return self.last_seen['pid'], pid_changed

    def get_window_pid_name(self, pid):
        return None if pid is None else psutil.Process(pid).name()

    def get_window_name(self, win_id):
        if not win_id:
            self.last_seen['title'] = "<no window id>"
            return self.last_seen['title']

        title_changed = False
        with self.window_obj(win_id) as wobj:
            if wobj:
                win_title = self._get_window_name_inner(wobj)
                title_changed = (win_title != self.last_seen['title'])
                self.last_seen['title'] = win_title

        return self.last_seen['title'], title_changed

    def handle_xevent(self, event):
        if event.type != Xlib.X.PropertyNotify:
            return

        changed = False
        if event.atom == self.NET_ACTIVE_WINDOW:
            if self.get_active_window()[1]:
                changed = changed or self.get_window_name(self.last_seen['xid'])[1]
        elif event.atom in (self.NET_WM_NAME, self.WM_NAME):
            changed = changed or self.get_window_name(self.last_seen['xid'])[1]

        if changed:
            self.get_window_pid(self.last_seen['xid'])
            self.last_seen['process_name'] = self.get_window_pid_name(self.last_seen['pid'])

        if changed:
            self.handle_change(self.last_seen)

    def handle_change(self, new_state):
        """Replace this with whatever you want to actually do"""
        self.handler(new_state)

    def _main_loop(self):
        while self.should_run:  # next_event() sleeps until we get an event
            self.handle_xevent(self.disp.next_event())


if __name__ == '__main__':
    wi = WindowInfo(print)
    wi.run()
