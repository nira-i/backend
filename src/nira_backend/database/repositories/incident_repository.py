"""Repository for HealthIncident data model."""

import json
from datetime import date, timedelta
from typing import Optional

from nira_backend.data_models.health_incident import HealthIncident
from nira_backend.database.repositories.base_repository import BaseRepository


class HealthIncidentRepository(BaseRepository[HealthIncident]):
    """CRUD operations for :class:`~nira_backend.data_models.health_incident.HealthIncident`."""

    _TABLE = "health_incidents"

    def create(self, model: HealthIncident) -> int:
        with self._db.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO health_incidents
                    (human_name, incident_date, description, symptoms,
                     severity, body_part, incident_type, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    model.human_name,
                    model.incident_date.isoformat(),
                    model.description,
                    json.dumps(model.symptoms) if model.symptoms else "[]",
                    model.severity,
                    model.body_part,
                    model.incident_type,
                    model.notes,
                ),
            )
            return cursor.lastrowid  # type: ignore[return-value]

    def get_by_id(self, record_id: int) -> Optional[HealthIncident]:
        with self._db.get_cursor() as cursor:
            cursor.execute("SELECT * FROM health_incidents WHERE id = ?", (record_id,))
            row = cursor.fetchone()
        return self._row_to_model(row) if row else None

    def get_all(self) -> list[HealthIncident]:
        with self._db.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM health_incidents ORDER BY incident_date DESC"
            )
            rows = cursor.fetchall()
        return [self._row_to_model(row) for row in rows]

    def get_by_human(self, human_name: str, days: int = 30) -> list[HealthIncident]:
        """Return incidents for a person within the last ``days`` days."""
        since = (date.today() - timedelta(days=days)).isoformat()
        with self._db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM health_incidents
                WHERE human_name LIKE ?
                  AND incident_date >= ?
                ORDER BY incident_date DESC
                """,
                (f"%{human_name}%", since),
            )
            rows = cursor.fetchall()
        return [self._row_to_model(row) for row in rows]

    def get_by_type(self, incident_type: str) -> list[HealthIncident]:
        """Return all incidents of a given type."""
        with self._db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM health_incidents
                WHERE incident_type = ?
                ORDER BY incident_date DESC
                """,
                (incident_type,),
            )
            rows = cursor.fetchall()
        return [self._row_to_model(row) for row in rows]

    def get_by_body_part(self, body_part: str) -> list[HealthIncident]:
        """Return incidents affecting a specific body part (case-insensitive)."""
        with self._db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM health_incidents
                WHERE body_part LIKE ?
                ORDER BY incident_date DESC
                """,
                (f"%{body_part.lower()}%",),
            )
            rows = cursor.fetchall()
        return [self._row_to_model(row) for row in rows]

    def update(self, record_id: int, model: HealthIncident) -> bool:
        with self._db.get_cursor() as cursor:
            if not self._row_exists(cursor, self._TABLE, record_id):
                return False
            cursor.execute(
                """
                UPDATE health_incidents
                SET human_name = ?, incident_date = ?, description = ?,
                    symptoms = ?, severity = ?, body_part = ?,
                    incident_type = ?, notes = ?
                WHERE id = ?
                """,
                (
                    model.human_name,
                    model.incident_date.isoformat(),
                    model.description,
                    json.dumps(model.symptoms) if model.symptoms else "[]",
                    model.severity,
                    model.body_part,
                    model.incident_type,
                    model.notes,
                    record_id,
                ),
            )
            return True

    def delete(self, record_id: int) -> bool:
        with self._db.get_cursor() as cursor:
            if not self._row_exists(cursor, self._TABLE, record_id):
                return False
            cursor.execute("DELETE FROM health_incidents WHERE id = ?", (record_id,))
            return True

    @staticmethod
    def _row_to_model(row: object) -> HealthIncident:
        raw_symptoms = row["symptoms"]  # type: ignore[index]
        try:
            symptoms = json.loads(raw_symptoms) if raw_symptoms else []
        except (json.JSONDecodeError, TypeError):
            symptoms = []
        return HealthIncident(
            human_name=row["human_name"],  # type: ignore[index]
            incident_date=date.fromisoformat(row["incident_date"]),  # type: ignore[index]
            description=row["description"],  # type: ignore[index]
            symptoms=symptoms,
            severity=row["severity"],  # type: ignore[index]
            body_part=row["body_part"],  # type: ignore[index]
            incident_type=row["incident_type"],  # type: ignore[index]
            notes=row["notes"],  # type: ignore[index]
        )
