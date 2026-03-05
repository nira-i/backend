"""Tests for database connection and schema initialization."""

import sqlite3
import pytest
from pathlib import Path

from nira_backend.database.connection import DatabaseConnection
from nira_backend.database.schema import initialize_schema


@pytest.fixture
def tmp_db(tmp_path: Path) -> DatabaseConnection:
    return DatabaseConnection(db_path=tmp_path / "test.db")


class TestDatabaseConnection:
    def test_creates_db_file(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        DatabaseConnection(db_path=db_path)
        assert db_path.exists()

    def test_cursor_context_manager(self, tmp_db: DatabaseConnection) -> None:
        with tmp_db.get_cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        assert result[0] == 1

    def test_rollback_on_error(self, tmp_db: DatabaseConnection) -> None:
        with pytest.raises(sqlite3.OperationalError):
            with tmp_db.get_cursor() as cursor:
                cursor.execute("SELECT * FROM nonexistent_table")

    def test_db_path_property(self, tmp_path: Path) -> None:
        db_path = tmp_path / "mydb.db"
        db = DatabaseConnection(db_path=db_path)
        assert db.db_path == db_path


class TestSchema:
    def test_all_tables_created(self, tmp_db: DatabaseConnection) -> None:
        expected = {
            "humans",
            "food_items",
            "food_recipes",
            "food_recipe_ingredients",
            "health_records",
        }
        with tmp_db.get_cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor.fetchall()}
        assert expected.issubset(tables)

    def test_schema_idempotent(self, tmp_path: Path) -> None:
        db_path = tmp_path / "idem.db"
        DatabaseConnection(db_path=db_path)
        DatabaseConnection(db_path=db_path)
