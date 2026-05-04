"""Repository for MealLog data model."""

from datetime import date
from typing import Optional

from nira_backend.data_models.exercise import MealLog
from nira_backend.database.repositories.base_repository import BaseRepository


class MealLogRepository(BaseRepository[MealLog]):
    """CRUD operations for :class:`~nira_backend.data_models.exercise.MealLog`."""

    _TABLE = "meal_logs"

    def create(self, model: MealLog) -> int:
        with self._db.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO meal_logs (human_name, food_name, quantity_g, meal_type, log_date, notes)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    model.human_name,
                    model.food_name,
                    model.quantity_g,
                    model.meal_type,
                    model.log_date.isoformat(),
                    model.notes,
                ),
            )
            return cursor.lastrowid  # type: ignore[return-value]

    def get_by_id(self, record_id: int) -> Optional[MealLog]:
        with self._db.get_cursor() as cursor:
            cursor.execute("SELECT * FROM meal_logs WHERE id = ?", (record_id,))
            row = cursor.fetchone()
        return self._row_to_model(row) if row else None

    def get_all(self) -> list[MealLog]:
        with self._db.get_cursor() as cursor:
            cursor.execute("SELECT * FROM meal_logs ORDER BY log_date DESC, id DESC")
            rows = cursor.fetchall()
        return [self._row_to_model(row) for row in rows]

    def get_by_human(self, human_name: str, days: int = 7) -> list[MealLog]:
        """Return meal logs for a person over the last N days."""
        with self._db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM meal_logs
                WHERE human_name LIKE ?
                  AND log_date >= date('now', ? || ' days')
                ORDER BY log_date DESC, id DESC
                """,
                (f"%{human_name}%", f"-{days}"),
            )
            rows = cursor.fetchall()
        return [self._row_to_model(row) for row in rows]

    def get_by_date(self, log_date: date) -> list[MealLog]:
        """Return all meal logs for a specific date."""
        with self._db.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM meal_logs WHERE log_date = ? ORDER BY id",
                (log_date.isoformat(),),
            )
            rows = cursor.fetchall()
        return [self._row_to_model(row) for row in rows]

    def update(self, record_id: int, model: MealLog) -> bool:
        with self._db.get_cursor() as cursor:
            if not self._row_exists(cursor, self._TABLE, record_id):
                return False
            cursor.execute(
                """
                UPDATE meal_logs
                SET human_name = ?, food_name = ?, quantity_g = ?,
                    meal_type = ?, log_date = ?, notes = ?
                WHERE id = ?
                """,
                (
                    model.human_name,
                    model.food_name,
                    model.quantity_g,
                    model.meal_type,
                    model.log_date.isoformat(),
                    model.notes,
                    record_id,
                ),
            )
            return True

    def delete(self, record_id: int) -> bool:
        with self._db.get_cursor() as cursor:
            if not self._row_exists(cursor, self._TABLE, record_id):
                return False
            cursor.execute("DELETE FROM meal_logs WHERE id = ?", (record_id,))
            return True

    @staticmethod
    def _row_to_model(row: object) -> MealLog:
        return MealLog(
            human_name=row["human_name"],  # type: ignore[index]
            food_name=row["food_name"],  # type: ignore[index]
            quantity_g=row["quantity_g"],  # type: ignore[index]
            meal_type=row["meal_type"],  # type: ignore[index]
            log_date=date.fromisoformat(row["log_date"]),  # type: ignore[index]
            notes=row["notes"],  # type: ignore[index]
        )
