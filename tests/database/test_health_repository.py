"""Tests for HealthRecordRepository."""

import pytest
from datetime import date
from pathlib import Path

from nira_backend.data_models.health_record import (
    BloodGlucoseRecord,
    BloodPressureRecord,
    HeartRateRecord,
    HealthRecord,
    SleepRecord,
)
from nira_backend.database.connection import DatabaseConnection
from nira_backend.database.repositories.health_repository import HealthRecordRepository


@pytest.fixture
def db(tmp_path: Path) -> DatabaseConnection:
    return DatabaseConnection(db_path=tmp_path / "test.db")


@pytest.fixture
def repo(db: DatabaseConnection) -> HealthRecordRepository:
    return HealthRecordRepository(db)


@pytest.fixture
def bp_record() -> HealthRecord:
    return HealthRecord(
        human_name="John Doe",
        record_date=date(2024, 1, 15),
        record_type="blood_pressure",
        measurement=BloodPressureRecord(systolic_mmhg=120, diastolic_mmhg=80, pulse_bpm=72),
        notes="After rest",
    )


@pytest.fixture
def glucose_record() -> HealthRecord:
    return HealthRecord(
        human_name="Jane Smith",
        record_date=date(2024, 2, 10),
        record_type="blood_glucose",
        measurement=BloodGlucoseRecord(glucose_mmol_l=5.2, measurement_context="fasting"),
    )


class TestHealthRecordRepository:
    def test_create_returns_id(self, repo: HealthRecordRepository, bp_record: HealthRecord) -> None:
        rid = repo.create(bp_record)
        assert isinstance(rid, int)

    def test_get_by_id_blood_pressure(
        self, repo: HealthRecordRepository, bp_record: HealthRecord
    ) -> None:
        rid = repo.create(bp_record)
        retrieved = repo.get_by_id(rid)
        assert retrieved is not None
        assert retrieved.human_name == "John Doe"
        assert retrieved.record_type == "blood_pressure"
        assert isinstance(retrieved.measurement, BloodPressureRecord)
        assert retrieved.measurement.systolic_mmhg == 120
        assert retrieved.notes == "After rest"

    def test_get_by_id_blood_glucose(
        self, repo: HealthRecordRepository, glucose_record: HealthRecord
    ) -> None:
        rid = repo.create(glucose_record)
        retrieved = repo.get_by_id(rid)
        assert retrieved is not None
        assert isinstance(retrieved.measurement, BloodGlucoseRecord)
        assert retrieved.measurement.glucose_mmol_l == 5.2

    def test_get_by_id_not_found(self, repo: HealthRecordRepository) -> None:
        assert repo.get_by_id(9999) is None

    def test_get_all_empty(self, repo: HealthRecordRepository) -> None:
        assert repo.get_all() == []

    def test_get_all(
        self,
        repo: HealthRecordRepository,
        bp_record: HealthRecord,
        glucose_record: HealthRecord,
    ) -> None:
        repo.create(bp_record)
        repo.create(glucose_record)
        all_records = repo.get_all()
        assert len(all_records) == 2

    def test_get_by_human_name(
        self,
        repo: HealthRecordRepository,
        bp_record: HealthRecord,
        glucose_record: HealthRecord,
    ) -> None:
        repo.create(bp_record)
        repo.create(glucose_record)
        results = repo.get_by_human_name("John")
        assert len(results) == 1
        assert results[0].human_name == "John Doe"

    def test_get_by_type(
        self,
        repo: HealthRecordRepository,
        bp_record: HealthRecord,
        glucose_record: HealthRecord,
    ) -> None:
        repo.create(bp_record)
        repo.create(glucose_record)
        results = repo.get_by_type("blood_pressure")
        assert len(results) == 1
        assert results[0].record_type == "blood_pressure"

    def test_get_by_date_range(self, repo: HealthRecordRepository, bp_record: HealthRecord) -> None:
        repo.create(bp_record)
        results = repo.get_by_date_range(date(2024, 1, 1), date(2024, 1, 31))
        assert len(results) == 1

    def test_get_by_date_range_outside(
        self, repo: HealthRecordRepository, bp_record: HealthRecord
    ) -> None:
        repo.create(bp_record)
        results = repo.get_by_date_range(date(2023, 1, 1), date(2023, 12, 31))
        assert len(results) == 0

    def test_update(self, repo: HealthRecordRepository, bp_record: HealthRecord) -> None:
        rid = repo.create(bp_record)
        updated = HealthRecord(
            human_name="John Doe",
            record_date=date(2024, 1, 15),
            record_type="blood_pressure",
            measurement=BloodPressureRecord(systolic_mmhg=118, diastolic_mmhg=76),
            notes="Updated note",
        )
        assert repo.update(rid, updated) is True
        retrieved = repo.get_by_id(rid)
        assert retrieved is not None
        assert isinstance(retrieved.measurement, BloodPressureRecord)
        assert retrieved.measurement.systolic_mmhg == 118
        assert retrieved.notes == "Updated note"

    def test_update_not_found(self, repo: HealthRecordRepository, bp_record: HealthRecord) -> None:
        assert repo.update(9999, bp_record) is False

    def test_delete(self, repo: HealthRecordRepository, bp_record: HealthRecord) -> None:
        rid = repo.create(bp_record)
        assert repo.delete(rid) is True
        assert repo.get_by_id(rid) is None

    def test_delete_not_found(self, repo: HealthRecordRepository) -> None:
        assert repo.delete(9999) is False

    def test_heart_rate_roundtrip(self, repo: HealthRecordRepository) -> None:
        record = HealthRecord(
            human_name="Alice",
            record_date=date(2024, 3, 5),
            record_type="heart_rate",
            measurement=HeartRateRecord(bpm=65, measurement_context="resting"),
        )
        rid = repo.create(record)
        retrieved = repo.get_by_id(rid)
        assert retrieved is not None
        assert isinstance(retrieved.measurement, HeartRateRecord)
        assert retrieved.measurement.bpm == 65

    def test_sleep_roundtrip(self, repo: HealthRecordRepository) -> None:
        record = HealthRecord(
            human_name="Bob",
            record_date=date(2024, 3, 6),
            record_type="sleep",
            measurement=SleepRecord(duration_hours=7.5, quality=4),
        )
        rid = repo.create(record)
        retrieved = repo.get_by_id(rid)
        assert retrieved is not None
        assert isinstance(retrieved.measurement, SleepRecord)
        assert retrieved.measurement.duration_hours == 7.5
