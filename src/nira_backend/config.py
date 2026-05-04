"""Central configuration for NIRA backend.

All runtime paths are read from ``config/local.json`` (gitignored).
Fall-back values work out-of-the-box so the project runs without any config
file during development.

Example ``config/local.json``::

    {
        "database_path": "/home/pi/nira/nira_data.db",
        "data_dir": "/home/pi/nira/data"
    }
"""

import json
from pathlib import Path

_CONFIG_FILE = Path("config/local.json")


def _load_config() -> dict:
    if _CONFIG_FILE.exists():
        try:
            return json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def get_database_path() -> Path:
    """Return the SQLite database file path."""
    cfg = _load_config()
    return Path(cfg.get("database_path", "nira_data.db"))


def get_data_dir() -> Path:
    """Return the root data directory (memory, entries, …)."""
    cfg = _load_config()
    return Path(cfg.get("data_dir", "data"))
