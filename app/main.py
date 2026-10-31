#!/usr/bin/env python3
"""
wallpaper.sh - a wallpaper-of-the-day app for KDE Plasma, on top of
~/.local/bin/wallpaper-sh.py.

The script stays the single source of truth: this app reads its defaults and
paths, writes overrides to its config.json, runs it for manual changes and
manages the systemd --user timer that runs it on a schedule.

Deps: python3-pyside6 (plus the script's own deps)
"""

from __future__ import annotations

import copy
import importlib.util
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import (Property, QFileSystemWatcher, QObject, QProcess,
                            QProcessEnvironment, Qt, QTimer, QUrl, Signal, Slot)
from PySide6.QtGui import (QDesktopServices, QFont, QGuiApplication, QIcon,
                           QImageReader, QPainter, QPixmap)
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickImageProvider
from PySide6.QtQuickControls2 import QQuickStyle
import PySide6
from PySide6.QtSvg import QSvgRenderer

APP_NAME = "wallpaper.sh"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Serhii Klymchuk"
APP_AUTHOR_ROLE = "Linux enthusiast"

APP_DIR = Path(__file__).resolve().parent
SCRIPT = Path(os.environ.get("WALLPAPER_SH_SCRIPT", Path.home() / ".local/bin/wallpaper-sh.py"))
TIMER = "wallpaper-sh.timer"
TIMER_OVERRIDE = Path.home() / ".config/systemd/user/wallpaper-sh.timer.d/app-schedule.conf"
ENV_FILE = Path.home() / ".config/wallpaper-sh/env"

DEFAULT_SCHEDULE = {"mode": "daily", "every": 3, "time": "08:30", "day": "Mon"}
SCHEDULE_HOURS = (1, 2, 3, 4, 6, 12)
WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

TARGET_KEYS = {"desktop": "apply_desktop", "lock": "apply_lock_screen", "login": "apply_login_screen"}
NAME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})_(.+)_([A-Za-z0-9]+)\.(?:jpe?g|png)$", re.I)
CATEGORY_LABELS = {"custom": "Custom prompt", "fallback": "Mixed pick"}
APPEARANCES = ("dark", "light")
CONTENT_TYPES = ("general", "anime", "people")


def load_script():
    """Import the wallpaper script as a module for its defaults and paths."""
    spec = importlib.util.spec_from_file_location("wallpaper_sh_script", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


wp = load_script()


def _cat(weight: int, queries: list[str], sorting: str = "relevance") -> dict:
    return {"weight": weight, "sorting": sorting, "queries": queries}


# Built-in themes. "formula_1" is the script's own defaults.
PRESETS: dict[str, dict] = {
    "formula_1": {
        "label": "Formula 1",
        "content": ["general"],
        "fallback_queries": list(wp.FALLBACK_QUERIES),
        "categories": copy.deepcopy(wp.CATEGORIES),
    },
    "nature": {
        "label": "Nature",
        "content": ["general"],
        "categories": {
            "mountains": _cat(30, ["mountains", "alps", "mountain lake", "dolomites"]),
            "forests": _cat(25, ["forest", "autumn forest", "misty forest", "waterfall"]),
            "sky": _cat(20, ["aurora", "sunset", "starry sky", "milky way"], "toplist"),
            "ocean": _cat(25, ["ocean waves", "beach", "coast", "underwater"]),
        },
    },
    "space": {
        "label": "Space",
        "content": ["general"],
        "categories": {
            "deep_space": _cat(40, ["nebula", "galaxy", "deep space", "james webb"], "toplist"),
            "planets": _cat(30, ["planet", "earth from space", "saturn", "mars"]),
            "sci_fi": _cat(30, ["space station", "astronaut", "spaceship", "sci-fi landscape"]),
        },
    },
    "cities": {
        "label": "Cities",
        "content": ["general"],
        "categories": {
            "night": _cat(40, ["city lights", "skyline night", "neon city", "rainy street"]),
            "landmarks": _cat(30, ["tokyo", "new york city", "paris", "hong kong"]),
            "architecture": _cat(30, ["architecture", "skyscraper", "bridge", "old town"]),
        },
    },
    "cars": {
        "label": "Cars",
        "content": ["general"],
        "categories": {
            "supercars": _cat(35, ["supercar", "lamborghini", "ferrari", "mclaren"]),
            "jdm": _cat(35, ["jdm", "nissan skyline", "toyota supra", "mazda rx-7"]),
            "classics": _cat(30, ["classic car", "porsche 911", "muscle car", "vintage car"]),
        },
    },
    "minimal": {
        "label": "Minimal",
        "content": ["general"],
        "categories": {
            "minimal": _cat(50, ["minimalism", "simple background", "gradient"], "toplist"),
            "abstract": _cat(50, ["abstract", "geometry", "digital art", "low poly"], "toplist"),
        },
    },
    "paintings": {
        "label": "Happy little paintings",
        "content": ["general"],
        "categories": {
            "landscapes": _cat(50, ["landscape painting", "oil painting", "bob ross"]),
            "classics": _cat(30, ["classic art", "impressionism", "claude monet", "van gogh"]),
            "fantasy": _cat(20, ["fantasy landscape", "concept art", "matte painting"], "toplist"),
        },
    },
    "anime": {
        "label": "Anime",
        "content": ["anime"],
        "categories": {
            "scenery": _cat(50, ["anime landscape", "anime sky", "makoto shinkai"], "toplist"),
            "ghibli": _cat(30, ["studio ghibli", "spirited away", "howl's moving castle"]),
            "city": _cat(20, ["anime city", "anime night", "cyberpunk anime"]),
        },
    },
}


# --- formatting --------------------------------------------------------------

def category_label(name: str) -> str:
    return CATEGORY_LABELS.get(name) or re.sub(r"[_-]+", " ", name).strip().capitalize()


def date_label(dt: datetime, with_year: bool = True) -> str:
    text = f"{WEEKDAYS[dt.weekday()]}, {dt.day} {MONTHS[dt.month - 1]}"
    return f"{text} {dt.year}" if with_year else text


def moment_label(dt: datetime) -> str:
    today = datetime.now().date()
    day = {0: "Today", 1: "Tomorrow", -1: "Yesterday"}.get((dt.date() - today).days)
    return f"{day or date_label(dt, with_year=False)} · {dt:%H:%M}"


def relative_label(dt: datetime) -> str:
    minutes = round((dt - datetime.now()).total_seconds() / 60)
    if minutes < 1:
        return "any moment"
    if minutes < 60:
        return f"in {minutes} min"
    if minutes < 48 * 60:
        return f"in {round(minutes / 60)} h"
    return f"in {round(minutes / 1440)} days"


def size_label(n: int) -> str:
    return f"{n / 1048576:.1f} MB" if n >= 1048576 else f"{round(n / 1024)} KB"


def describe(path: Path) -> dict:
    m = NAME_RE.match(path.name)
    date, category, wid = m.groups() if m else ("", "unknown", "")
    st = path.stat()
    try:
        dt = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        dt = datetime.fromtimestamp(st.st_mtime)
    size = QImageReader(str(path)).size()
    return {
        "path": str(path),
        "url": QUrl.fromLocalFile(str(path)).toString(),
        "name": path.name,
        "id": wid,
        "category": category,
        "categoryLabel": category_label(category),
        "date": dt.strftime("%Y-%m-%d"),
        "dateLabel": date_label(dt),
        "width": size.width(),
        "height": size.height(),
        "sizeLabel": size_label(st.st_size),
        "mtime": st.st_mtime,
    }


# --- config ------------------------------------------------------------------

def read_config() -> dict:
    try:
        return json.loads(wp.CONFIG_FILE.read_text())
    except (OSError, ValueError):
        return {}


def migrate_config() -> None:
    """Pre-theme configs had top-level "categories": they become the Formula 1 theme."""
    cfg = read_config()
    if "themes" in cfg:
        return
    themes = copy.deepcopy(PRESETS)
    if "categories" in cfg:
        themes["formula_1"]["categories"] = cfg.pop("categories")
    cfg["themes"] = themes
    cfg.setdefault("active_theme", "formula_1")
    write_config(cfg)


def theme_id(label: str, taken) -> str:
    base = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_") or "theme"
    tid, n = base, 2
    while tid in taken:
        tid, n = f"{base}_{n}", n + 1
    return tid


def command_output(*cmd: str) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=5).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def write_config(cfg: dict) -> None:
    wp.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = wp.CONFIG_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(cfg, indent=2))
    tmp.replace(wp.CONFIG_FILE)


def env_file_pairs() -> dict[str, str]:
    """KEY=VALUE pairs from the service's EnvironmentFile, if any."""
    pairs = {}
    try:
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                pairs[key.strip()] = value.strip().strip("'\"")
    except OSError:
        pass
    return pairs


def systemctl(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["systemctl", "--user", *args], capture_output=True, text=True, timeout=20)


def on_calendar(s: dict) -> str:
    if s["mode"] == "hours":
        return "hourly" if s["every"] == 1 else f"*-*-* 00/{s['every']}:00:00"
    prefix = f"{s['day']} " if s["mode"] == "weekly" else ""
    return f"{prefix}*-*-* {s['time']}:00"


# --- icons -------------------------------------------------------------------

ICONS = {
    "flag": '<path d="M4 22V4"/><path d="M4 4h13l-2.5 4.5L17 13H4"/>',
    "grid": '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/>'
            '<rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
    "sparkles": '<path d="M11 3l1.9 5.1L18 10l-5.1 1.9L11 17l-1.9-5.1L4 10l5.1-1.9z"/><path d="M19 3v4M17 5h4"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "refresh": '<path d="M21 12a9 9 0 1 1-2.64-6.36L21 8"/><path d="M21 3v5h-5"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "x": '<path d="M18 6 6 18M6 6l12 12"/>',
    "external": '<path d="M15 3h6v6M10 14 21 3M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>',
    "trash": '<path d="M3 6h18M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "play": '<path d="M7 4.5v15l12-7.5z"/>',
    "folder": '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    "monitor": '<rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/>',
    "lock": '<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
    "left": '<path d="m15 18-6-6 6-6"/>',
    "right": '<path d="m9 18 6-6-6-6"/>',
    "loader": '<path d="M21 12a9 9 0 1 1-6.2-8.56"/>',
    "pause": '<circle cx="12" cy="12" r="9"/><path d="M10 9v6M14 9v6"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4'
           'M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    "calendar": '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 16v-5M12 8h.01"/>',
    "moon": '<path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z"/>',
    "image": '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="9" cy="9" r="2"/>'
             '<path d="m21 15-3.1-3.1a2 2 0 0 0-2.8 0L6 21"/>',
}


class IconProvider(QQuickImageProvider):
    """image://icon/<name>/<hex color> - stroke icons tinted to any color."""

    def __init__(self):
        super().__init__(QQuickImageProvider.ImageType.Pixmap)

    def requestPixmap(self, icon_id, size, requested_size):
        name, _, hex_color = icon_id.partition("/")
        w = requested_size.width() if requested_size.width() > 0 else 48
        h = requested_size.height() if requested_size.height() > 0 else w
        hex_color = hex_color or "ffffff"
        opacity = 1.0
        if len(hex_color) == 8:                     # QML hands over #AARRGGBB
            opacity, hex_color = int(hex_color[:2], 16) / 255, hex_color[2:]
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
               f'stroke="#{hex_color}" stroke-opacity="{opacity:.3f}" stroke-width="1.9" '
               f'stroke-linecap="round" stroke-linejoin="round">{ICONS.get(name, "")}</svg>')
        pixmap = QPixmap(w, h)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        QSvgRenderer(svg.encode()).render(painter)
        painter.end()
        if size is not None:
            size.setWidth(w)
            size.setHeight(h)
        return pixmap


# --- backend -------------------------------------------------------------------

class Backend(QObject):
    imagesChanged = Signal()
    configChanged = Signal()
    aboutChanged = Signal()
    scheduleChanged = Signal()
    busyChanged = Signal()
    statusChanged = Signal()
    toast = Signal(str, bool)

    def __init__(self):
        super().__init__()
        self._images: list[dict] = []
        self._current: dict = {}
        self._config: dict = {}
        self._schedule: dict = {}
        self._proc: QProcess | None = None
        self._status = ""
        self._last_error = ""
        self._about: dict = {}

        migrate_config()
        wp.WALLPAPER_DIR.mkdir(parents=True, exist_ok=True)
        wp.STATE_DIR.mkdir(parents=True, exist_ok=True)
        self._debounce = QTimer(self, singleShot=True, interval=400, timeout=self.refresh)
        self._watcher = QFileSystemWatcher([str(wp.WALLPAPER_DIR), str(wp.STATE_DIR)], self)
        self._watcher.directoryChanged.connect(self._debounce.start)
        self._clock = QTimer(self, interval=30_000, timeout=self._load_schedule)
        self._clock.start()

        self.refresh()

    # -- properties -----------------------------------------------------------

    def _get_images(self):
        return self._images

    def _get_current(self):
        return self._current

    def _get_targets(self):
        c = self._config
        return {
            **{k: bool(c.get(key, True)) for k, key in TARGET_KEYS.items()},
            "allMonitors": bool(c.get("all_monitors", wp.ALL_MONITORS)),
            "loginAvailable": os.access(wp.LOGIN_WALLPAPER.parent, os.W_OK),
        }

    def _theme(self) -> tuple[str, dict]:
        themes = self._config.get("themes") or {}
        tid = self._config.get("active_theme")
        if tid not in themes:
            tid = next(iter(themes), "formula_1")
        return tid, themes.get(tid) or copy.deepcopy(PRESETS["formula_1"])

    def _get_categories(self):
        cats = self._theme()[1].get("categories", {})
        edited = ("weight", "sorting", "queries")
        return [{"name": n, "weight": int(c.get("weight", 0)), "sorting": c.get("sorting", "relevance"),
                 "queries": list(c.get("queries", [])),
                 "extra": {k: v for k, v in c.items() if k not in edited}}   # e.g. max_pages
                for n, c in cats.items()]

    def _get_themes(self):
        active = self._theme()[0]
        return [{"id": tid, "label": t.get("label", tid), "active": tid == active, "preset": tid in PRESETS}
                for tid, t in (self._config.get("themes") or {}).items()]

    def _get_active_theme(self):
        tid, t = self._theme()
        queries = [q for c in t.get("categories", {}).values() for q in c.get("queries", [])
                   if not q.startswith("id:")]
        return {
            "id": tid,
            "label": t.get("label", tid),
            "content": list(t.get("content") or ["general"]),
            "preset": tid in PRESETS,
            "examples": ", ".join(queries[:2]) or "mountains, neon city",
        }

    def _get_appearance(self):
        mode = self._config.get("appearance", "dark")
        return mode if mode in APPEARANCES else "dark"

    def _get_about(self):
        if not self._about:
            self._about = self._collect_about()
        return self._about

    def _get_total_weight(self):
        return sum(c["weight"] for c in self._get_categories()) or 1

    def _get_keep_files(self):
        return int(self._config.get("keep_files", wp.KEEP_FILES))

    def _get_schedule(self):
        return self._schedule

    def _get_busy(self):
        return self._proc is not None

    def _get_status(self):
        return self._status

    images = Property("QVariantList", _get_images, notify=imagesChanged)
    current = Property("QVariantMap", _get_current, notify=imagesChanged)
    targets = Property("QVariantMap", _get_targets, notify=configChanged)
    categories = Property("QVariantList", _get_categories, notify=configChanged)
    themes = Property("QVariantList", _get_themes, notify=configChanged)
    activeTheme = Property("QVariantMap", _get_active_theme, notify=configChanged)
    appearance = Property(str, _get_appearance, notify=configChanged)
    about = Property("QVariantMap", _get_about, notify=aboutChanged)
    totalWeight = Property(int, _get_total_weight, notify=configChanged)
    keepFiles = Property(int, _get_keep_files, notify=configChanged)
    schedule = Property("QVariantMap", _get_schedule, notify=scheduleChanged)
    busy = Property(bool, _get_busy, notify=busyChanged)
    status = Property(str, _get_status, notify=statusChanged)

    # -- loading ----------------------------------------------------------------

    @Slot()
    def refresh(self):
        self._config = read_config()
        self._load_images()
        self._load_schedule()
        self.configChanged.emit()

    def _load_images(self):
        files = [p for p in wp.WALLPAPER_DIR.iterdir()
                 if p.is_file() and not p.name.startswith(".") and p.suffix.lower() in (".jpg", ".jpeg", ".png")]
        images = sorted((describe(p) for p in files), key=lambda i: (i["date"], i["mtime"]), reverse=True)

        try:
            state = json.loads(wp.CURRENT_FILE.read_text())
        except (OSError, ValueError):
            state = {}
        current = next((i for i in images if i["path"] == state.get("path")), images[0] if images else {})
        if current:
            current = {**current, "query": state.get("query") or ""}
            applied = state.get("applied_at") if current["path"] == state.get("path") else current["mtime"]
            current["appliedLabel"] = moment_label(datetime.fromtimestamp(applied or current["mtime"]))

        self._images, self._current = images, current
        self.imagesChanged.emit()

    @Slot()
    def _load_schedule(self):
        s = {**DEFAULT_SCHEDULE, **self._config.get("schedule", {})}
        props = {}
        for line in systemctl("show", TIMER, "-p", "UnitFileState", "-p", "NextElapseUSecRealtime").stdout.splitlines():
            key, _, value = line.partition("=")
            props[key] = value
        s["active"] = props.get("UnitFileState") == "enabled"
        if not s["active"]:
            s["mode"] = "off"
        s["nextLabel"], s["nextRelative"] = "Not scheduled", ""
        parts = props.get("NextElapseUSecRealtime", "").split()
        if s["active"] and len(parts) >= 3:
            try:
                nxt = datetime.strptime(f"{parts[1]} {parts[2]}", "%Y-%m-%d %H:%M:%S")
                s["nextLabel"], s["nextRelative"] = moment_label(nxt), relative_label(nxt)
            except ValueError:
                pass
        self._schedule = s
        self.scheduleChanged.emit()

    def _update_config(self, **changes):
        cfg = read_config()
        cfg.update(changes)
        write_config(cfg)
        self._config = cfg
        self.configChanged.emit()

    # -- running the script -----------------------------------------------------

    @Slot()
    def newImage(self):
        self._run([], "Finding a new wallpaper…", "New wallpaper applied")

    @Slot(str)
    def tryQuery(self, query: str):
        query = " ".join(query.split())
        if query:
            self._run(["--query", query], f"Searching “{query}”…", f"Applied a wallpaper for “{query}”")

    @Slot(str)
    def applyImage(self, path: str):
        self._run(["--apply", path], "Applying wallpaper…", "Wallpaper applied")

    def _run(self, args: list[str], label: str, done: str):
        if self._proc is not None:
            self.toast.emit("A wallpaper change is already running", False)
            return
        env = QProcessEnvironment.systemEnvironment()
        for key, value in env_file_pairs().items():
            env.insert(key, value)
        proc = QProcess(self)
        proc.setProcessEnvironment(env)
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        proc.setProgram(sys.executable)
        proc.setArguments([str(SCRIPT), *args])
        proc.readyReadStandardOutput.connect(self._on_output)
        proc.finished.connect(lambda code, _status: self._on_finished(code, done))
        proc.errorOccurred.connect(lambda _err: self._on_finished(-1, done) if self._proc else None)

        self._proc, self._last_error = proc, ""
        self._set_status(label)
        self.busyChanged.emit()
        proc.start()

    def _on_output(self):
        text = bytes(self._proc.readAllStandardOutput()).decode(errors="replace")
        for line in text.splitlines():
            level, _, message = line.partition(" ")
            if level == "ERROR":
                self._last_error = message
            elif level == "INFO" and message:
                self._set_status(message)

    def _on_finished(self, code: int, done: str):
        if self._proc is None:
            return
        self._proc.deleteLater()
        self._proc = None
        self._set_status("")
        self.busyChanged.emit()
        if code == 0:
            self.toast.emit(done, True)
        else:
            self.toast.emit(self._last_error or f"Wallpaper script failed (exit {code})", False)
        self.refresh()

    def _set_status(self, text: str):
        self._status = text
        self.statusChanged.emit()

    # -- images -------------------------------------------------------------------

    @Slot(str)
    def deleteImage(self, path: str):
        if path == self._current.get("path"):
            self.toast.emit("That's the current wallpaper - apply another one first", False)
            return
        target = Path(path)
        if target.parent != wp.WALLPAPER_DIR:
            return
        target.unlink(missing_ok=True)
        self.toast.emit("Image deleted", True)
        self._load_images()

    @Slot(str)
    def openWallhaven(self, wid: str):
        if wid:
            QDesktopServices.openUrl(QUrl(f"https://wallhaven.cc/w/{wid}"))

    @Slot()
    def openFolder(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(wp.WALLPAPER_DIR)))

    # -- targets & storage ----------------------------------------------------------

    @Slot(str, bool)
    def setTarget(self, target: str, enabled: bool):
        if target in TARGET_KEYS:
            self._update_config(**{TARGET_KEYS[target]: enabled})

    @Slot(bool)
    def setAllMonitors(self, enabled: bool):
        self._update_config(all_monitors=enabled)

    @Slot(int)
    def setKeepFiles(self, n: int):
        self._update_config(keep_files=max(5, n))

    # -- prompts --------------------------------------------------------------------

    def _save_theme(self, **changes):
        cfg = read_config()
        tid, theme = self._theme()
        themes = cfg.setdefault("themes", {})
        themes[tid] = {**theme, **changes}
        cfg["active_theme"] = tid
        write_config(cfg)
        self._config = cfg
        self.configChanged.emit()

    def _save_categories(self, cats: list[dict]):
        self._save_theme(categories={
            c["name"]: {**c.get("extra", {}), "weight": c["weight"], "sorting": c["sorting"], "queries": c["queries"]}
            for c in cats
        })

    def _edit_category(self, index: int, edit) -> None:
        cats = self._get_categories()
        if 0 <= index < len(cats):
            edit(cats, cats[index])
            self._save_categories(cats)

    @Slot(int, int)
    def setCategoryWeight(self, index: int, weight: int):
        self._edit_category(index, lambda _cats, c: c.update(weight=max(0, min(100, weight))))

    @Slot(int, str)
    def setCategorySorting(self, index: int, sorting: str):
        if sorting in ("relevance", "date_added", "toplist"):
            self._edit_category(index, lambda _cats, c: c.update(sorting=sorting))

    @Slot(int, str)
    def renameCategory(self, index: int, name: str):
        name = re.sub(r"[^a-z0-9_]+", "_", name.strip().lower()).strip("_")
        cats = self._get_categories()
        if not name or any(c["name"] == name for c in cats):
            self.toast.emit("Category names must be unique and not empty", False)
            self.configChanged.emit()           # puts the old name back in the field
            return
        self._edit_category(index, lambda _cats, c: c.update(name=name))

    @Slot(int, str)
    def addQuery(self, index: int, query: str):
        query = " ".join(query.split()).lower()
        if query:
            self._edit_category(index, lambda _cats, c: query in c["queries"] or c["queries"].append(query))

    @Slot(int, int)
    def removeQuery(self, index: int, query_index: int):
        self._edit_category(index, lambda _cats, c: c["queries"].pop(query_index))

    @Slot()
    def addCategory(self):
        cats = self._get_categories()
        names = {c["name"] for c in cats}
        n = 1
        while f"category_{n}" in names:
            n += 1
        cats.append({"name": f"category_{n}", "weight": 10, "sorting": "relevance", "queries": []})
        self._save_categories(cats)

    @Slot(int)
    def removeCategory(self, index: int):
        self._edit_category(index, lambda cats, c: cats.remove(c))

    @Slot()
    def resetCategories(self):
        tid, theme = self._theme()
        if tid not in PRESETS:
            return
        self._save_theme(**copy.deepcopy(PRESETS[tid]))
        self.toast.emit(f"{theme.get('label', tid)} reset to its defaults", True)

    # -- themes -----------------------------------------------------------------------

    @Slot(str)
    def setActiveTheme(self, tid: str):
        if tid in (self._config.get("themes") or {}):
            self._update_config(active_theme=tid)
            self.toast.emit(f"Theme: {self._get_active_theme()['label']} - applies from the next change", True)

    @Slot(str)
    def addTheme(self, label: str):
        label = " ".join(label.split()) or "My theme"
        cfg = read_config()
        themes = cfg.setdefault("themes", {})
        tid = theme_id(label, themes)
        themes[tid] = {"label": label, "content": ["general"],
                       "categories": {"main": _cat(10, [label.lower()])}}
        cfg["active_theme"] = tid
        write_config(cfg)
        self._config = cfg
        self.configChanged.emit()
        self.toast.emit(f"Theme “{label}” created - add categories and queries below", True)

    @Slot(str)
    def renameTheme(self, label: str):
        label = " ".join(label.split())
        if label:
            self._save_theme(label=label)

    @Slot()
    def deleteTheme(self):
        cfg = read_config()
        themes = cfg.get("themes", {})
        tid = self._theme()[0]
        if len(themes) <= 1 or tid not in themes:
            self.toast.emit("Keep at least one theme", False)
            return
        label = themes.pop(tid).get("label", tid)
        cfg["active_theme"] = next(iter(themes))
        write_config(cfg)
        self._config = cfg
        self.configChanged.emit()
        self.toast.emit(f"Theme “{label}” deleted", True)

    @Slot(str, bool)
    def setThemeContent(self, kind: str, enabled: bool):
        content = set(self._get_active_theme()["content"])
        content = content | {kind} if enabled else content - {kind}
        if kind in CONTENT_TYPES and content:
            self._save_theme(content=[k for k in CONTENT_TYPES if k in content])

    # -- appearance & about -------------------------------------------------------------

    @Slot(str)
    def setAppearance(self, mode: str):
        if mode in APPEARANCES:
            self._update_config(appearance=mode)

    def _collect_about(self) -> dict:
        plasma = command_output("plasmashell", "--version").replace("plasmashell", "").strip()
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "")
        session = os.environ.get("XDG_SESSION_TYPE", "unknown")
        systemd = command_output("systemctl", "--version").split("\n")[0].split(" (")[0].replace("systemd ", "")
        dm = next((d for d in ("plasmalogin", "sddm", "gdm", "lightdm")
                   if command_output("systemctl", "is-active", f"{d}.service") == "active"), "")
        os_name = ""
        try:
            os_name = platform.freedesktop_os_release().get("PRETTY_NAME", "")
        except OSError:
            pass
        login_ok = os.access(wp.LOGIN_WALLPAPER.parent, os.W_OK)
        timer_ok = bool(command_output("systemctl", "--user", "show", TIMER, "-p", "FragmentPath",
                                       "--value"))
        checks = [
            {"label": "KDE Plasma 6 desktop", "ok": "KDE" in desktop and plasma.startswith("6"),
             "detail": f"Plasma {plasma}" if plasma else "Plasma not found - desktop wallpaper needs it"},
            {"label": "Lock screen", "ok": bool(shutil.which("kwriteconfig6")),
             "detail": "kwriteconfig6 found" if shutil.which("kwriteconfig6") else "kwriteconfig6 missing"},
            {"label": "Login screen", "ok": login_ok and dm == "plasmalogin",
             "detail": f"{dm or 'unknown'} · " + ("ready" if login_ok else "needs one-time setup")},
            {"label": "Scheduling", "ok": timer_ok,
             "detail": f"systemd {systemd} user timer" if timer_ok else "wallpaper-sh.timer not installed"},
            {"label": "Qt for Python", "ok": tuple(map(int, PySide6.__version__.split(".")[:2])) >= (6, 5),
             "detail": f"PySide6 {PySide6.__version__} (6.5+ needed)"},
        ]
        return {
            "name": APP_NAME,
            "version": APP_VERSION,
            "author": APP_AUTHOR,
            "role": APP_AUTHOR_ROLE,
            "os": os_name,
            "session": session.capitalize(),
            "python": platform.python_version(),
            "pyside": PySide6.__version__,
            "plasma": plasma,
            "folder": str(wp.WALLPAPER_DIR).replace(str(Path.home()), "~"),
            "config": str(wp.CONFIG_FILE).replace(str(Path.home()), "~"),
            "checks": checks,
        }

    @Slot()
    def openConfigFolder(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(wp.CONFIG_FILE.parent)))

    # -- schedule -------------------------------------------------------------------

    @Slot(str, int, str, str)
    def saveSchedule(self, mode: str, every: int, at: str, day: str):
        if mode not in ("off", "hours", "daily", "weekly") or every not in SCHEDULE_HOURS \
                or day not in WEEKDAYS or not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", at):
            self.toast.emit("Invalid schedule", False)
            return
        s = {"mode": mode, "every": every, "time": at, "day": day}
        if mode == "off":
            result = systemctl("disable", "--now", TIMER)
        else:
            self._update_config(schedule=s)
            TIMER_OVERRIDE.parent.mkdir(parents=True, exist_ok=True)
            TIMER_OVERRIDE.write_text(
                "# Managed by the wallpaper.sh app - edit the schedule there.\n"
                "[Timer]\n"
                "OnCalendar=\n"
                f"OnCalendar={on_calendar(s)}\n"
                "RandomizedDelaySec=0\n"
            )
            result = systemctl("daemon-reload")
            if result.returncode == 0:
                result = systemctl("enable", TIMER)
            if result.returncode == 0:
                result = systemctl("restart", TIMER)
        if result.returncode != 0:
            self.toast.emit(f"systemctl failed: {result.stderr.strip()}", False)
        else:
            self.toast.emit("Automatic changes turned off" if mode == "off" else "Schedule saved", True)
        self._load_schedule()


def main() -> int:
    QQuickStyle.setStyle("Basic")
    app = QGuiApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setDesktopFileName("wallpaper-sh")
    app.setWindowIcon(QIcon(str(APP_DIR / "icon.svg")))
    app.setFont(QFont("Inter", 10))

    backend = Backend()
    engine = QQmlApplicationEngine()
    engine.addImageProvider("icon", IconProvider())
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(APP_DIR / "qml" / "Main.qml")))
    if not engine.rootObjects():
        return 1
    code = app.exec()
    del engine                                  # tear QML down while backend still exists
    return code


if __name__ == "__main__":
    sys.exit(main())
