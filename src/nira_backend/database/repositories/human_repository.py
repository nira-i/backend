"""Repository for Human data model."""

from datetime import date
from typing import Optional

from nira_backend.data_models.human import Human
from nira_backend.database.repositories.base_repository import BaseRepository


class HumanRepository(BaseRepository[Human]):
    """CRUD operations for :class:`~nira_backend.data_models.human.Human` records."""

    _TABLE = "humans"

    def create(self, model: Human) -> int:
        with self._db.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO humans (name, gender, date_of_birth, weight_kg, height_cm)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    model.name,
                    model.gender,
                    model.date_of_birth.isoformat(),
                    model.weight,
                    model.height,
                ),
            )
            return cursor.lastrowid  # type: ignore[return-value]

    def get_by_id(self, record_id: int) -> Optional[Human]:
        with self._db.get_cursor() as cursor:
            cursor.execute("SELECT * FROM humans WHERE id = ?", (record_id,))
            row = cursor.fetchone()
        return self._row_to_model(row) if row else None

    def get_all(self) -> list[Human]:
        with self._db.get_cursor() as cursor:
            cursor.execute("SELECT * FROM humans ORDER BY name")
            rows = cursor.fetchall()
        return [self._row_to_model(row) for row in rows]

    def get_by_name(self, name: str) -> list[Human]:
        """Return all humans whose name matches (case-insensitive)."""
        with self._db.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM humans WHERE name LIKE ? ORDER BY name",
                (f"%{name}%",),
            )
            rows = cursor.fetchall()
        return [self._row_to_model(row) for row in rows]

    def update(self, record_id: int, model: Human) -> bool:
        with self._db.get_cursor() as cursor:
            if not self._row_exists(cursor, self._TABLE, record_id):
                return False
            cursor.execute(
                """
                UPDATE humans
                SET name = ?, gender = ?, date_of_birth = ?, weight_kg = ?, height_cm = ?,
                    updated_at = datetime('now')
                WHERE id = ?
                """,
                (
                    model.name,
                    model.gender,
                    model.date_of_birth.isoformat(),
                    model.weight,
                    model.height,
                    record_id,
                ),
            )
            return True

    def delete(self, record_id: int) -> bool:
        with self._db.get_cursor() as cursor:
            if not self._row_exists(cursor, self._TABLE, record_id):
                return False
            cursor.execute("DELETE FROM humans WHERE id = ?", (record_id,))
            return True

    @staticmethod
    def _row_to_model(row: object) -> Human:
        return Human(
            name=row["name"],  # type: ignore[index]
            gender=row["gender"],  # type: ignore[index]
            date_of_birth=date.fromisoformat(row["date_of_birth"]),  # type: ignore[index]
            weight=row["weight_kg"],  # type: ignore[index]
            height=row["height_cm"],  # type: ignore[index]
        )
