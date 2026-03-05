"""Repository for HealthRecord data model."""

import json
from datetime import date
from typing import Optional

from nira_backend.data_models.health_record import (
    BloodGlucoseRecord,
    BloodPressureRecord,
    HeartRateRecord,
    HealthRecord,
    SleepRecord,
)
from nira_backend.database.repositories.base_repository import BaseRepository

_RECORD_TYPE_MAP = {
    "blood_pressure": BloodPressureRecord,
    "blood_glucose": BloodGlucoseRecord,
    "heart_rate": HeartRateRecord,
    "sleep": SleepRecord,
}


class HealthRecordRepository(BaseRepository[HealthRecord]):
    """CRUD operations for :class:`~nira_backend.data_models.health_record.HealthRecord`."""

    _TABLE = "health_records"

    def create(self, model: HealthRecord) -> int:
        with self._db.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO health_records
                    (human_name, record_date, record_type, measurement, notes)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    model.human_name,
                    model.record_date.isoformat(),
                    model.record_type,
                    model.measurement.model_dump_json(),
                    model.notes,
                ),
            )
            return cursor.lastrowid  # type: ignore[return-value]

    def get_by_id(self, record_id: int) -> Optional[HealthRecord]:
        with self._db.get_cursor() as cursor:
            cursor.execute("SELECT * FROM health_records WHERE id = ?", (record_id,))
            row = cursor.fetchone()
        return self._row_to_model(row) if row else None

    def get_all(self) -> list[HealthRecord]:
        with self._db.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM health_records ORDER BY record_date DESC, id DESC"
            )
            rows = cursor.fetchall()
        return [self._row_to_model(row) for row in rows]

    def get_by_human_name(self, name: str) -> list[HealthRecord]:
        """Return all health records for a given person (case-insensitive substring)."""
        with self._db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM health_records
                WHERE human_name LIKE ?
                ORDER BY record_date DESC, id DESC
                """,
                (f"%{name}%",),
            )
            rows = cursor.fetchall()
        return [self._row_to_model(row) for row in rows]

    def get_by_type(self, record_type: str) -> list[HealthRecord]:
        """Return all health records of a given type."""
        with self._db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM health_records
                WHERE record_type = ?
                ORDER BY record_date DESC, id DESC
                """,
                (record_type,),
            )
            rows = cursor.fetchall()
        return [self._row_to_model(row) for row in rows]

    def get_by_date_range(
        self, start_date: date, end_date: date
    ) -> list[HealthRecord]:
        """Return health records within an inclusive date range."""
        with self._db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM health_records
                WHERE record_date BETWEEN ? AND ?
                ORDER BY record_date DESC, id DESC
                """,
                (start_date.isoformat(), end_date.isoformat()),
            )
            rows = cursor.fetchall()
        return [self._row_to_model(row) for row in rows]

    def update(self, record_id: int, model: HealthRecord) -> bool:
        with self._db.get_cursor() as cursor:
            if not self._row_exists(cursor, self._TABLE, record_id):
                return False
            cursor.execute(
                """
                UPDATE health_records
                SET human_name = ?, record_date = ?, record_type = ?,
                    measurement = ?, notes = ?
                WHERE id = ?
                """,
                (
                    model.human_name,
                    model.record_date.isoformat(),
                    model.record_type,
                    model.measurement.model_dump_json(),
                    model.notes,
                    record_id,
                ),
            )
            return True

    def delete(self, record_id: int) -> bool:
        with self._db.get_cursor() as cursor:
            if not self._row_exists(cursor, self._TABLE, record_id):
                return False
            cursor.execute("DELETE FROM health_records WHERE id = ?", (record_id,))
            return True

    @staticmethod
    def _row_to_model(row: object) -> HealthRecord:
        record_type: str = row["record_type"]  # type: ignore[index]
        model_class = _RECORD_TYPE_MAP[record_type]
        measurement_data = json.loads(row["measurement"])  # type: ignore[index]
        measurement = model_class(**measurement_data)
        return HealthRecord(
            human_name=row["human_name"],  # type: ignore[index]
            record_date=date.fromisoformat(row["record_date"]),  # type: ignore[index]
            record_type=record_type,  # type: ignore[arg-type]
            measurement=measurement,
            notes=row["notes"],  # type: ignore[index]
        )
