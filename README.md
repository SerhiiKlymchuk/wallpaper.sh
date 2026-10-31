<p align="center">
  <img src="icons/hicolor/128x128/apps/wallpaper-sh.png" width="96" alt="wallpaper.sh icon">
</p>

<h1 align="center">wallpaper.sh</h1>

<p align="center">
  A fresh wallpaper of the day for KDE Plasma 6: desktop, lock screen and login screen.
</p>

<p align="center">
  <img src="docs/images/screenshot.webp" alt="wallpaper.sh app, Now page" width="820">
</p>

---

wallpaper.sh picks a new landscape wallpaper from [wallhaven.cc](https://wallhaven.cc) on a
schedule and applies it everywhere you see a background on KDE Plasma. It's two small pieces:

- **`wallpaper-sh.py`**: a one-shot script run by a systemd user timer. It picks a weighted-random
  category from the active theme, searches wallhaven, rejects anything too small, too narrow or
  already shown, downloads and validates the image, applies it, and exits. There's no daemon.
- **The wallpaper.sh app**: a PySide6/QML desktop app on top of the script. It lets you browse
  what was downloaded, try a one-off prompt, edit themes and set the schedule.

## Features

- **Applies everywhere:** desktop (all monitors or just the primary one), lock screen, and
  the login screen (Plasma Login Manager).
- **Themes:** Formula 1, Nature, Space, Cities, Cars, Minimal, Happy little paintings and Anime
  are built in, and you can make your own. Each theme is a set of weighted categories of
  wallhaven searches.
- **Prompts:** type anything ("max verstappen", "misty forest") and get a matching image
  right now.
- **Gallery:** re-apply, delete or open any downloaded image on wallhaven. Old files are
  pruned automatically.
- **Schedule:** every few hours, daily at a time, or weekly. If the machine was off, the
  missed run happens at the next login, and it waits for Plasma to finish starting.
- **No repeats:** remembers what it has shown. SFW and landscape-only filters are on.
- **Dark and light appearance**, plus a 32px pixel-art icon of a painter at work on a
  happy little landscape.

## Quick start

```bash
# Fedora / Nobara
sudo dnf install python3-requests python3-pillow python3-pyside6

git clone https://github.com/SerhiiKlymchuk/wallpaper.sh.git
cd wallpaper.sh
./install.sh

# optional, one-time: let it change the login screen too
sudo ./scripts/setup-login-screen.sh
```

Then open **wallpaper.sh** from the application menu, or get a new wallpaper straight away:

```bash
systemctl --user start wallpaper-sh.service
```

## Requirements

| | |
|---|---|
| Desktop | KDE Plasma 6 (Wayland or X11), started through systemd (the default) |
| Login screen | Plasma Login Manager (optional; SDDM isn't supported yet) |
| Python | 3.10+ with `requests` and `Pillow` |
| App | PySide6 6.5+ (the timer works without it) |
| System | systemd user session, `gdbus`, `kwriteconfig6` |

## Documentation

- [Installation](docs/INSTALL.md): dependencies per distro, install options, login screen
  setup, uninstalling
- [Usage](docs/USAGE.md): the app, the command line, logs and troubleshooting
- [Configuration](docs/CONFIGURATION.md): `config.json`, themes and categories, wallhaven
  search tips, file locations
- [Development](docs/DEVELOPMENT.md): project layout, how the pieces talk, running from a
  checkout, the icon generator

## How it works

```
systemd timer ──► wallpaper-sh.py ──► wallhaven.cc API
                        │
                        ├─► Plasma desktop   (D-Bus: org.kde.PlasmaShell.evaluateScript)
                        ├─► lock screen      (kwriteconfig6 → kscreenlockerrc)
                        └─► login screen     (copy → /usr/local/share/wallpapers/wallpaper-sh/)

wallpaper.sh app ──► reads/writes ~/.config/wallpaper-sh/config.json
                 ├─► runs wallpaper-sh.py for "New image", prompts and re-apply
                 └─► manages the timer schedule (systemd drop-in)
```

## Credits

Images come from [wallhaven.cc](https://wallhaven.cc) and belong to their respective
authors. wallpaper.sh only downloads them for personal use as a background. Please respect
wallhaven's API rules and the image authors' rights.

## License

[MIT](LICENSE) © Serhii Klymchuk
