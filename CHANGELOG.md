# Changelog

## 1.0.0 - 2026-10-31

First public release.

- `wallpaper-sh.py`: wallhaven search with weighted theme categories, image validation,
  no-repeat history, and applying to the desktop, lock screen and login screen.
- wallpaper.sh app (PySide6/QML): Now, Gallery, Themes, Schedule and About pages; prompt
  search; 8 built-in themes plus custom ones; dark and light appearance.
- systemd user timer with a schedule you can set in the app.
- The timer is tied to the graphical session. A missed run now catches up after you log
  in, instead of in the short-lived user manager that starts before login, where it was
  killed after downloading but before applying.
- After login, the script waits for Plasma to finish starting before applying.
