import json
import os
import time

from selfcontrol.constants import (
    BLOCKLIST_FILE,
    DEFAULT_BLOCKLIST,
    STATE_DIR,
    STATE_FILE,
)


class StateManager:
    def __init__(self):
        os.makedirs(STATE_DIR, exist_ok=True)
        self._state = self._load_state()
        if not os.path.exists(BLOCKLIST_FILE):
            self.set_blocklist(DEFAULT_BLOCKLIST)

    def _load_state(self):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"end_time": 0, "resolved_ips": {}}

    def _save_state(self):
        tmp = STATE_FILE + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self._state, f)
        os.rename(tmp, STATE_FILE)

    def start(self, duration_seconds):
        self._state["end_time"] = time.time() + duration_seconds
        self._state["resolved_ips"] = {}
        self._save_state()

    def set_resolved_ips(self, resolved_ips):
        self._state["resolved_ips"] = resolved_ips
        self._save_state()

    def get_resolved_ips(self):
        return self._state.get("resolved_ips", {})

    def clear(self):
        self._state = {"end_time": 0, "resolved_ips": {}}
        self._save_state()

    def is_active(self):
        return self._state.get("end_time", 0) > time.time()

    def remaining_seconds(self):
        remaining = self._state.get("end_time", 0) - time.time()
        return max(0, int(remaining))

    def get_blocklist(self):
        try:
            with open(BLOCKLIST_FILE, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return DEFAULT_BLOCKLIST[:]

    def set_blocklist(self, domains):
        tmp = BLOCKLIST_FILE + ".tmp"
        with open(tmp, "w") as f:
            json.dump(domains, f)
        os.rename(tmp, BLOCKLIST_FILE)
