import os
import json
from pathlib import Path
from datetime import datetime
from musicdl.logger import log_info, log_error

LOCAL_ROOT = Path(__file__).resolve().parent.parent
if (LOCAL_ROOT / "app.py").exists():
    CONFIG_FILE = LOCAL_ROOT / "config.json"
    DEFAULT_DOWNLOAD_DIR = LOCAL_ROOT / "downloads"
else:
    USER_DIR = Path.home() / ".northtracks"
    USER_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE = USER_DIR / "config.json"
    DEFAULT_DOWNLOAD_DIR = Path.home() / "Music" / "NorthTracks"

DEFAULT_CONFIG = {
    "download_dir": str(DEFAULT_DOWNLOAD_DIR),
    "preferred_bitrate": "320kbps",
    "naming_style": "short",          # "short" (Lead Artist - Title), "title_only", "full"
    "create_m3u": True,               # Generates .m3u companion for playlists
    "embed_lyrics": True,             # Synchronized / plain lyrics
    "skip_duplicates": True,          # Prevents downloading existing songs
    "total_downloads": 0,
    "first_run_completed": False
}

def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {**DEFAULT_CONFIG, **data}
        except Exception as e:
            log_error("Failed to read config.json, restoring defaults", e)
    save_config(DEFAULT_CONFIG)
    return DEFAULT_CONFIG.copy()

def save_config(cfg: dict):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4)
    except Exception as e:
        log_error("Failed to save config.json", e)

def get_download_dir() -> Path:
    cfg = load_config()
    p = Path(cfg.get("download_dir", DEFAULT_DOWNLOAD_DIR))
    p.mkdir(parents=True, exist_ok=True)
    return p

def set_download_dir(new_path: str) -> Path:
    p = Path(new_path).resolve()
    p.mkdir(parents=True, exist_ok=True)
    cfg = load_config()
    cfg["download_dir"] = str(p)
    save_config(cfg)
    log_info(f"Download directory changed to: {p}")
    return p

def set_config_value(key: str, val):
    cfg = load_config()
    cfg[key] = val
    save_config(cfg)
    log_info(f"Config updated: {key} = {val}")

def increment_download_count():
    cfg = load_config()
    cfg["total_downloads"] = cfg.get("total_downloads", 0) + 1
    save_config(cfg)

def get_greeting() -> str:
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "Good morning"
    elif 12 <= hour < 17:
        return "Good afternoon"
    elif 17 <= hour < 22:
        return "Good evening"
    else:
        return "Good night"
