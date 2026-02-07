APP_ID = "com.github.selfcontrol"

DBUS_NAME = "com.github.selfcontrol"
DBUS_PATH = "/com/github/selfcontrol"
DBUS_INTERFACE = "com.github.selfcontrol"

STATE_DIR = "/var/lib/selfcontrol-linux"
STATE_FILE = STATE_DIR + "/state.json"
BLOCKLIST_FILE = STATE_DIR + "/blocklist.json"

HOSTS_FILE = "/etc/hosts"
HOSTS_MARKER_BEGIN = "# BEGIN SELFCONTROL BLOCK"
HOSTS_MARKER_END = "# END SELFCONTROL BLOCK"

NFTABLES_TABLE_NAME = "selfcontrol"

DEFAULT_BLOCKLIST = [
    "facebook.com",
    "twitter.com",
    "instagram.com",
    "reddit.com",
    "youtube.com",
]
