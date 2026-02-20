#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:?Usage: build-deb.sh VERSION SRCDIR}"
SRCDIR="${2:?Usage: build-deb.sh VERSION SRCDIR}"
BUILDDIR="$(dirname "$0")/build/selfcontrol-linux_${VERSION}_all"

rm -rf "$BUILDDIR"
mkdir -p "$BUILDDIR"

# --- DEBIAN control files ---
mkdir -p "$BUILDDIR/DEBIAN"

cat > "$BUILDDIR/DEBIAN/control" <<EOF
Package: selfcontrol-linux
Version: ${VERSION}
Architecture: all
Maintainer: SelfControl Linux Contributors
Description: Block distracting websites for a set duration
 A port of the macOS SelfControl app. Blocks distracting websites via
 DNS (/etc/hosts) and firewall (nftables) for a set duration. Once
 started, blocks cannot be undone, even on reboot.
Depends: python3, python3-gi, gir1.2-gtk-4.0, gir1.2-adw-1, python3-dbus, nftables
Section: utils
Priority: optional
Homepage: https://github.com/selfcontrol-linux/selfcontrol-linux
EOF

cat > "$BUILDDIR/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e
mkdir -p /var/lib/selfcontrol-linux
systemctl daemon-reload
systemctl enable selfcontrol-daemon.service
EOF
chmod 755 "$BUILDDIR/DEBIAN/postinst"

cat > "$BUILDDIR/DEBIAN/prerm" <<'EOF'
#!/bin/sh
set -e
if [ "$1" = "remove" ]; then
    systemctl stop selfcontrol-daemon.service || true
    systemctl disable selfcontrol-daemon.service || true
fi
EOF
chmod 755 "$BUILDDIR/DEBIAN/prerm"

cat > "$BUILDDIR/DEBIAN/postrm" <<'EOF'
#!/bin/sh
set -e
systemctl daemon-reload
EOF
chmod 755 "$BUILDDIR/DEBIAN/postrm"

# --- Application files ---

# Python packages
install -d "$BUILDDIR/usr/lib/selfcontrol-linux"
cp -r "$SRCDIR/selfcontrol" "$BUILDDIR/usr/lib/selfcontrol-linux/"
cp -r "$SRCDIR/selfcontrol_daemon" "$BUILDDIR/usr/lib/selfcontrol-linux/"
cp -r "$SRCDIR/data" "$BUILDDIR/usr/lib/selfcontrol-linux/"

# Launcher scripts
install -Dm755 "$SRCDIR/bin/selfcontrol" "$BUILDDIR/usr/bin/selfcontrol"
install -Dm755 "$SRCDIR/bin/selfcontrol-daemon" "$BUILDDIR/usr/libexec/selfcontrol-daemon"

# systemd service
install -Dm644 "$SRCDIR/data/selfcontrol-daemon.service" \
    "$BUILDDIR/usr/lib/systemd/system/selfcontrol-daemon.service"

# D-Bus config
install -Dm644 "$SRCDIR/data/com.github.selfcontrol.conf" \
    "$BUILDDIR/usr/share/dbus-1/system.d/com.github.selfcontrol.conf"
install -Dm644 "$SRCDIR/data/com.github.selfcontrol.service" \
    "$BUILDDIR/usr/share/dbus-1/system-services/com.github.selfcontrol.service"

# Polkit policy
install -Dm644 "$SRCDIR/data/com.github.selfcontrol.policy" \
    "$BUILDDIR/usr/share/polkit-1/actions/com.github.selfcontrol.policy"

# Desktop entry
install -Dm644 "$SRCDIR/data/com.github.selfcontrol.desktop" \
    "$BUILDDIR/usr/share/applications/com.github.selfcontrol.desktop"

# --- Build the .deb ---
dpkg-deb --build --root-owner-group "$BUILDDIR"

OUTFILE="$(dirname "$0")/selfcontrol-linux_${VERSION}_all.deb"
mv "$BUILDDIR.deb" "$OUTFILE"
echo "Built: $OUTFILE"
