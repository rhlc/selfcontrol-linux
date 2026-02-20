Name:           selfcontrol-linux
Version:        %{version}
Release:        1%{?dist}
Summary:        Block distracting websites for a set duration
License:        GPLv3+
URL:            https://github.com/selfcontrol-linux/selfcontrol-linux
BuildArch:      noarch

Requires:       python3
Requires:       python3-gobject
Requires:       gtk4
Requires:       libadwaita
Requires:       python3-dbus
Requires:       nftables

%description
A port of the macOS SelfControl app. Blocks distracting websites via
DNS (/etc/hosts) and firewall (nftables) for a set duration. Once
started, blocks cannot be undone, even on reboot.

%install
rm -rf %{buildroot}

# Python packages
install -d %{buildroot}/usr/lib/selfcontrol-linux
cp -r %{srcdir}/selfcontrol %{buildroot}/usr/lib/selfcontrol-linux/
cp -r %{srcdir}/selfcontrol_daemon %{buildroot}/usr/lib/selfcontrol-linux/
cp -r %{srcdir}/data %{buildroot}/usr/lib/selfcontrol-linux/

# Launcher scripts
install -Dm755 %{srcdir}/bin/selfcontrol %{buildroot}/usr/bin/selfcontrol
install -Dm755 %{srcdir}/bin/selfcontrol-daemon %{buildroot}/usr/libexec/selfcontrol-daemon

# systemd service
install -Dm644 %{srcdir}/data/selfcontrol-daemon.service \
    %{buildroot}/usr/lib/systemd/system/selfcontrol-daemon.service

# D-Bus config
install -Dm644 %{srcdir}/data/com.github.selfcontrol.conf \
    %{buildroot}/usr/share/dbus-1/system.d/com.github.selfcontrol.conf
install -Dm644 %{srcdir}/data/com.github.selfcontrol.service \
    %{buildroot}/usr/share/dbus-1/system-services/com.github.selfcontrol.service

# Polkit policy
install -Dm644 %{srcdir}/data/com.github.selfcontrol.policy \
    %{buildroot}/usr/share/polkit-1/actions/com.github.selfcontrol.policy

# Desktop entry
install -Dm644 %{srcdir}/data/com.github.selfcontrol.desktop \
    %{buildroot}/usr/share/applications/com.github.selfcontrol.desktop

# State directory
install -d %{buildroot}/var/lib/selfcontrol-linux

%files
/usr/bin/selfcontrol
/usr/libexec/selfcontrol-daemon
/usr/lib/selfcontrol-linux/
/usr/lib/systemd/system/selfcontrol-daemon.service
/usr/share/dbus-1/system.d/com.github.selfcontrol.conf
/usr/share/dbus-1/system-services/com.github.selfcontrol.service
/usr/share/polkit-1/actions/com.github.selfcontrol.policy
/usr/share/applications/com.github.selfcontrol.desktop
%dir /var/lib/selfcontrol-linux

%post
systemctl daemon-reload
systemctl enable selfcontrol-daemon.service

%preun
if [ "$1" -eq 0 ]; then
    systemctl stop selfcontrol-daemon.service || true
    systemctl disable selfcontrol-daemon.service || true
fi

%postun
systemctl daemon-reload
