"""Repository for ExerciseEntry data model."""

from datetime import date
from typing import Optional

from nira_backend.data_models.exercise import ExerciseEntry
from nira_backend.database.repositories.base_repository import BaseRepository


class ExerciseRepository(BaseRepository[ExerciseEntry]):
    """CRUD operations for :class:`~nira_backend.data_models.exercise.ExerciseEntry`."""

    _TABLE = "exercise_entries"

    def create(self, model: ExerciseEntry) -> int:
        with self._db.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO exercise_entries
                    (human_name, exercise_date, activity, duration_minutes,
                     intensity, calories_burned, distance_km, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    model.human_name,
                    model.exercise_date.isoformat(),
                    model.activity,
                    model.duration_minutes,
                    model.intensity,
                    model.calories_burned,
                    model.distance_km,
                    model.notes,
                ),
            )
            return cursor.lastrowid  # type: ignore[return-value]

    def get_by_id(self, record_id: int) -> Optional[ExerciseEntry]:
        with self._db.get_cursor() as cursor:
            cursor.execute("SELECT * FROM exercise_entries WHERE id = ?", (record_id,))
            row = cursor.fetchone()
        return self._row_to_model(row) if row else None

    def get_all(self) -> list[ExerciseEntry]:
        with self._db.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM exercise_entries ORDER BY exercise_date DESC, id DESC"
            )
            rows = cursor.fetchall()
        return [self._row_to_model(row) for row in rows]

    def get_by_human(self, human_name: str, days: int = 7) -> list[ExerciseEntry]:
        """Return exercise entries for a person over the last N days."""
        with self._db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM exercise_entries
                WHERE human_name LIKE ?
                  AND exercise_date >= date('now', ? || ' days')
                ORDER BY exercise_date DESC, id DESC
                """,
                (f"%{human_name}%", f"-{days}"),
            )
            rows = cursor.fetchall()
        return [self._row_to_model(row) for row in rows]

    def get_by_activity(self, activity: str) -> list[ExerciseEntry]:
        """Return all entries for a given activity (case-insensitive substring)."""
        with self._db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM exercise_entries
                WHERE activity LIKE ?
                ORDER BY exercise_date DESC
                """,
                (f"%{activity}%",),
            )
            rows = cursor.fetchall()
        return [self._row_to_model(row) for row in rows]

    def update(self, record_id: int, model: ExerciseEntry) -> bool:
        with self._db.get_cursor() as cursor:
            if not self._row_exists(cursor, self._TABLE, record_id):
                return False
            cursor.execute(
                """
                UPDATE exercise_entries
                SET human_name = ?, exercise_date = ?, activity = ?,
                    duration_minutes = ?, intensity = ?, calories_burned = ?,
                    distance_km = ?, notes = ?
                WHERE id = ?
                """,
                (
                    model.human_name,
                    model.exercise_date.isoformat(),
                    model.activity,
                    model.duration_minutes,
                    model.intensity,
                    model.calories_burned,
                    model.distance_km,
                    model.notes,
                    record_id,
                ),
            )
            return True

    def delete(self, record_id: int) -> bool:
        with self._db.get_cursor() as cursor:
            if not self._row_exists(cursor, self._TABLE, record_id):
                return False
            cursor.execute("DELETE FROM exercise_entries WHERE id = ?", (record_id,))
            return True

    @staticmethod
    def _row_to_model(row: object) -> ExerciseEntry:
        return ExerciseEntry(
            human_name=row["human_name"],  # type: ignore[index]
            exercise_date=date.fromisoformat(row["exercise_date"]),  # type: ignore[index]
            activity=row["activity"],  # type: ignore[index]
            duration_minutes=row["duration_minutes"],  # type: ignore[index]
            intensity=row["intensity"],  # type: ignore[index]
            calories_burned=row["calories_burned"],  # type: ignore[index]
            distance_km=row["distance_km"],  # type: ignore[index]
            notes=row["notes"],  # type: ignore[index]
        )
