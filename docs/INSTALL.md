# Installation

wallpaper.sh installs per user into `~/.local` and needs no root, except for the optional
login screen step.

## 1. Dependencies

The script needs Python 3.10+ with `requests` and `Pillow`. The app also needs PySide6 6.5
or newer. Plasma 6 already ships `gdbus`, `kwriteconfig6` and `plasma-apply-wallpaperimage`.

**Fedora, Nobara**

```bash
sudo dnf install python3-requests python3-pillow python3-pyside6
```

**Arch, EndeavourOS, CachyOS**

```bash
sudo pacman -S python-requests python-pillow pyside6
```

**openSUSE Tumbleweed**

```bash
sudo zypper install python3-requests python3-Pillow python3-pyside6
```

**Debian, Ubuntu, KDE neon** (package names vary between releases)

```bash
sudo apt install python3-requests python3-pil python3-pyside6.qtquick python3-pyside6.qtquickcontrols2 python3-pyside6.qtsvg
```

**Anything else**: install `PySide6`, `requests` and `pillow` from pip.

```bash
python3 -m pip install --user PySide6 requests pillow
```

> Only Fedora/Nobara has been tested. Package names for other distros are best effort,
> so please open an issue if one is wrong.

## 2. Install

```bash
git clone https://github.com/SerhiiKlymchuk/wallpaper.sh.git
cd wallpaper.sh
./install.sh
```

The installer:

| What | Where |
|---|---|
| script | `~/.local/bin/wallpaper-sh.py` |
| app (main.py, QML, icon) | `~/.local/share/wallpaper-sh/` |
| launcher | `~/.local/share/applications/wallpaper-sh.desktop` |
| icons | `~/.local/share/icons/hicolor/*/apps/wallpaper-sh.*` |
| systemd units | `~/.config/systemd/user/wallpaper-sh.{service,timer}` |

It also enables `wallpaper-sh.timer`. The first wallpaper arrives at the next scheduled time
(by default a random time between 08:30 and 09:00, until you set your own schedule in the app). Run `systemctl --user start wallpaper-sh.service` to get one now.

Options:

| Option | Effect |
|---|---|
| `--desktop-shortcut` | also put a launcher on your desktop |
| `--dev` | symlink the files instead of copying them, so edits in the checkout apply straight away (systemd units are still copied; see [DEVELOPMENT.md](DEVELOPMENT.md)) |

Running `./install.sh` again updates an existing install. Your settings, history, images and
the schedule you set in the app are kept.

## 3. Login screen (optional)

The login screen (Plasma Login Manager) runs as its own `plasmalogin` user and can't read your
home folder. The one-time setup:

1. creates `/usr/local/share/wallpapers/wallpaper-sh/`, owned by you and readable by everyone
2. backs up `/etc/plasmalogin.conf` to `/etc/plasmalogin.conf.bak-<date>`
3. points the greeter at `/usr/local/share/wallpapers/wallpaper-sh/login.jpg`

```bash
sudo ./scripts/setup-login-screen.sh
```

From then on every new wallpaper is also copied there. You'll see it on the next boot or logout.

> If you later change the login screen wallpaper in System Settings, that replaces this
> setting. Run the setup script again to restore it.
>
> SDDM isn't supported yet. The app's About page shows which login manager you're running.

## 4. Optional: wallhaven API key

Anonymous access is enough. If you have a wallhaven account and want requests to use your key:

```bash
mkdir -p ~/.config/wallpaper-sh
echo 'WALLHAVEN_API_KEY=your-key-here' > ~/.config/wallpaper-sh/env
chmod 600 ~/.config/wallpaper-sh/env
```

The service reads this file. The app passes the key on when it runs the script itself.

## Uninstall

```bash
./uninstall.sh            # keeps settings and downloaded images
./uninstall.sh --purge    # removes those too
```

To put the old login screen back, restore the backup the setup script made:

```bash
sudo cp /etc/plasmalogin.conf.bak-<date> /etc/plasmalogin.conf
```

You can also choose another login wallpaper in *System Settings → Login Screen*. Delete
`/usr/local/share/wallpapers/wallpaper-sh/` if you want it gone.
