import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gtk

from selfcontrol.blocklist_dialog import BlocklistDialog
from selfcontrol.client import SelfControlClient


def format_duration(hours):
    h = int(hours)
    m = int((hours - h) * 60)
    if h == 0:
        return f"{m} minutes"
    elif m == 0:
        if h == 1:
            return "1 hour"
        return f"{h} hours"
    else:
        if h == 1:
            return f"1 hour {m} min"
        return f"{h} hours {m} min"


def format_countdown(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h}:{m:02d}:{s:02d}"


def blocklist_summary(domains):
    if not domains:
        return "No sites in blocklist"
    if len(domains) == 1:
        return f"Blocking {domains[0]}"
    if len(domains) == 2:
        return f"Blocking {domains[0]} and {domains[1]}"
    others = len(domains) - 2
    return f"Blocking {domains[0]} and {others} {'other' if others == 1 else 'others'}"


class SelfControlWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="SelfControl", default_width=480, default_height=340, resizable=False)

        self._client = None
        self._blocking = False

        # Header bar
        header = Adw.HeaderBar()
        title_label = Gtk.Label(label="SelfControl")
        title_label.add_css_class("title")
        header.set_title_widget(title_label)

        # Main content area
        self._content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._content_box.set_vexpand(True)

        # -- Idle view --
        self._idle_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._idle_box.set_vexpand(True)

        # Start Block button area
        btn_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        btn_box.set_margin_top(24)
        btn_box.set_margin_bottom(20)
        self._start_btn = Gtk.Button(label="Start Block")
        self._start_btn.add_css_class("suggested-action")
        self._start_btn.add_css_class("pill")
        self._start_btn.add_css_class("start-block-button")
        self._start_btn.set_halign(Gtk.Align.CENTER)
        self._start_btn.connect("clicked", self._on_start_clicked)
        btn_box.append(self._start_btn)
        self._idle_box.append(btn_box)

        # Duration + slider in a clamp for nice width
        slider_clamp = Adw.Clamp(maximum_size=420)
        slider_clamp.set_margin_start(24)
        slider_clamp.set_margin_end(24)
        slider_inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        self._duration_label = Gtk.Label(label="1 hour")
        self._duration_label.add_css_class("duration-label")
        self._duration_label.set_xalign(0)
        slider_inner.append(self._duration_label)

        self._scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.25, 24.0, 0.25)
        self._scale.set_value(1.0)
        self._scale.set_draw_value(False)
        self._scale.set_hexpand(True)
        self._scale.connect("value-changed", self._on_scale_changed)
        slider_inner.append(self._scale)

        slider_clamp.set_child(slider_inner)
        self._idle_box.append(slider_clamp)

        # Spacer to push bottom bar down
        spacer = Gtk.Box()
        spacer.set_vexpand(True)
        self._idle_box.append(spacer)

        self._content_box.append(self._idle_box)

        # -- Blocking view (hidden initially) --
        self._blocking_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self._blocking_box.set_vexpand(True)
        self._blocking_box.set_valign(Gtk.Align.CENTER)
        self._blocking_box.set_visible(False)

        self._skull_label = Gtk.Label(label="\u2620")
        self._skull_label.add_css_class("skull-icon")
        self._skull_label.set_halign(Gtk.Align.CENTER)
        self._blocking_box.append(self._skull_label)

        self._countdown_label = Gtk.Label(label="0:00:00")
        self._countdown_label.add_css_class("countdown-label")
        self._countdown_label.set_halign(Gtk.Align.CENTER)
        self._blocking_box.append(self._countdown_label)

        self._content_box.append(self._blocking_box)

        # -- Bottom bar --
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self._content_box.append(separator)

        bottom_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        bottom_bar.set_margin_top(12)
        bottom_bar.set_margin_bottom(12)
        bottom_bar.set_margin_start(20)
        bottom_bar.set_margin_end(20)

        self._summary_label = Gtk.Label(label="")
        self._summary_label.add_css_class("summary-label")
        self._summary_label.set_xalign(0)
        self._summary_label.set_hexpand(True)
        self._summary_label.set_ellipsize(3)  # PANGO_ELLIPSIZE_END
        bottom_bar.append(self._summary_label)

        self._edit_btn = Gtk.Button(label="Edit Blocklist")
        self._edit_btn.add_css_class("flat")
        self._edit_btn.connect("clicked", self._on_edit_clicked)
        bottom_bar.append(self._edit_btn)

        self._content_box.append(bottom_bar)

        # Assemble
        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(header)
        toolbar.set_content(self._content_box)
        self.set_content(toolbar)

        # Connect to daemon
        self._connect_daemon()

    def _connect_daemon(self):
        try:
            self._client = SelfControlClient()
            self._client.connect_tick_signal(self._on_timer_tick)
            self._refresh_status()
        except Exception as e:
            self._summary_label.set_label(f"Cannot connect to daemon: {e}")

    def _refresh_status(self):
        if not self._client:
            return

        try:
            status = self._client.get_status()
        except Exception:
            return

        if status["active"]:
            self._set_blocking_mode(status["remaining"])
        else:
            self._set_idle_mode()

        self._update_summary(status.get("blocklist", []))

    def _set_blocking_mode(self, remaining):
        self._blocking = True
        self._idle_box.set_visible(False)
        self._blocking_box.set_visible(True)
        self._countdown_label.set_label(format_countdown(remaining))
        self._edit_btn.set_sensitive(False)

    def _set_idle_mode(self):
        self._blocking = False
        self._idle_box.set_visible(True)
        self._blocking_box.set_visible(False)
        self._edit_btn.set_sensitive(True)

    def _update_summary(self, blocklist):
        self._summary_label.set_label(blocklist_summary(blocklist))

    def _on_scale_changed(self, scale):
        hours = scale.get_value()
        self._duration_label.set_label(format_duration(hours))

    def _on_start_clicked(self, btn):
        if not self._client or self._blocking:
            return

        hours = self._scale.get_value()
        duration_seconds = int(hours * 3600)

        try:
            success = self._client.start_block(duration_seconds)
            if success:
                self._set_blocking_mode(duration_seconds)
        except Exception as e:
            self._summary_label.set_label(f"Error: {e}")

    def _on_edit_clicked(self, btn):
        if not self._client or self._blocking:
            return

        dialog = BlocklistDialog(self._client)
        dialog.connect("closed", lambda d: self._refresh_status())
        dialog.present(self)

    def _on_timer_tick(self, remaining_seconds):
        remaining = int(remaining_seconds)
        if remaining <= 0:
            self._set_idle_mode()
            self._refresh_status()
        else:
            self._set_blocking_mode(remaining)
