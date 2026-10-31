#!/usr/bin/env bash
# Install wallpaper.sh for the current user (no root needed).
#
#   ./install.sh                      copy files into ~/.local and enable the timer
#   ./install.sh --dev                symlink instead of copy, so edits in this
#                                     checkout take effect immediately (systemd
#                                     units are always copied: rerun after editing them)
#   ./install.sh --desktop-shortcut   also put a launcher on the desktop
#
# The login screen needs a separate one-time root step:
#   sudo ./scripts/setup-login-screen.sh
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$HOME/.local/bin"
APP_DIR="$HOME/.local/share/wallpaper-sh"
UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
APPS_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor"

dev=0
shortcut=0
for arg in "$@"; do
    case "$arg" in
        --dev) dev=1 ;;
        --desktop-shortcut) shortcut=1 ;;
        -h|--help) sed -n '2,11p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "Unknown option: $arg" >&2; exit 2 ;;
    esac
done

say()  { printf '\033[1;32m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33mwarning:\033[0m %s\n' "$*" >&2; }

# place SRC DST - copy, or symlink in --dev mode. Replaces whatever is at DST.
place() {
    mkdir -p "$(dirname "$2")"
    rm -rf "$2"
    if (( dev )); then ln -s "$1" "$2"; else cp -r "$1" "$2"; fi
}

say "Checking dependencies"
python3 - <<'EOF' || { warn "install the missing packages listed above (see docs/INSTALL.md)"; exit 1; }
import importlib.util, sys
missing = [m for m in ("requests", "PIL") if importlib.util.find_spec(m) is None]
if missing:
    print("  missing Python modules for the script:", ", ".join(missing))
    sys.exit(1)
if importlib.util.find_spec("PySide6") is None:
    print("  PySide6 not found: the timer will work, the desktop app will not start")
EOF
for cmd in plasmashell gdbus kwriteconfig6 systemctl; do
    command -v "$cmd" >/dev/null || warn "$cmd not found - see docs/INSTALL.md"
done

say "Installing the script to $BIN_DIR"
place "$REPO/bin/wallpaper-sh.py" "$BIN_DIR/wallpaper-sh.py"
chmod +x "$REPO/bin/wallpaper-sh.py"

say "Installing the app to $APP_DIR"
mkdir -p "$APP_DIR"
for item in main.py qml icon.svg icon-32.png; do
    place "$REPO/app/$item" "$APP_DIR/$item"
done

say "Installing the launcher and icons"
mkdir -p "$APPS_DIR"
sed "s|@APP_DIR@|$APP_DIR|g" "$REPO/desktop/wallpaper-sh.desktop.in" > "$APPS_DIR/wallpaper-sh.desktop"
for icon in "$REPO"/icons/hicolor/*/apps/wallpaper-sh.*; do
    rel="${icon#"$REPO/icons/hicolor/"}"
    place "$icon" "$ICON_DIR/$rel"
done
command -v gtk-update-icon-cache >/dev/null && gtk-update-icon-cache -q -t "$ICON_DIR" 2>/dev/null || true
command -v update-desktop-database >/dev/null && update-desktop-database -q "$APPS_DIR" 2>/dev/null || true

if (( shortcut )); then
    desktop_dir="$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")"
    mkdir -p "$desktop_dir"
    cp "$APPS_DIR/wallpaper-sh.desktop" "$desktop_dir/"
    chmod +x "$desktop_dir/wallpaper-sh.desktop"
fi

say "Installing and enabling the systemd user timer"
mkdir -p "$UNIT_DIR"
# Always copied, even with --dev: systemd treats a symlinked unit as "linked",
# and disabling it (e.g. schedule "Off" in the app) deletes the symlink itself.
for unit in wallpaper-sh.service wallpaper-sh.timer; do
    rm -f "$UNIT_DIR/$unit"
    cp "$REPO/systemd/$unit" "$UNIT_DIR/$unit"
done
systemctl --user daemon-reload
# reenable: drops a timers.target.wants link left by older installs
systemctl --user reenable wallpaper-sh.timer
systemctl --user start wallpaper-sh.timer

say "Done"
cat <<EOF

  Open the app:        wallpaper.sh in the application menu
                       (or: python3 $APP_DIR/main.py)
  New wallpaper now:   systemctl --user start wallpaper-sh.service
  Next scheduled run:  systemctl --user list-timers wallpaper-sh.timer

  Login screen (optional, one-time, needs root):
                       sudo $REPO/scripts/setup-login-screen.sh
EOF
