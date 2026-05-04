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

        CREATE TABLE IF NOT EXISTS meal_logs (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            human_name      TEXT    NOT NULL,
            food_name       TEXT    NOT NULL,
            quantity_g      REAL    NOT NULL,
            meal_type       TEXT    NOT NULL DEFAULT 'other'
                CHECK (meal_type IN ('breakfast', 'lunch', 'dinner', 'snack', 'other')),
            log_date        TEXT    NOT NULL,
            notes           TEXT,
            created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS exercise_entries (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            human_name          TEXT    NOT NULL,
            exercise_date       TEXT    NOT NULL,
            activity            TEXT    NOT NULL,
            duration_minutes    INTEGER NOT NULL,
            intensity           TEXT    NOT NULL DEFAULT 'moderate'
                CHECK (intensity IN ('light', 'moderate', 'vigorous')),
            calories_burned     REAL,
            distance_km         REAL,
            notes               TEXT,
            created_at          TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_health_records_human_name
            ON health_records (human_name);
        CREATE INDEX IF NOT EXISTS idx_health_records_record_date
            ON health_records (record_date);
        CREATE INDEX IF NOT EXISTS idx_health_records_record_type
            ON health_records (record_type);
        CREATE INDEX IF NOT EXISTS idx_food_recipe_ingredients_recipe
            ON food_recipe_ingredients (recipe_id);
        CREATE INDEX IF NOT EXISTS idx_meal_logs_human_name
            ON meal_logs (human_name);
        CREATE INDEX IF NOT EXISTS idx_meal_logs_log_date
            ON meal_logs (log_date);
        CREATE TABLE IF NOT EXISTS fridge_inventory (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            food_name       TEXT    NOT NULL,
            quantity        REAL    NOT NULL,
            unit            TEXT    NOT NULL DEFAULT 'g'
                CHECK (unit IN ('g', 'kg', 'pieces', 'ml', 'l')),
            location        TEXT    NOT NULL DEFAULT 'fridge'
                CHECK (location IN ('fridge', 'freezer', 'pantry', 'other')),
            added_date      TEXT    NOT NULL,
            expiry_date     TEXT,
            notes           TEXT,
            created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
            updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_exercise_entries_human_name
            ON exercise_entries (human_name);
        CREATE INDEX IF NOT EXISTS idx_exercise_entries_date
            ON exercise_entries (exercise_date);
        CREATE INDEX IF NOT EXISTS idx_fridge_inventory_location
            ON fridge_inventory (location);
        CREATE INDEX IF NOT EXISTS idx_fridge_inventory_expiry
            ON fridge_inventory (expiry_date);
    """)

    conn.commit()
