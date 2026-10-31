#!/usr/bin/env bash
# Remove wallpaper.sh for the current user.
#
#   ./uninstall.sh           remove the script, app, launcher, icons and timer
#   ./uninstall.sh --purge   also delete settings, state and downloaded images
#
# The current wallpaper stays on screen. The login screen config (root-owned)
# is left alone; see docs/INSTALL.md to revert it.
set -euo pipefail

CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}"
STATE="${XDG_STATE_HOME:-$HOME/.local/state}"

purge=0
case "${1:-}" in
    "") ;;
    --purge) purge=1 ;;
    -h|--help) sed -n '2,8p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
esac

systemctl --user disable --now wallpaper-sh.timer 2>/dev/null || true
rm -rf "$CONFIG/systemd/user/wallpaper-sh.service" \
       "$CONFIG/systemd/user/wallpaper-sh.timer" \
       "$CONFIG/systemd/user/wallpaper-sh.timer.d"
systemctl --user daemon-reload

rm -rf "$HOME/.local/bin/wallpaper-sh.py" \
       "$HOME/.local/share/wallpaper-sh" \
       "$HOME/.local/share/applications/wallpaper-sh.desktop" \
       "$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")/wallpaper-sh.desktop"
find "$HOME/.local/share/icons/hicolor" -name 'wallpaper-sh.*' -path '*/apps/*' -delete 2>/dev/null || true

if (( purge )); then
    rm -rf "$CONFIG/wallpaper-sh" "$STATE/wallpaper-sh" "$HOME/Pictures/wallpaper-sh"
    echo "Removed wallpaper.sh, its settings and downloaded images."
else
    echo "Removed wallpaper.sh. Kept settings ($CONFIG/wallpaper-sh) and images (~/Pictures/wallpaper-sh)."
fi
