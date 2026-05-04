"""Repository for FridgeItem data model."""

from datetime import date
from typing import Optional

from nira_backend.data_models.food_inventory import FridgeItem
from nira_backend.database.repositories.base_repository import BaseRepository


class FridgeInventoryRepository(BaseRepository[FridgeItem]):
    """CRUD operations for :class:`~nira_backend.data_models.food_inventory.FridgeItem`."""

    _TABLE = "fridge_inventory"

    def create(self, model: FridgeItem) -> int:
        with self._db.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO fridge_inventory
                    (food_name, quantity, unit, location, added_date, expiry_date, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    model.food_name,
                    model.quantity,
                    model.unit,
                    model.location,
                    model.added_date.isoformat(),
                    model.expiry_date.isoformat() if model.expiry_date else None,
                    model.notes,
                ),
            )
            return cursor.lastrowid  # type: ignore[return-value]

    def get_by_id(self, record_id: int) -> Optional[FridgeItem]:
        with self._db.get_cursor() as cursor:
            cursor.execute("SELECT * FROM fridge_inventory WHERE id = ?", (record_id,))
            row = cursor.fetchone()
        return self._row_to_model(row) if row else None

    def get_all(self) -> list[FridgeItem]:
        with self._db.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM fridge_inventory ORDER BY location, food_name"
            )
            rows = cursor.fetchall()
        return [self._row_to_model(row) for row in rows]

    def get_by_location(self, location: str) -> list[FridgeItem]:
        """Return all items in a given storage location."""
        with self._db.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM fridge_inventory WHERE location = ? ORDER BY food_name",
                (location,),
            )
            rows = cursor.fetchall()
        return [self._row_to_model(row) for row in rows]

    def search_by_name(self, query: str) -> list[FridgeItem]:
        """Case-insensitive substring search by food name."""
        with self._db.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM fridge_inventory WHERE food_name LIKE ? ORDER BY food_name",
                (f"%{query}%",),
            )
            rows = cursor.fetchall()
        return [self._row_to_model(row) for row in rows]

    def get_expiring_soon(self, days: int = 3) -> list[FridgeItem]:
        """Return items that expire within the next ``days`` days (including today)."""
        with self._db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM fridge_inventory
                WHERE expiry_date IS NOT NULL
                  AND expiry_date <= date('now', ? || ' days')
                ORDER BY expiry_date, food_name
                """,
                (f"+{days}",),
            )
            rows = cursor.fetchall()
        return [self._row_to_model(row) for row in rows]

    def get_expired(self) -> list[FridgeItem]:
        """Return all items that have already expired."""
        with self._db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM fridge_inventory
                WHERE expiry_date IS NOT NULL
                  AND expiry_date < date('now')
                ORDER BY expiry_date
                """,
            )
            rows = cursor.fetchall()
        return [self._row_to_model(row) for row in rows]

    def update(self, record_id: int, model: FridgeItem) -> bool:
        with self._db.get_cursor() as cursor:
            if not self._row_exists(cursor, self._TABLE, record_id):
                return False
            cursor.execute(
                """
                UPDATE fridge_inventory
                SET food_name = ?, quantity = ?, unit = ?, location = ?,
                    added_date = ?, expiry_date = ?, notes = ?,
                    updated_at = datetime('now')
                WHERE id = ?
                """,
                (
                    model.food_name,
                    model.quantity,
                    model.unit,
                    model.location,
                    model.added_date.isoformat(),
                    model.expiry_date.isoformat() if model.expiry_date else None,
                    model.notes,
                    record_id,
                ),
            )
            return True

    def update_quantity(self, record_id: int, new_quantity: float) -> bool:
        """Convenience method to update just the quantity of an item."""
        with self._db.get_cursor() as cursor:
            if not self._row_exists(cursor, self._TABLE, record_id):
                return False
            cursor.execute(
                """
                UPDATE fridge_inventory
                SET quantity = ?, updated_at = datetime('now')
                WHERE id = ?
                """,
                (new_quantity, record_id),
            )
            return True

    def delete(self, record_id: int) -> bool:
        with self._db.get_cursor() as cursor:
            if not self._row_exists(cursor, self._TABLE, record_id):
                return False
            cursor.execute("DELETE FROM fridge_inventory WHERE id = ?", (record_id,))
            return True

    @staticmethod
    def _row_to_model(row: object) -> FridgeItem:
        expiry_raw = row["expiry_date"]  # type: ignore[index]
        return FridgeItem(
            food_name=row["food_name"],  # type: ignore[index]
            quantity=row["quantity"],  # type: ignore[index]
            unit=row["unit"],  # type: ignore[index]
            location=row["location"],  # type: ignore[index]
            added_date=date.fromisoformat(row["added_date"]),  # type: ignore[index]
            expiry_date=date.fromisoformat(expiry_raw) if expiry_raw else None,
            notes=row["notes"],  # type: ignore[index]
        )
