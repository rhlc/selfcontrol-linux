import ctypes
import ctypes.util
import os
import struct
import time

from gi.repository import GLib

from selfcontrol.constants import HOSTS_FILE

# inotify constants
IN_MODIFY = 0x00000002
IN_CLOSE_WRITE = 0x00000008
IN_MOVE_SELF = 0x00000800
IN_DELETE_SELF = 0x00000400
IN_IGNORED = 0x00008000
WATCH_MASK = IN_MODIFY | IN_CLOSE_WRITE | IN_MOVE_SELF | IN_DELETE_SELF

SELF_WRITE_COOLDOWN = 1.0  # ignore events for 1s after our own write

# Load libc
_libc_name = ctypes.util.find_library("c")
_libc = ctypes.CDLL(_libc_name, use_errno=True)

_libc.inotify_init.argtypes = []
_libc.inotify_init.restype = ctypes.c_int
_libc.inotify_add_watch.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_uint32]
_libc.inotify_add_watch.restype = ctypes.c_int


class HostsWatcher:
    def __init__(self, on_tamper):
        self._on_tamper = on_tamper
        self._last_self_write = 0
        self._fd = None
        self._wd = None
        self._source_id = None

    def start(self):
        if self._fd is not None:
            return  # already running

        self._fd = _libc.inotify_init()
        if self._fd < 0:
            raise OSError(f"inotify_init failed: errno {ctypes.get_errno()}")

        self._add_watch()

        self._source_id = GLib.io_add_watch(
            self._fd, GLib.PRIORITY_DEFAULT, GLib.IOCondition.IN, self._on_event
        )

    def stop(self):
        if self._source_id is not None:
            GLib.source_remove(self._source_id)
            self._source_id = None
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None
        self._wd = None

    def notify_self_write(self):
        self._last_self_write = time.monotonic()

    def _is_self_write(self):
        return (time.monotonic() - self._last_self_write) < SELF_WRITE_COOLDOWN

    def _add_watch(self):
        path = HOSTS_FILE.encode("utf-8")
        self._wd = _libc.inotify_add_watch(self._fd, path, WATCH_MASK)
        if self._wd < 0:
            raise OSError(f"inotify_add_watch failed: errno {ctypes.get_errno()}")

    def _on_event(self, fd, condition):
        buf = os.read(fd, 4096)
        offset = 0
        need_rewatch = False

        while offset < len(buf):
            # inotify_event: wd(i32), mask(u32), cookie(u32), len(u32)
            wd, mask, cookie, name_len = struct.unpack_from("iIII", buf, offset)
            offset += 16 + name_len

            if mask & (IN_MOVE_SELF | IN_DELETE_SELF | IN_IGNORED):
                need_rewatch = True

        if need_rewatch:
            GLib.timeout_add(200, self._rewatch_and_trigger)
        elif not self._is_self_write():
            self._on_tamper()

        return True  # keep the GLib watch active

    def _rewatch_and_trigger(self):
        try:
            self._add_watch()
        except OSError:
            GLib.timeout_add(500, self._rewatch_and_trigger)
            return False

        if not self._is_self_write():
            self._on_tamper()
        return False  # one-shot timeout
