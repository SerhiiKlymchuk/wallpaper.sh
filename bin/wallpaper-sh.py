#!/usr/bin/env python3
"""
wallpaper.sh - a themed "picture of the day" wallpaper for KDE Plasma.

Runs once (from a systemd --user timer), picks a weighted-random category of
the active theme, downloads a fresh landscape wallpaper from wallhaven.cc,
validates it, and applies it to the Plasma desktop, lock screen and login
screen. Exits immediately afterwards - no daemon.

  wallpaper-sh.py                  weighted-random category (the timer's run)
  wallpaper-sh.py --query "senna"  one-off search for a custom prompt
  wallpaper-sh.py --apply FILE     re-apply an already downloaded image

Settings in CONFIG_FILE (written by the wallpaper.sh app) override the
defaults below.

Deps: python3-requests, python3-pillow
"""

from __future__ import annotations

import argparse
import fcntl
import json
import logging
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import requests
from PIL import Image, ImageFile
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ---------------------------------------------------------------------------
# CONFIGURATION - everything you are likely to change lives in this block.
# ---------------------------------------------------------------------------

# Weights are relative: they do NOT have to add up to 100.
# Change a single number (e.g. verstappen 10 -> 40) and nothing else breaks.
#
# "queries"  - wallhaven search strings, tried in random order until one yields
#              usable candidates.
# "sorting"  - wallhaven sort order for this category.
#              "relevance" = best keyword match, "date_added" = newest uploads,
#              "toplist"   = highest rated.
# "max_pages"- only look at the first N result pages (24 items each).
#              Used with "date_added" to mean "recent uploads only".
#
# Note on wallhaven queries: multiple words are ANDed against an image's tags,
# so short, tag-like queries work far better than sentences.
# "id:922" is wallhaven's tag id for the curated "Formula 1" tag - it is the
# most reliable pure-F1 pool on the site (~660 landscape images >=1920x1080).

CATEGORIES: dict[str, dict] = {
    "verstappen": {
        "weight": 10,
        "sorting": "relevance",
        "queries": [
            "max verstappen",
            "verstappen red bull",
            "red bull racing formula 1",
            "red bull rb19",
        ],
    },
    "ferrari": {
        "weight": 10,
        "sorting": "relevance",
        "queries": [
            "ferrari formula 1",
            "scuderia ferrari",
            "ferrari f1 car",
            "charles leclerc",
        ],
    },
    "current_season": {
        # Wallhaven has very few images literally tagged "2026", so the reliable
        # way to get current-season content is "newest F1 uploads" instead.
        "weight": 10,
        "sorting": "date_added",
        "max_pages": 4,           # ~96 most recently uploaded F1 wallpapers
        "queries": [
            "id:922",             # the "Formula 1" tag
            "formula 1 2026",
            "formula 1 2025",
        ],
    },
    "classic": {
        "weight": 60,
        "sorting": "relevance",
        "queries": [
            "ayrton senna",
            "michael schumacher",
            "niki lauda",
            "jackie stewart",
            "gilles villeneuve",
            "james hunt",
            "alain prost",
            "nigel mansell",
            "nelson piquet",
            "emerson fittipaldi",
            "lotus formula 1",
            "mclaren formula 1",
            "williams formula 1",
            "brabham",
            "tyrrell",
            "formula 1 retro",
            "vintage racing car",
            "classic formula 1",
            "historic grand prix",
        ],
    },
    "circuits": {
        "weight": 10,
        "sorting": "toplist",
        "queries": [
            "formula 1 circuit",
            "formula 1 night race",
            "monaco grand prix",
            "suzuka circuit",
            "spa francorchamps",
            "formula 1 rain",
            "formula 1 grid",
        ],
    },
}

# Fallback pool used when the chosen category returns nothing usable.
FALLBACK_QUERIES = ["id:922", "formula 1"]

# How many of a category's queries to pool together in one run, and how many
# to try before giving up (queries that return nothing are cheap but not free).
POOL_QUERIES = 4
MAX_QUERY_ATTEMPTS = 8

# --- image requirements ----------------------------------------------------
MIN_WIDTH, MIN_HEIGHT = 1920, 1080   # hard minimum
PREFER_WIDTH = 2560                  # prefer >=1440p / 4K when available
MIN_ASPECT = 1.50                    # reject anything not clearly landscape
MAX_ASPECT = 2.60                    # reject ultra-wide panoramas
MIN_BYTES = 150 * 1024               # reject thumbnails / over-compressed junk
MAX_BYTES = 30 * 1024 * 1024
ALLOWED_TYPES = {"image/jpeg", "image/png"}

# --- KDE -------------------------------------------------------------------
# Plasma fill mode (QML Image.fillMode):
#   0 Stretch, 1 Scaled(keep proportions), 2 Scaled&Cropped, 3 Tiled, 6 Centered
# 2 is the right choice for a 16:9 monitor.
FILL_MODE = 2
ALL_MONITORS = True                  # False -> only the primary screen changes
# After boot the timer can fire before plasmashell has exported its scripting
# API; wait this long for it instead of failing the run.
PLASMA_WAIT_SECONDS = 180
ALSO_LOCK_SCREEN = True              # also update the lock screen wallpaper
ALSO_LOGIN_SCREEN = True             # also update the login (greeter) wallpaper
# The greeter runs as the "plasmalogin" user and can't read $HOME, so the image
# is copied to a world-readable path that /etc/plasmalogin.conf points at.
# One-time root setup: mkdir this dir, chown it to the user, edit that config.
LOGIN_WALLPAPER = Path("/usr/local/share/wallpapers/wallpaper-sh/login.jpg")

# --- storage ---------------------------------------------------------------
WALLPAPER_DIR = Path.home() / "Pictures" / "wallpaper-sh"
STATE_DIR = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "wallpaper-sh"
HISTORY_FILE = STATE_DIR / "history.json"
KEEP_FILES = 40                      # how many downloaded wallpapers to keep

# --- network ---------------------------------------------------------------
API = "https://wallhaven.cc/api/v1/search"
API_TIMEOUT = (10, 30)               # (connect, read)
DL_TIMEOUT = (10, 120)
NETWORK_WAIT_SECONDS = 300           # keep retrying this long if offline
USER_AGENT = "wallpaper-sh/1.0 (+https://github.com/SerhiiKlymchuk/wallpaper.sh)"

# --- app integration -------------------------------------------------------
CONFIG_FILE = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "wallpaper-sh" / "config.json"
CURRENT_FILE = STATE_DIR / "current.json"   # what is on screen right now
LOCK_FILE = STATE_DIR / "run.lock"          # timer and app must not overlap

# config.json key -> module setting it overrides
CONFIG_KEYS = {
    "categories": "CATEGORIES",
    "fallback_queries": "FALLBACK_QUERIES",
    "all_monitors": "ALL_MONITORS",
    "apply_desktop": "ALSO_DESKTOP",
    "apply_lock_screen": "ALSO_LOCK_SCREEN",
    "apply_login_screen": "ALSO_LOGIN_SCREEN",
    "keep_files": "KEEP_FILES",
}
ALSO_DESKTOP = True
CONTENT = "100"             # wallhaven content filter: general / anime / people bits
CONTENT_BITS = ("general", "anime", "people")

# ---------------------------------------------------------------------------


def load_config() -> None:
    """Override the defaults above with the app's config.json, if present."""
    try:
        cfg = json.loads(CONFIG_FILE.read_text())
    except FileNotFoundError:
        return
    except (OSError, ValueError) as e:
        log.warning("Ignoring unreadable %s: %s", CONFIG_FILE, e)
        return
    for key, name in CONFIG_KEYS.items():
        if key in cfg:
            globals()[name] = cfg[key]
    apply_theme(cfg.get("themes", {}).get(cfg.get("active_theme")))
    # a category with no queries or zero weight must never be picked
    for name in [n for n, c in CATEGORIES.items()
                 if not c.get("queries") or c.get("weight", 0) <= 0]:
        del CATEGORIES[name]


def apply_theme(theme: dict | None) -> None:
    """A theme (set up in the app) bundles categories, fallback and content filter."""
    global CATEGORIES, FALLBACK_QUERIES, CONTENT
    if not theme:
        return
    CATEGORIES = theme.get("categories", {})
    FALLBACK_QUERIES = theme.get("fallback_queries") or [
        q for c in CATEGORIES.values() for q in c.get("queries", [])][:6]
    content = theme.get("content") or ["general"]
    CONTENT = "".join("1" if bit in content else "0" for bit in CONTENT_BITS)

ImageFile.LOAD_TRUNCATED_IMAGES = False  # a cut-off download must fail, not half-decode

log = logging.getLogger("wallpaper-sh")


def make_session() -> requests.Session:
    """HTTP session with retries on transient errors and rate limiting."""
    s = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=2,                       # 0s, 2s, 4s
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET"]),
        respect_retry_after_header=True,
    )
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.headers.update({"User-Agent": USER_AGENT, "Referer": "https://wallhaven.cc/"})
    # Optional wallhaven API key (see README): raises rate limits, not required.
    key = os.environ.get("WALLHAVEN_API_KEY", "").strip()
    if key:
        s.headers["X-API-Key"] = key
        log.debug("Using WALLHAVEN_API_KEY")
    return s


def wait_for_network(s: requests.Session) -> bool:
    """Poll until wallhaven is reachable, or give up. Never raises."""
    deadline = time.monotonic() + NETWORK_WAIT_SECONDS
    delay = 10
    while True:
        try:
            s.get(API, params={"q": "id:922", "page": 999}, timeout=API_TIMEOUT).raise_for_status()
            return True
        except requests.RequestException as e:
            if time.monotonic() >= deadline:
                log.error("Network unreachable after %ss: %s", NETWORK_WAIT_SECONDS, e)
                return False
            log.info("Network not ready (%s); retrying in %ss", e.__class__.__name__, delay)
            time.sleep(delay)
            delay = min(delay * 2, 60)


def load_history() -> set[str]:
    try:
        return set(json.loads(HISTORY_FILE.read_text())["ids"])
    except (OSError, ValueError, KeyError):
        return set()


def save_history(ids: set[str]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = HISTORY_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps({"ids": sorted(ids)}, indent=0))
    tmp.replace(HISTORY_FILE)


def pick_category() -> tuple[str, dict]:
    """Weighted random category choice."""
    if not CATEGORIES:
        return "fallback", {"queries": FALLBACK_QUERIES, "sorting": "toplist"}
    names = list(CATEGORIES)
    weights = [CATEGORIES[n]["weight"] for n in names]
    name = random.choices(names, weights=weights, k=1)[0]
    return name, CATEGORIES[name]


def search(s: requests.Session, query: str, sorting: str, page: int) -> dict:
    params = {
        "q": query,
        "categories": CONTENT,    # default "100": general only (no anime, no people-only)
        "purity": "100",          # SFW only
        "atleast": f"{MIN_WIDTH}x{MIN_HEIGHT}",
        "ratios": "landscape",    # wallhaven server-side landscape filter
        "sorting": sorting,
        "page": page,
    }
    r = s.get(API, params=params, timeout=API_TIMEOUT)
    r.raise_for_status()
    return r.json()


def acceptable(item: dict, history: set[str]) -> bool:
    """Metadata-level filtering, before we spend bandwidth on a download."""
    if item["id"] in history:
        return False
    if item.get("file_type") not in ALLOWED_TYPES:
        return False
    w, h = item.get("dimension_x", 0), item.get("dimension_y", 0)
    if w < MIN_WIDTH or h < MIN_HEIGHT:
        return False
    if not (MIN_ASPECT <= w / h <= MAX_ASPECT):
        return False
    if not (MIN_BYTES <= item.get("file_size", 0) <= MAX_BYTES):
        return False
    return True


def collect_candidates(s: requests.Session, cfg: dict, history: set[str]) -> list[dict]:
    """Pool candidates from several of a category's queries.

    Individual wallhaven queries for historic F1 are small (4-30 hits), so
    stopping at the first query that returns anything would keep picking from
    a 1-2 image pool. Instead we gather from up to POOL_QUERIES successful
    queries and pick from the union.
    """
    queries = list(cfg["queries"])
    random.shuffle(queries)
    sorting = cfg.get("sorting", "relevance")
    pool: list[dict] = []
    hits, tried = 0, 0

    for q in queries:
        if hits >= POOL_QUERIES or tried >= MAX_QUERY_ATTEMPTS:
            break
        tried += 1
        try:
            first = search(s, q, sorting, page=1)
        except requests.RequestException as e:
            log.warning("Search failed for %r: %s", q, e)
            continue
        last_page = max(1, int(first["meta"].get("last_page") or 1))
        last_page = min(last_page, cfg.get("max_pages", last_page))
        page = random.randint(1, last_page)
        data = first["data"] if page == 1 else None
        if data is None:
            try:
                data = search(s, q, sorting, page=page)["data"]
            except requests.RequestException as e:
                log.warning("Page %s failed for %r: %s", page, q, e)
                continue
        good = [i for i in data if acceptable(i, history)]
        log.debug("query=%r page=%s/%s -> %s usable", q, page, last_page, len(good))
        if good:
            hits += 1
            pool.extend(good)

    # de-duplicate: the same image is often tagged with several drivers/teams
    seen, uniq = set(), []
    for item in pool:
        if item["id"] not in seen:
            seen.add(item["id"])
            uniq.append(item)
    log.info("Pooled %s candidates from %s/%s queries", len(uniq), hits, tried)
    return uniq


def choose(candidates: list[dict]) -> dict:
    """Prefer higher-resolution images, but stay random."""
    hi = [c for c in candidates if c["dimension_x"] >= PREFER_WIDTH]
    return random.choice(hi or candidates)


def download_and_validate(s: requests.Session, item: dict) -> Path:
    """Download to a temp file and verify it is genuinely a usable image."""
    WALLPAPER_DIR.mkdir(parents=True, exist_ok=True)
    ext = ".png" if item["file_type"] == "image/png" else ".jpg"
    fd, tmp_name = tempfile.mkstemp(dir=WALLPAPER_DIR, prefix=".dl-", suffix=ext)
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as fh:
            with s.get(item["path"], stream=True, timeout=DL_TIMEOUT) as r:
                r.raise_for_status()
                size = 0
                for chunk in r.iter_content(1 << 16):
                    size += len(chunk)
                    if size > MAX_BYTES:
                        raise ValueError("download exceeded MAX_BYTES")
                    fh.write(chunk)
        if size < MIN_BYTES:
            raise ValueError(f"file too small ({size} bytes)")

        # Pillow validation. im.verify() only checks headers, so we also force
        # a full decode with im.load() - that is what catches a download that
        # was cut off half way (truncated JPEG/PNG data).
        with Image.open(tmp) as im:
            im.verify()
        with Image.open(tmp) as im:
            w, h = im.size
            fmt = im.format
            im.load()
        if fmt not in ("JPEG", "PNG"):
            raise ValueError(f"unexpected format {fmt}")
        if w < MIN_WIDTH or h < MIN_HEIGHT:
            raise ValueError(f"too small: {w}x{h}")
        if not (MIN_ASPECT <= w / h <= MAX_ASPECT):
            raise ValueError(f"bad aspect ratio: {w}x{h}")

        final = WALLPAPER_DIR / f"{time.strftime('%Y-%m-%d')}_{item['_category']}_{item['id']}{ext}"
        tmp.replace(final)
        os.chmod(final, 0o644)
        log.info("Saved %s (%sx%s, %.1f MiB)", final.name, w, h, size / 1048576)
        return final
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


# --- KDE Plasma ------------------------------------------------------------

def _plasma_script(path: Path) -> str:
    """Plasma scripting-API snippet: set image + fill mode on the desktops."""
    url = json.dumps(path.as_uri())          # safe JS string literal
    screen_guard = "" if ALL_MONITORS else "if (d.screen !== 0) { continue; }"
    return f"""
var ds = desktops();
for (var i = 0; i < ds.length; i++) {{
    var d = ds[i];
    {screen_guard}
    d.wallpaperPlugin = "org.kde.image";
    d.currentConfigGroup = Array("Wallpaper", "org.kde.image", "General");
    d.writeConfig("Image", {url});
    d.writeConfig("FillMode", {FILL_MODE});
}}
"""


def _dbus_apply(path: Path) -> bool:
    """Supported Plasma D-Bus scripting API. Gives us fill mode + per-screen."""
    script = _plasma_script(path)
    for cmd in (
        ["gdbus", "call", "--session", "--dest", "org.kde.plasmashell",
         "--object-path", "/PlasmaShell",
         "--method", "org.kde.PlasmaShell.evaluateScript", script],
        # qdbus name differs between distros/Qt versions
        *[[q, "org.kde.plasmashell", "/PlasmaShell",
           "org.kde.PlasmaShell.evaluateScript", script]
          for q in ("qdbus6", "qdbus-qt6", "qdbus", "qdbus-qt5")],
    ):
        if shutil.which(cmd[0]) is None:
            continue
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        except subprocess.SubprocessError as e:
            log.warning("%s failed: %s", cmd[0], e)
            continue
        if out.returncode == 0 and "Error" not in out.stdout:
            log.info("Wallpaper applied via %s", cmd[0])
            return True
        log.warning("%s returned rc=%s out=%r err=%r",
                    cmd[0], out.returncode, out.stdout.strip(), out.stderr.strip())
    return False


def _cli_apply(path: Path) -> bool:
    """Official plasma-workspace CLI (Plasma >= 5.23). Applies to all screens."""
    exe = shutil.which("plasma-apply-wallpaperimage")
    if not exe:
        return False
    try:
        out = subprocess.run([exe, str(path)], capture_output=True, text=True, timeout=30)
    except subprocess.SubprocessError as e:
        log.warning("plasma-apply-wallpaperimage failed: %s", e)
        return False
    if out.returncode == 0:
        log.info("Wallpaper applied via plasma-apply-wallpaperimage")
        return True
    log.warning("plasma-apply-wallpaperimage rc=%s err=%r", out.returncode, out.stderr.strip())
    return False


def _plasma_ready() -> bool:
    """True once plasmashell exposes org.kde.PlasmaShell.evaluateScript."""
    try:
        out = subprocess.run(
            ["gdbus", "introspect", "--session", "--dest", "org.kde.plasmashell",
             "--object-path", "/PlasmaShell"],
            capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return out.returncode == 0 and "evaluateScript" in out.stdout


def wait_for_plasma() -> bool:
    if shutil.which("gdbus") is None:
        return True                           # can't probe; just try to apply
    deadline = time.monotonic() + PLASMA_WAIT_SECONDS
    waited = False
    while not _plasma_ready():
        if time.monotonic() >= deadline:
            log.warning("plasmashell not ready after %ss", PLASMA_WAIT_SECONDS)
            return False
        if not waited:
            log.info("Waiting for plasmashell to finish starting...")
            waited = True
        time.sleep(5)
    if waited:
        time.sleep(3)                         # let the desktop containments load
    return True


def set_wallpaper(path: Path) -> bool:
    """D-Bus first (fill mode + monitor control), official CLI as fallback."""
    wait_for_plasma()
    return _dbus_apply(path) or _cli_apply(path)


def set_lock_screen(path: Path) -> bool:
    """Point the lock screen (kscreenlocker) at the same image.

    The lock screen has no D-Bus scripting API, so the supported route is
    kwriteconfig - KDE's own config-writing tool, part of kconfig. The greeter
    re-reads kscreenlockerrc every time it starts, so the change shows up at
    the next lock; nothing needs restarting.
    """
    exe = next((shutil.which(e) for e in ("kwriteconfig6", "kwriteconfig5", "kwriteconfig")
                if shutil.which(e)), None)
    if not exe:
        log.warning("kwriteconfig not found; lock screen left unchanged")
        return False

    wp = ["--group", "Greeter", "--group", "Wallpaper",
          "--group", "org.kde.image", "--group", "General"]
    commands = [
        [exe, "--file", "kscreenlockerrc", "--group", "Greeter",
         "--key", "WallpaperPlugin", "org.kde.image"],
        [exe, "--file", "kscreenlockerrc", *wp, "--key", "Image", path.as_uri()],
        [exe, "--file", "kscreenlockerrc", *wp, "--key", "FillMode", str(FILL_MODE)],
    ]
    for cmd in commands:
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        except subprocess.SubprocessError as e:
            log.warning("%s failed: %s", exe, e)
            return False
        if r.returncode != 0:
            log.warning("%s rc=%s err=%r", exe, r.returncode, r.stderr.strip())
            return False
    log.info("Lock screen updated (takes effect at the next lock)")
    return True


def set_login_screen(path: Path) -> bool:
    """Copy the image to LOGIN_WALLPAPER, which the greeter reads at startup.

    Always re-encoded as JPEG so the fixed .jpg name stays truthful, and written
    via a temp file + rename so the greeter never sees a half-written image.
    """
    target_dir = LOGIN_WALLPAPER.parent
    if not os.access(target_dir, os.W_OK):
        log.warning("%s is missing or not writable; login screen left unchanged", target_dir)
        return False
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(dir=target_dir, suffix=".jpg", delete=False) as f:
            tmp = Path(f.name)
            with Image.open(path) as im:
                im.convert("RGB").save(f, "JPEG", quality=92)
        tmp.chmod(0o644)
        os.replace(tmp, LOGIN_WALLPAPER)
    except Exception as e:
        log.warning("Login screen update failed: %s", e)
        if tmp:
            tmp.unlink(missing_ok=True)
        return False
    log.info("Login screen updated (takes effect at the next boot/logout)")
    return True


def prune(keep: int) -> None:
    files = sorted(
        (p for p in WALLPAPER_DIR.glob("*") if p.is_file() and not p.name.startswith(".")),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for p in files[keep:]:
        p.unlink(missing_ok=True)


def apply_everywhere(path: Path) -> bool:
    """Apply to every enabled target. Only the desktop can fail the run."""
    if ALSO_DESKTOP and not set_wallpaper(path):
        log.error("Could not talk to Plasma (is plasmashell running?)")
        return False
    if ALSO_LOCK_SCREEN:
        set_lock_screen(path)                 # best effort: never fails the run
    if ALSO_LOGIN_SCREEN:
        set_login_screen(path)                # best effort: never fails the run
    return True


def save_current(path: Path, query: str | None = None) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CURRENT_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps({"path": str(path), "query": query, "applied_at": int(time.time())}))
    tmp.replace(CURRENT_FILE)


def acquire_lock():
    """Non-blocking run lock; returns the open file (keep it alive) or None."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    fh = open(LOCK_FILE, "w")
    try:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        fh.close()
        return None
    return fh


def reapply(path: Path) -> int:
    if not path.is_file():
        log.error("No such image: %s", path)
        return 1
    if not apply_everywhere(path):
        return 1
    os.utime(path)                            # freshly used -> survives prune()
    save_current(path)
    log.info("Done: re-applied %s", path.name)
    return 0


def fetch_new(query: str | None) -> int:
    session = make_session()
    if not wait_for_network(session):
        return 1                              # existing wallpaper is untouched

    history = load_history()
    if query:
        name, cfg = "custom", {"queries": [query], "sorting": "relevance"}
        log.info("Custom prompt: %r", query)
    else:
        name, cfg = pick_category()
        log.info("Category: %s (%s already in history)", name, len(history))

    candidates = collect_candidates(session, cfg, history)
    if not candidates and query:
        log.error("No usable wallpaper found for %r; keeping the current one", query)
        return 1
    if not candidates:
        log.warning("Category %r produced nothing usable; using fallback pool", name)
        name = "fallback"
        candidates = collect_candidates(
            session, {"queries": FALLBACK_QUERIES, "sorting": "toplist"}, history
        )
    if not candidates:
        log.error("No usable wallpaper found; keeping the current one")
        return 1

    # Try a few candidates: a download or validation failure shouldn't end the run.
    random.shuffle(candidates)
    for item in candidates[:5]:
        item["_category"] = re.sub(r"[^a-z0-9_]+", "-", name.lower()).strip("-") or "custom"
        try:
            path = download_and_validate(session, item)
        except Exception as e:
            log.warning("Rejected %s: %s", item["id"], e)
            continue
        if not apply_everywhere(path):
            return 1                          # keep the file, retry next time
        history.add(item["id"])               # only remember what we actually showed
        save_history(history)
        save_current(path, query)
        prune(KEEP_FILES)
        log.info("Done: https://wallhaven.cc/w/%s", item["id"])
        return 0

    log.error("All candidates failed validation; keeping the current wallpaper")
    return 1


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(message)s",   # journald adds its own timestamp
        stream=sys.stderr,
    )
    parser = argparse.ArgumentParser(description="wallpaper.sh - wallpaper of the day")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--query", help="search wallhaven for this prompt instead of a category")
    group.add_argument("--apply", type=Path, metavar="FILE", help="re-apply a downloaded image")
    args = parser.parse_args()

    load_config()
    lock = acquire_lock()
    if lock is None:
        log.error("Another wallpaper run is in progress")
        return 75                             # EX_TEMPFAIL
    with lock:
        if args.apply:
            return reapply(args.apply.expanduser().resolve())
        return fetch_new((args.query or "").strip() or None)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception:
        logging.exception("Unhandled error; wallpaper left unchanged")
        sys.exit(1)
