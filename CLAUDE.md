# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SelfControl for Linux — a port of the macOS SelfControl app. Blocks distracting websites via DNS (/etc/hosts) and firewall (nftables) for a set duration. Once started, blocks cannot be undone, even on reboot.

## Development Commands

```bash
# Install (first time, requires root)
sudo bash setup.sh

# Deploy code changes to system paths and restart daemon
sudo bash update.sh

# Launch GUI
selfcontrol

# View daemon logs
journalctl -u selfcontrol-daemon -f
```

There is no test suite, linter, or build step. The project is pure Python with no third-party dependencies beyond system packages (GTK4, libadwaita, python3-dbus, python3-gobject, nftables).

## Architecture

Two separate processes communicate over D-Bus (system bus):

**GUI** (`selfcontrol/`) — runs as regular user
- `app.py` → GTK4/libadwaita application entry point, forces light theme, loads CSS
- `window.py` → main window with two views: idle (duration slider + start button) and blocking (skull + countdown)
- `blocklist_dialog.py` → modal dialog for editing blocked domains
- `client.py` → thin D-Bus proxy to the daemon

**Daemon** (`selfcontrol_daemon/`) — runs as root via systemd
- `daemon.py` → D-Bus service object, main GLib event loop, re-enforces blocks every 5 seconds, emits `TimerTick` signal to GUI each second
- `blocker.py` → dual-layer blocking: writes `0.0.0.0`/`::` entries to `/etc/hosts` (with BEGIN/END markers) and creates nftables rules for resolved IPs
- `state.py` → persists block end time and resolved IPs to `/var/lib/selfcontrol-linux/state.json`, blocklist to `blocklist.json`
- `watcher.py` → inotify (via ctypes) on `/etc/hosts` to detect and re-apply blocks if tampered

**Data flow**: GUI calls D-Bus methods on daemon → daemon applies blocks and persists state → daemon emits `TimerTick` signals back to GUI.

**Key design choices**:
- Block end time stored as absolute Unix timestamp so blocks survive reboots
- DNS resolution happens at block start; resolved IPs are cached in state
- Both /etc/hosts AND nftables are used together for robust enforcement
- D-Bus bus name: `com.github.selfcontrol`, state dir: `/var/lib/selfcontrol-linux/`

## Configuration Files (data/)

- `com.github.selfcontrol.conf` — D-Bus policy (root owns bus, any user can call)
- `com.github.selfcontrol.policy` — PolicyKit (active users allowed without prompt)
- `selfcontrol-daemon.service` — systemd unit with security hardening (ProtectSystem, CapabilityBoundingSet)
- `style.css` — GTK4 CSS for the GUI
