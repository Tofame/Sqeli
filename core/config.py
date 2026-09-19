"""
core/config.py — Configuration loading, saving, and defaults for Sqeli.
"""

import sys
import json
import os
from pathlib import Path


def get_app_root() -> Path:
	if getattr(sys, "frozen", False):
		return Path(sys.executable).parent.resolve()
	return Path(__file__).resolve().parent.parent


CONFIG_FILE = get_app_root() / "config.json"

DEFAULTS = {
    "theme": "dark",
    "autostart": False,
    "autostart_services": False,
    "apache": {
        "bin": "C:/laragon/bin/apache/bin/httpd.exe",
        "htdocs": "",
        "port": 80,
        "enabled": True,
    },
    "mysql": {
        "bin": "C:/laragon/bin/mysql/bin/mysqld.exe",
        "port": 3306,
        "datadir": "C:/laragon/data",
        "enabled": True,
    },
}


def load() -> dict:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Merge missing keys from DEFAULTS (deep merge one level)
            for key, val in DEFAULTS.items():
                if key not in data:
                    data[key] = val
                elif isinstance(val, dict):
                    for subkey, subval in val.items():
                        if subkey not in data[key]:
                            data[key][subkey] = subval
            return data
        except (json.JSONDecodeError, OSError):
            pass
    return dict(DEFAULTS)


def save(cfg: dict) -> None:
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except OSError as e:
        print(f"[Config] Failed to save: {e}")
