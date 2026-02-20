# SelfControl for Linux

A Linux port of the macOS [SelfControl](https://github.com/SelfControlApp/selfcontrol) app. Block distracting websites for a set duration. Once a block is started, it cannot be undone — even if you restart your computer.

![SelfControl idle](screenshots/idle.png)
![SelfControl blocking](screenshots/blocking.png)

## How It Works

- Blocks websites via `/etc/hosts` (DNS-level) **and** nftables firewall rules (IP-level)
- A root daemon enforces blocks — you can't bypass them by editing `/etc/hosts` (an inotify watcher restores entries within seconds)
- Block duration is stored as an absolute timestamp, so blocks survive reboots
- Rules are re-enforced every 5 seconds in case of firewall reloads or manual deletion

## Requirements

- Linux with GNOME desktop (GTK4 / libadwaita)
- Tested on Fedora 43, Ubuntu 24.04, Arch Linux

## Installation

### Debian / Ubuntu

Download the `.deb` from the [latest release](https://github.com/rhlc/selfcontrol-linux/releases/latest):

```bash
sudo apt install ./selfcontrol-linux_0.1.0_all.deb
```

### Fedora / RHEL

Download the `.rpm` from the [latest release](https://github.com/rhlc/selfcontrol-linux/releases/latest):

```bash
sudo dnf install ./selfcontrol-linux-0.1.0-1.fc43.noarch.rpm
```

### Arch Linux

Download the source tarball from the [latest release](https://github.com/rhlc/selfcontrol-linux/releases/latest), extract it, then build with the included PKGBUILD:

```bash
tar xzf selfcontrol-linux-0.1.0.tar.gz
cd selfcontrol-linux-0.1.0/packaging/arch
VERSION=0.1.0 SRCDIR="$PWD/../.." makepkg -si
```

### From source

```bash
git clone https://github.com/rhlc/selfcontrol-linux.git
cd selfcontrol-linux
sudo bash setup.sh
```

This installs all dependencies (Fedora only), copies files to system directories, and enables the daemon service.

## Usage

Launch **SelfControl** from your application menu, or run:

```bash
selfcontrol
```

1. **Edit Blocklist** — add or remove websites to block (default: facebook, twitter, instagram, reddit, youtube)
2. **Adjust duration** — drag the slider from 15 minutes to 24 hours
3. **Start Block** — click to begin. The button turns red and shows a countdown. The slider and blocklist editor are locked until the block expires.

That's it. Wait it out.

## Uninstalling

If installed via a package:

```bash
sudo apt remove selfcontrol-linux    # Debian/Ubuntu
sudo dnf remove selfcontrol-linux    # Fedora/RHEL
sudo pacman -R selfcontrol-linux     # Arch
```

If installed from source:

```bash
sudo rm -rf /usr/lib/selfcontrol-linux
sudo rm /usr/bin/selfcontrol /usr/libexec/selfcontrol-daemon
sudo rm /usr/share/dbus-1/system.d/com.github.selfcontrol.conf
sudo rm /usr/share/dbus-1/system-services/com.github.selfcontrol.service
sudo rm /usr/share/polkit-1/actions/com.github.selfcontrol.policy
sudo rm /usr/lib/systemd/system/selfcontrol-daemon.service
sudo rm /usr/share/applications/com.github.selfcontrol.desktop
sudo rm -rf /var/lib/selfcontrol-linux
sudo systemctl daemon-reload
```

## Architecture

```
GUI (Python + GTK4/libadwaita, runs as user)
  │
  │ D-Bus (system bus)
  ▼
Daemon (Python, runs as root via systemd)
  ├── /etc/hosts modification (with BEGIN/END markers)
  ├── nftables firewall rules (separate inet selfcontrol table)
  ├── inotify watcher (detects /etc/hosts tampering, re-applies)
  └── state persisted to /var/lib/selfcontrol-linux/state.json
```

## License

MIT
