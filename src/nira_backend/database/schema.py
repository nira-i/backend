"""SQLite schema definitions and migration helpers."""

import sqlite3


def initialize_schema(conn: sqlite3.Connection) -> None:
    """
    Create all required tables if they do not already exist.

    This function is idempotent — it is safe to call multiple times.

    Args:
        conn: An open SQLite connection.
    """
    cursor = conn.cursor()

    cursor.executescript("""
        PRAGMA foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS humans (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            name              TEXT    NOT NULL,
            gender            TEXT    NOT NULL CHECK (gender IN ('male', 'female', 'undisclosed')),
            date_of_birth     TEXT    NOT NULL,
            weight_kg         REAL    NOT NULL,
            height_cm         REAL    NOT NULL,
            created_at        TEXT    NOT NULL DEFAULT (datetime('now')),
            updated_at        TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS food_items (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            name                TEXT    NOT NULL,
            category            TEXT    NOT NULL,
            calories            REAL    NOT NULL,
            protein_g           REAL    NOT NULL,
            carbohydrates_g     REAL    NOT NULL,
            fat_g               REAL    NOT NULL,
            fiber_g             REAL    NOT NULL DEFAULT 0,
            sugar_g             REAL    NOT NULL DEFAULT 0,
            sodium_mg           REAL    NOT NULL DEFAULT 0,
            serving_size_g      REAL,
            description         TEXT,
            brand               TEXT,
            created_at          TEXT    NOT NULL DEFAULT (datetime('now')),
            updated_at          TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS food_recipes (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            name                TEXT    NOT NULL,
            description         TEXT,
            servings            INTEGER NOT NULL DEFAULT 1,
            prep_time_minutes   INTEGER,
            cook_time_minutes   INTEGER,
            instructions        TEXT    NOT NULL DEFAULT '[]',
            tags                TEXT    NOT NULL DEFAULT '[]',
            created_at          TEXT    NOT NULL DEFAULT (datetime('now')),
            updated_at          TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS food_recipe_ingredients (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id       INTEGER NOT NULL REFERENCES food_recipes(id) ON DELETE CASCADE,
            food_item_id    INTEGER NOT NULL REFERENCES food_items(id) ON DELETE RESTRICT,
            quantity_g      REAL    NOT NULL,
            notes           TEXT
        );

        CREATE TABLE IF NOT EXISTS health_records (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            human_id        INTEGER REFERENCES humans(id) ON DELETE SET NULL,
            human_name      TEXT    NOT NULL,
            record_date     TEXT    NOT NULL,
            record_type     TEXT    NOT NULL
                CHECK (record_type IN ('blood_pressure', 'blood_glucose', 'heart_rate', 'sleep')),
            measurement     TEXT    NOT NULL,
            notes           TEXT,
            created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_health_records_human_name
            ON health_records (human_name);
        CREATE INDEX IF NOT EXISTS idx_health_records_record_date
            ON health_records (record_date);
        CREATE INDEX IF NOT EXISTS idx_health_records_record_type
            ON health_records (record_type);
        CREATE INDEX IF NOT EXISTS idx_food_recipe_ingredients_recipe
            ON food_recipe_ingredients (recipe_id);
    """)

    conn.commit()
