"""Tests for ExerciseRepository."""

from datetime import date
from pathlib import Path

import pytest

from nira_backend.data_models.exercise import ExerciseEntry
from nira_backend.database.connection import DatabaseConnection
from nira_backend.database.repositories.exercise_repository import ExerciseRepository


@pytest.fixture
def db(tmp_path: Path) -> DatabaseConnection:
    return DatabaseConnection(db_path=tmp_path / "exercise_test.db")


@pytest.fixture
def repo(db: DatabaseConnection) -> ExerciseRepository:
    return ExerciseRepository(db)


@pytest.fixture
def run_entry() -> ExerciseEntry:
    return ExerciseEntry(
        human_name="Alice",
        exercise_date=date(2024, 1, 15),
        activity="running",
        duration_minutes=30,
        intensity="moderate",
        calories_burned=300.0,
        distance_km=5.0,
        notes="Morning run",
    )


@pytest.fixture
def yoga_entry() -> ExerciseEntry:
    return ExerciseEntry(
        human_name="Bob",
        exercise_date=date(2024, 1, 15),
        activity="yoga",
        duration_minutes=60,
        intensity="light",
    )


class TestExerciseRepositoryCreate:
    def test_create_returns_integer_id(
        self, repo: ExerciseRepository, run_entry: ExerciseEntry
    ) -> None:
        record_id = repo.create(run_entry)
        assert isinstance(record_id, int)
        assert record_id >= 1

    def test_create_assigns_sequential_ids(
        self, repo: ExerciseRepository, run_entry: ExerciseEntry, yoga_entry: ExerciseEntry
    ) -> None:
        id1 = repo.create(run_entry)
        id2 = repo.create(yoga_entry)
        assert id2 > id1


class TestExerciseRepositoryRead:
    def test_get_by_id_returns_correct_entry(
        self, repo: ExerciseRepository, run_entry: ExerciseEntry
    ) -> None:
        record_id = repo.create(run_entry)
        fetched = repo.get_by_id(record_id)
        assert fetched is not None
        assert fetched.human_name == "Alice"
        assert fetched.activity == "running"
        assert fetched.duration_minutes == 30
        assert fetched.intensity == "moderate"
        assert fetched.calories_burned == 300.0
        assert fetched.distance_km == 5.0
        assert fetched.notes == "Morning run"

    def test_get_by_id_returns_none_for_missing(
        self, repo: ExerciseRepository
    ) -> None:
        assert repo.get_by_id(999) is None

    def test_get_all_returns_all_entries(
        self, repo: ExerciseRepository, run_entry: ExerciseEntry, yoga_entry: ExerciseEntry
    ) -> None:
        repo.create(run_entry)
        repo.create(yoga_entry)
        all_entries = repo.get_all()
        assert len(all_entries) == 2

    def test_get_all_empty_returns_empty_list(self, repo: ExerciseRepository) -> None:
        assert repo.get_all() == []

    def test_get_by_human_filters_by_name(
        self, repo: ExerciseRepository, run_entry: ExerciseEntry, yoga_entry: ExerciseEntry
    ) -> None:
        repo.create(run_entry)
        repo.create(yoga_entry)
        alice_entries = repo.get_by_human("Alice", days=365)
        assert all(e.human_name == "Alice" for e in alice_entries)

    def test_get_by_activity_filters_correctly(
        self, repo: ExerciseRepository, run_entry: ExerciseEntry, yoga_entry: ExerciseEntry
    ) -> None:
        repo.create(run_entry)
        repo.create(yoga_entry)
        runs = repo.get_by_activity("running")
        assert len(runs) == 1
        assert runs[0].activity == "running"

    def test_entry_with_optional_fields_none(
        self, repo: ExerciseRepository, yoga_entry: ExerciseEntry
    ) -> None:
        record_id = repo.create(yoga_entry)
        fetched = repo.get_by_id(record_id)
        assert fetched is not None
        assert fetched.calories_burned is None
        assert fetched.distance_km is None
        assert fetched.notes is None


class TestExerciseRepositoryUpdate:
    def test_update_modifies_entry(
        self, repo: ExerciseRepository, run_entry: ExerciseEntry
    ) -> None:
        record_id = repo.create(run_entry)
        updated = ExerciseEntry(
            human_name="Alice",
            exercise_date=date(2024, 1, 15),
            activity="cycling",
            duration_minutes=45,
            intensity="vigorous",
        )
        assert repo.update(record_id, updated) is True
        fetched = repo.get_by_id(record_id)
        assert fetched is not None
        assert fetched.activity == "cycling"
        assert fetched.duration_minutes == 45

    def test_update_nonexistent_returns_false(
        self, repo: ExerciseRepository, run_entry: ExerciseEntry
    ) -> None:
        assert repo.update(999, run_entry) is False


class TestExerciseRepositoryDelete:
    def test_delete_removes_entry(
        self, repo: ExerciseRepository, run_entry: ExerciseEntry
    ) -> None:
        record_id = repo.create(run_entry)
        assert repo.delete(record_id) is True
        assert repo.get_by_id(record_id) is None

    def test_delete_nonexistent_returns_false(self, repo: ExerciseRepository) -> None:
        assert repo.delete(999) is False
