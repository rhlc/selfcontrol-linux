import json

import dbus
import dbus.mainloop.glib

from selfcontrol.constants import DBUS_INTERFACE, DBUS_NAME, DBUS_PATH


class SelfControlClient:
    def __init__(self):
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self._bus = dbus.SystemBus()
        self._proxy = self._bus.get_object(DBUS_NAME, DBUS_PATH)
        self._iface = dbus.Interface(self._proxy, DBUS_INTERFACE)

    def start_block(self, duration_seconds):
        return bool(self._iface.StartBlock(int(duration_seconds)))

    def get_status(self):
        raw = self._iface.GetStatus()
        return json.loads(str(raw))

    def set_blocklist(self, domains):
        return bool(self._iface.SetBlocklist(domains))

    def get_blocklist(self):
        return [str(d) for d in self._iface.GetBlocklist()]

    def connect_tick_signal(self, callback):
        self._bus.add_signal_receiver(
            callback,
            signal_name="TimerTick",
            dbus_interface=DBUS_INTERFACE,
            bus_name=DBUS_NAME,
            path=DBUS_PATH,
        )
