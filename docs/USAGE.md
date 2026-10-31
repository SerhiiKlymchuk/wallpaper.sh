# Usage

## The app

Open **wallpaper.sh** from the application menu, or run `python3 ~/.local/share/wallpaper-sh/main.py`.

| Page | What it does |
|---|---|
| **Now** | The current wallpaper. **New image** fetches a fresh one from the active theme. The search bar at the top (**Find**) fetches an image for any prompt. *Shows on* toggles desktop, lock screen and login screen; **Re-apply** applies the current image again, e.g. after you change those toggles. Click a *Recent* thumbnail to preview and apply it. |
| **Gallery** | Every downloaded image, filterable by category. Apply, delete or open any image on wallhaven. **Open folder** opens `~/Pictures/wallpaper-sh`. |
| **Themes** | Pick the active theme or create, rename and delete your own. Each theme has a content filter (general / anime / people) and a list of categories, each with a weight, a sort order and its search queries. **Reset to defaults** restores a built-in theme. |
| **Schedule** | Off, every 1-12 hours, daily at a time, or weekly on a day. Also: how many images to keep and whether the desktop changes on all monitors. Shows the next and last change. |
| **About** | Versions and a checklist of what your system supports (Plasma 6, lock screen, login screen, timer, PySide6). |

The sun/moon button in the top right switches between dark and light appearance.

## Command line

The script works on its own, without the app:

```bash
wallpaper-sh.py                      # weighted-random category of the active theme
wallpaper-sh.py --query "senna"      # one-off search for a prompt
wallpaper-sh.py --apply FILE         # re-apply an already downloaded image
```

`~/.local/bin` is on `PATH` in most distros. If it isn't, call it by its full path.

Through systemd, the same way the timer runs it:

```bash
systemctl --user start wallpaper-sh.service      # new wallpaper now
systemctl --user list-timers wallpaper-sh.timer  # when is the next change?
systemctl --user disable --now wallpaper-sh.timer   # pause automatic changes
systemctl --user enable --now wallpaper-sh.timer    # resume
```

The app and the timer never run at the same time: a lock file makes a second run exit with
code 75.

## Logs

```bash
journalctl --user -u wallpaper-sh.service -n 30 --no-pager
```

A successful run looks like this:

```
INFO Category: classic (58 already in history)
INFO Pooled 26 candidates from 4/8 queries
INFO Saved 2026-10-04_classic_p9ol7m.jpg (3004x1689, 0.7 MiB)
INFO Wallpaper applied via gdbus
INFO Lock screen updated (takes effect at the next lock)
INFO Login screen updated (takes effect at the next boot/logout)
INFO Done: https://wallhaven.cc/w/p9ol7m
```

## Troubleshooting

**An image was downloaded but the wallpaper didn't change**

Check the log:

- `Could not talk to Plasma`: the script needs the desktop shell running in your session.
  After login it waits up to 3 minutes for Plasma to finish starting (`PLASMA_WAIT_SECONDS`).
  On very slow logins, raise that value in the script.
- `code=killed, status=15/TERM` right after boot: the run was started outside your graphical
  session, before you logged in. Check that the timer is tied to the session:
  `systemctl --user show wallpaper-sh.timer -p WantedBy` should print
  `graphical-session.target`. If it doesn't, run `./install.sh` again.

**`Temporary failure in name resolution` right after boot**

This is harmless. The network wasn't up yet, and the script retries for up to 5 minutes.

**The lock screen still shows the old image**

The lock screen reads its config each time it starts, so the change appears at the next lock.

**The login screen didn't change**

- Run `sudo ./scripts/setup-login-screen.sh` once (see [INSTALL.md](INSTALL.md)).
- Check that the app's About page reports *plasmalogin · ready*.
- If you changed the login wallpaper in System Settings, run the setup script again.

**No usable wallpaper found**

Every query in the chosen category returned nothing new, large enough and landscape. Use
shorter, tag-like queries (see [CONFIGURATION.md](CONFIGURATION.md#writing-good-queries)) or add
more queries. The script then falls back to the theme's fallback pool.

**The app doesn't start**

Run it from a terminal to see the error:

```bash
QT_FORCE_STDERR_LOGGING=1 python3 ~/.local/share/wallpaper-sh/main.py
```

A `ModuleNotFoundError: PySide6` means the app dependency is missing (see [INSTALL.md](INSTALL.md)).
