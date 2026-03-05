"""SQLite database connection manager."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from nira_backend.database.config import get_database_path
from nira_backend.database.schema import initialize_schema


class DatabaseConnection:
    """
    Manages a SQLite database connection and ensures the schema exists.

    Usage::

        db = DatabaseConnection()

        with db.get_cursor() as cursor:
            cursor.execute("SELECT * FROM humans")
            rows = cursor.fetchall()

    The database path is resolved via :func:`~nira_backend.database.config.get_database_path`.
    Pass ``db_path`` to override this (useful in tests).
    """

    def __init__(self, db_path: Path | None = None) -> None:
        self._db_path: Path = db_path if db_path is not None else get_database_path()
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    @property
    def db_path(self) -> Path:
        """Path to the SQLite database file."""
        return self._db_path

    def _ensure_schema(self) -> None:
        """Create tables if they do not already exist."""
        with self._connect() as conn:
            initialize_schema(conn)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @contextmanager
    def get_cursor(self) -> Generator[sqlite3.Cursor, None, None]:
        """
        Context manager that yields a cursor and commits on success.

        Rolls back the transaction automatically on exception.

        Yields:
            sqlite3.Cursor connected to the database.
        """
        conn = self._connect()
        try:
            cursor = conn.cursor()
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
