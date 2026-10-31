#!/usr/bin/env bash
# One-time root setup so wallpaper.sh can also change the login screen
# (Plasma Login Manager). The greeter runs as its own user and can't read
# $HOME, so each new image is copied to a world-readable folder owned by you,
# and /etc/plasmalogin.conf is pointed at it once.
#
# Run with: sudo ./scripts/setup-login-screen.sh
set -euo pipefail

owner="${SUDO_USER:?run this via sudo}"
dir=/usr/local/share/wallpapers/wallpaper-sh
conf=/etc/plasmalogin.conf

if [[ ! -f "$conf" ]]; then
    echo "$conf not found - only Plasma Login Manager is supported." >&2
    exit 1
fi

install -d -m 755 -o "$owner" -g "$owner" "$dir"

cp -a "$conf" "$conf.bak-$(date +%F)"
kwriteconfig6 --file "$conf" --group Greeter --key WallpaperPluginId org.kde.image
kwriteconfig6 --file "$conf" --group Greeter --group Wallpaper --group org.kde.image --group General \
    --key Image "file://$dir/login.jpg"
kwriteconfig6 --file "$conf" --group Greeter --group Wallpaper --group org.kde.image --group General \
    --key FillMode 2

echo "Done. $conf now:"
cat "$conf"
