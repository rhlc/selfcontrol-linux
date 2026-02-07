#!/usr/bin/env bash
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
    echo "Error: setup.sh must be run as root (use sudo)" >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_DIR="/usr/lib/selfcontrol-linux"

echo "==> Installing dependencies..."
dnf install -y python3 python3-gobject gtk4 libadwaita python3-dbus nftables

echo "==> Installing SelfControl Linux..."

# Install Python packages
mkdir -p "$INSTALL_DIR"
cp -r "$SCRIPT_DIR/selfcontrol" "$INSTALL_DIR/"
cp -r "$SCRIPT_DIR/selfcontrol_daemon" "$INSTALL_DIR/"
cp -r "$SCRIPT_DIR/data" "$INSTALL_DIR/"

# Install launcher scripts
install -m 755 "$SCRIPT_DIR/bin/selfcontrol" /usr/bin/selfcontrol
install -m 755 "$SCRIPT_DIR/bin/selfcontrol-daemon" /usr/libexec/selfcontrol-daemon

# Install D-Bus system bus policy
install -m 644 "$SCRIPT_DIR/data/com.github.selfcontrol.conf" /usr/share/dbus-1/system.d/

# Install D-Bus activation service
install -m 644 "$SCRIPT_DIR/data/com.github.selfcontrol.service" /usr/share/dbus-1/system-services/

# Install Polkit policy
install -m 644 "$SCRIPT_DIR/data/com.github.selfcontrol.policy" /usr/share/polkit-1/actions/

# Install systemd service
install -m 644 "$SCRIPT_DIR/data/selfcontrol-daemon.service" /usr/lib/systemd/system/

# Install desktop entry
install -m 644 "$SCRIPT_DIR/data/com.github.selfcontrol.desktop" /usr/share/applications/

# Create state directory
mkdir -p /var/lib/selfcontrol-linux

# Reload and enable
systemctl daemon-reload
systemctl enable selfcontrol-daemon.service

echo "==> Installation complete!"
echo "    Launch SelfControl from your application menu or run: selfcontrol"
