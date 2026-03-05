"""Database configuration loader.

The database path is read from ``config/local.json``.  If that file does not
exist the application falls back to ``nira_data.db`` in the current working
directory.  ``config/local.json`` is listed in ``.gitignore`` so it is never
committed to source control.

Example ``config/local.json``::

    {
        "database_path": "/home/pi/nira/nira_data.db"
    }
"""

import json
from pathlib import Path

_CONFIG_FILE = Path("config/local.json")
_DEFAULT_DB_PATH = Path("nira_data.db")


def get_database_path() -> Path:
    """
    Return the path to the SQLite database file.

    Reads the path from ``config/local.json`` under the ``database_path`` key.
    Falls back to ``nira_data.db`` in the current directory if the config file
    does not exist or the key is absent.

    Returns:
        Path to the SQLite database file.
    """
    if _CONFIG_FILE.exists():
        try:
            with _CONFIG_FILE.open("r", encoding="utf-8") as fh:
                config = json.load(fh)
            db_path_str = config.get("database_path")
            if db_path_str:
                return Path(db_path_str)
        except (json.JSONDecodeError, OSError):
            pass
    return _DEFAULT_DB_PATH
