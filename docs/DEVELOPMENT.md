# Development

## Layout

```
wallpaper-sh/
├── bin/wallpaper-sh.py          the script: search, download, validate, apply
├── app/
│   ├── main.py                  PySide6 backend (Backend QObject + image providers)
│   ├── qml/                     UI: Main.qml shell, one *Page.qml per nav item, small components
│   ├── icon.svg, icon-32.png    app icon (generated, see below)
├── systemd/                     wallpaper-sh.service (oneshot) + wallpaper-sh.timer
├── desktop/                     launcher template (@APP_DIR@ is filled in by install.sh)
├── icons/hicolor/               themed icon sizes for the launcher
├── scripts/setup-login-screen.sh   one-time root setup for the login screen
├── tools/make_icon.py           pixel-art icon generator
├── install.sh, uninstall.sh
└── docs/
```

## How the pieces talk

- **The script is the single source of truth.** `app/main.py` imports `wallpaper-sh.py` as a
  module (`load_script()`) to read its defaults and paths (`CATEGORIES`, `WALLPAPER_DIR`,
  `CONFIG_FILE`, ...). It never reimplements them.
- **Settings go through `config.json`.** The app writes it, and the script reads it at start
  (`load_config()`), overriding its module constants through `CONFIG_KEYS`. The built-in
  themes live in `PRESETS` in `main.py`. *Formula 1* is the script's own `CATEGORIES`.
- **Changes are made by running the script.** "New image", prompts and re-apply all run the
  script as a subprocess (`Backend._run`). The app parses its `INFO`/`ERROR` log lines for the
  status text and error toasts.
- **The schedule is a systemd drop-in.** The app writes `wallpaper-sh.timer.d/app-schedule.conf`
  and restarts the timer. The shipped `wallpaper-sh.timer` stays untouched.
- **The timer lives in the graphical session** (`WantedBy`/`PartOf=graphical-session.target`),
  not in `timers.target`. At boot the user manager can start briefly before login. A timer in
  `timers.target` would fire its catch-up run there, get killed when that manager exits, and
  still count as "ran today".
- **A run lock** (`~/.local/state/wallpaper-sh/run.lock`, `flock`) keeps the timer and the
  app from overlapping.

How the script applies an image:

| Target | Method |
|---|---|
| Desktop | `org.kde.PlasmaShell.evaluateScript` over D-Bus (`gdbus`, then `qdbus*`). This sets the image and fill mode on every monitor (or only the primary one). Falls back to `plasma-apply-wallpaperimage`. Waits for plasmashell to export the method first. |
| Lock screen | `kwriteconfig6 --file kscreenlockerrc`. The greeter rereads it at every lock. |
| Login screen | re-encode to JPEG and atomically replace `/usr/local/share/wallpapers/wallpaper-sh/login.jpg` |

Only the desktop can fail a run. The lock and login screens are best effort.

## Running from a checkout

The simplest way is to install with symlinks, so the menu launcher, the timer and the app
all use your checkout:

```bash
./install.sh --dev
```

The systemd units are the one exception: they're always copied. systemd treats a
symlinked unit as "linked", and disabling it (schedule *Off* in the app) would delete the
symlink. After editing `systemd/*`, run `./install.sh --dev` again.

Or run the pieces directly without installing:

```bash
python3 bin/wallpaper-sh.py --query "nebula"            # script only
WALLPAPER_SH_SCRIPT=$PWD/bin/wallpaper-sh.py \
QT_FORCE_STDERR_LOGGING=1 python3 app/main.py           # app using this checkout's script
```

`WALLPAPER_SH_SCRIPT` tells the app which script to import and run. It defaults to
`~/.local/bin/wallpaper-sh.py`.

Both use your real config, state and wallpaper. To experiment without touching them, point
the XDG dirs somewhere else:

```bash
XDG_CONFIG_HOME=/tmp/wsh/config XDG_STATE_HOME=/tmp/wsh/state python3 app/main.py
```

(Images still go to `~/Pictures/wallpaper-sh`, applying still changes the real desktop, and
saving a schedule still edits the real timer drop-in.)

### QML tips

- Run the app on your real Wayland session. The `offscreen` platform has no GPU, and
  `MultiEffect`-based images render blank there.
- `QT_FORCE_STDERR_LOGGING=1` prints QML warnings and errors to the terminal.
- Colours, radii and fonts live in `qml/Theme.qml` (a singleton that switches with the dark
  and light appearance). Stroke icons come from `image://icon/<name>/<hex colour>`, defined
  in `ICONS` in `main.py`.

## Checks

There's no test suite yet. Before sending a change:

```bash
python3 -m py_compile bin/wallpaper-sh.py app/main.py
bash -n install.sh uninstall.sh scripts/setup-login-screen.sh
python3 bin/wallpaper-sh.py && journalctl --user -n 20   # a real end-to-end run
```

Then click through every page of the app in both appearances.

## The icon

The icon is a 32×32 pixel-art painter, drawn in code:

```bash
python3 tools/make_icon.py app/      # writes icon-32.png, icon.svg, icon-preview.png
```

`icons/hicolor/` holds the scaled copies used by the launcher. Regenerate them after changing
the icon (nearest-neighbour scaling for 32 px and up keeps the pixels crisp).

## Releasing

1. Bump `APP_VERSION` in `app/main.py` and the version in the script's `USER_AGENT`.
2. Add an entry to `CHANGELOG.md`.
3. Tag the release: `git tag vX.Y.Z && git push --tags`.
