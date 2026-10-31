# Configuration

You'll rarely need this file: the app writes everything below for you. It's for editing by
hand, scripting, or understanding what the app does.

## Files

| Path | What |
|---|---|
| `~/.config/wallpaper-sh/config.json` | settings and themes (written by the app) |
| `~/.config/wallpaper-sh/env` | optional `WALLHAVEN_API_KEY=...` |
| `~/.config/systemd/user/wallpaper-sh.timer.d/app-schedule.conf` | schedule set in the app |
| `~/.local/state/wallpaper-sh/history.json` | wallhaven ids already shown (never repeated) |
| `~/.local/state/wallpaper-sh/current.json` | what's on screen now |
| `~/Pictures/wallpaper-sh/` | downloaded images, named `YYYY-MM-DD_<category>_<wallhaven id>.jpg` |
| `/usr/local/share/wallpapers/wallpaper-sh/login.jpg` | copy for the login screen |

`XDG_CONFIG_HOME` and `XDG_STATE_HOME` are respected.

## config.json

```jsonc
{
  "active_theme": "formula_1",       // id of a theme below
  "appearance": "dark",              // app look: "dark" | "light"
  "apply_desktop": true,
  "apply_lock_screen": true,
  "apply_login_screen": true,
  "all_monitors": true,              // false -> only the primary screen changes
  "keep_files": 40,                  // newest N images kept in ~/Pictures/wallpaper-sh
  "schedule": { "mode": "daily", "every": 3, "time": "08:30", "day": "Mon" },
  "themes": {
    "formula_1": {
      "label": "Formula 1",
      "content": ["general"],        // any of "general", "anime", "people"
      "fallback_queries": ["id:922", "formula 1"],
      "categories": {
        "ferrari": {
          "weight": 20,              // relative chance; weights don't need to add up to 100
          "sorting": "relevance",    // "relevance" | "date_added" | "toplist"
          "queries": ["ferrari formula 1", "scuderia ferrari", "charles leclerc"]
        },
        "current_season": {
          "weight": 10,
          "sorting": "date_added",
          "max_pages": 4,            // only look at the newest 4 pages (~96 images)
          "queries": ["id:922"]
        }
      }
    }
  }
}
```

How a run works:

1. Pick a category of the active theme at random, weighted by `weight`.
2. Try its `queries` in random order and pool the usable candidates.
3. Choose one at random, preferring images at least 2560 px wide.
4. If the category yields nothing, use `fallback_queries`. If a theme has none, its first
   six queries are used.

Categories with zero weight or no queries are skipped. The `schedule` key only stores what
the app's Schedule page shows. The timer drop-in is what actually decides when runs happen.

A missing key falls back to the script's default. Deleting `config.json` resets everything
(the app recreates the built-in themes the next time it starts).

## Writing good queries

- wallhaven matches the words of a query against image **tags** (all words must match). Short,
  tag-like queries work much better than sentences: `misty forest` works, but
  `a beautiful misty forest at dawn` doesn't.
- `id:<tag id>` searches one exact tag. For example, `id:922` is the curated *Formula 1* tag.
  The id is in the tag's URL on wallhaven.
- `sorting: "date_added"` with a small `max_pages` means "recent uploads only". It's good for
  "current season" style categories.
- `sorting: "toplist"` favours highly rated images. It suits broad topics like `nebula`
  or `abstract`.

## Built-in filters

These are constants at the top of `bin/wallpaper-sh.py`, not config keys:

| Constant | Default | Meaning |
|---|---|---|
| `MIN_WIDTH`, `MIN_HEIGHT` | 1920 × 1080 | hard minimum resolution |
| `PREFER_WIDTH` | 2560 | prefer images at least this wide when available |
| `MIN_ASPECT`, `MAX_ASPECT` | 1.50 – 2.60 | landscape only, no ultra-wide panoramas |
| `MIN_BYTES`, `MAX_BYTES` | 150 KiB – 30 MiB | rejects thumbnails and huge files |
| `FILL_MODE` | 2 | Plasma fill mode: scaled and cropped |
| `PLASMA_WAIT_SECONDS` | 180 | how long to wait for Plasma after login |
| `NETWORK_WAIT_SECONDS` | 300 | how long to wait for the network |

Purity is always SFW, and wallhaven's server-side landscape filter is always on.
