import json
import logging

import dbus
import dbus.mainloop.glib
import dbus.service
from gi.repository import GLib

from selfcontrol.constants import DBUS_INTERFACE, DBUS_NAME, DBUS_PATH
from selfcontrol_daemon.blocker import Blocker
from selfcontrol_daemon.state import StateManager
from selfcontrol_daemon.watcher import HostsWatcher

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger("selfcontrol-daemon")

REENFORCE_INTERVAL = 5  # re-apply blocks every N ticks


class SelfControlDaemon(dbus.service.Object):
    def __init__(self):
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        bus = dbus.SystemBus()
        bus_name = dbus.service.BusName(DBUS_NAME, bus)
        super().__init__(bus_name, DBUS_PATH)

        self._state = StateManager()
        self._blocker = Blocker()
        self._watcher = HostsWatcher(on_tamper=self._on_hosts_tampered)
        self._tick_count = 0

        # Resume active block on daemon startup (e.g. after reboot)
        if self._state.is_active():
            log.info(
                "Resuming active block, %d seconds remaining",
                self._state.remaining_seconds(),
            )
            self._apply_blocks()
            self._watcher.start()

        GLib.timeout_add_seconds(1, self._on_tick)

    def run(self):
        log.info("SelfControl daemon started")
        loop = GLib.MainLoop()
        loop.run()

    # -- D-Bus methods --

    @dbus.service.method(DBUS_INTERFACE, in_signature="i", out_signature="b")
    def StartBlock(self, duration_seconds):
        if self._state.is_active():
            log.warning("Block already active, ignoring StartBlock")
            return False

        if duration_seconds <= 0:
            return False

        blocklist = self._state.get_blocklist()
        if not blocklist:
            log.warning("Blocklist is empty, ignoring StartBlock")
            return False

        log.info("Starting block for %d seconds", duration_seconds)

        # Resolve IPs BEFORE applying hosts blocks
        resolved = self._blocker.resolve_domains(blocklist)
        self._state.set_resolved_ips(resolved)

        self._state.start(duration_seconds)
        self._apply_blocks()
        self._watcher.start()
        return True

    @dbus.service.method(DBUS_INTERFACE, in_signature="", out_signature="s")
    def GetStatus(self):
        return json.dumps({
            "active": self._state.is_active(),
            "remaining": self._state.remaining_seconds(),
            "blocklist": self._state.get_blocklist(),
        })

    @dbus.service.method(DBUS_INTERFACE, in_signature="as", out_signature="b")
    def SetBlocklist(self, domains):
        if self._state.is_active():
            log.warning("Block is active, cannot modify blocklist")
            return False
        self._state.set_blocklist(list(domains))
        log.info("Blocklist updated: %s", list(domains))
        return True

    @dbus.service.method(DBUS_INTERFACE, in_signature="", out_signature="as")
    def GetBlocklist(self):
        return self._state.get_blocklist()

    # -- D-Bus signals --

    @dbus.service.signal(DBUS_INTERFACE, signature="i")
    def TimerTick(self, remaining_seconds):
        pass

    # -- Internal --

    def _on_tick(self):
        if not self._state.is_active():
            return True  # keep timer running

        remaining = self._state.remaining_seconds()

        if remaining <= 0:
            log.info("Block expired, cleaning up")
            self._remove_blocks()
            self._watcher.stop()
            self._state.clear()
            self.TimerTick(0)
            return True

        self.TimerTick(remaining)

        self._tick_count += 1
        if self._tick_count >= REENFORCE_INTERVAL:
            self._tick_count = 0
            self._apply_blocks()

        return True  # keep timer running

    def _apply_blocks(self):
        blocklist = self._state.get_blocklist()
        resolved = self._state.get_resolved_ips()

        self._watcher.notify_self_write()
        self._blocker.apply_hosts_blocks(blocklist)

        try:
            self._blocker.apply_nftables_blocks(resolved)
        except Exception as e:
            log.error("Failed to apply nftables blocks: %s", e)

    def _remove_blocks(self):
        self._watcher.notify_self_write()
        self._blocker.remove_hosts_blocks()
        self._blocker.remove_nftables_blocks()

    def _on_hosts_tampered(self):
        if self._state.is_active():
            log.warning("Hosts file tampered with, re-applying blocks")
            self._watcher.notify_self_write()
            self._blocker.apply_hosts_blocks(self._state.get_blocklist())
