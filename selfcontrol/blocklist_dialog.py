import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gtk


class BlocklistDialog(Adw.Dialog):
    def __init__(self, client):
        super().__init__(title="Edit Blocklist", content_width=400, content_height=450)

        self._client = client
        self._domains = []

        # Header bar with Cancel/Save
        header = Adw.HeaderBar()
        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.connect("clicked", lambda b: self.close())
        header.pack_start(cancel_btn)

        save_btn = Gtk.Button(label="Save")
        save_btn.add_css_class("suggested-action")
        save_btn.connect("clicked", self._on_save)
        header.pack_end(save_btn)

        # Main content
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content_box.set_margin_top(12)
        content_box.set_margin_bottom(12)
        content_box.set_margin_start(12)
        content_box.set_margin_end(12)

        # Add domain row
        add_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self._entry = Gtk.Entry()
        self._entry.set_placeholder_text("example.com")
        self._entry.set_hexpand(True)
        self._entry.connect("activate", self._on_add)
        add_box.append(self._entry)

        add_btn = Gtk.Button(label="Add")
        add_btn.connect("clicked", self._on_add)
        add_box.append(add_btn)

        content_box.append(add_box)

        # Scrollable domain list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self._list_box = Gtk.ListBox()
        self._list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self._list_box.add_css_class("boxed-list")
        scrolled.set_child(self._list_box)
        content_box.append(scrolled)

        # Toolbar view to combine header + content
        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(header)
        toolbar.set_content(content_box)
        self.set_child(toolbar)

        # Load current blocklist
        self._load_blocklist()

    def _load_blocklist(self):
        try:
            self._domains = self._client.get_blocklist()
        except Exception:
            self._domains = []
        self._rebuild_list()

    def _rebuild_list(self):
        # Remove all rows
        while True:
            row = self._list_box.get_row_at_index(0)
            if row is None:
                break
            self._list_box.remove(row)

        for domain in self._domains:
            row = self._make_row(domain)
            self._list_box.append(row)

    def _make_row(self, domain):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        box.set_margin_start(12)
        box.set_margin_end(6)

        label = Gtk.Label(label=domain)
        label.set_hexpand(True)
        label.set_xalign(0)
        box.append(label)

        remove_btn = Gtk.Button(icon_name="user-trash-symbolic")
        remove_btn.add_css_class("flat")
        remove_btn.connect("clicked", self._on_remove, domain)
        box.append(remove_btn)

        return box

    def _on_add(self, widget):
        text = self._entry.get_text().strip().lower()
        if not text or text in self._domains:
            return

        # Strip common prefixes
        for prefix in ("https://", "http://", "www."):
            if text.startswith(prefix):
                text = text[len(prefix):]
        text = text.rstrip("/")

        if not text or text in self._domains:
            return

        self._domains.append(text)
        self._list_box.append(self._make_row(text))
        self._entry.set_text("")

    def _on_remove(self, btn, domain):
        if domain in self._domains:
            self._domains.remove(domain)
        self._rebuild_list()

    def _on_save(self, btn):
        try:
            self._client.set_blocklist(self._domains)
        except Exception:
            pass
        self.close()
