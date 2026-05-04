"""Tests for MealLogRepository."""

from datetime import date
from pathlib import Path

import pytest

from nira_backend.data_models.exercise import MealLog
from nira_backend.database.connection import DatabaseConnection
from nira_backend.database.repositories.meal_repository import MealLogRepository


@pytest.fixture
def db(tmp_path: Path) -> DatabaseConnection:
    return DatabaseConnection(db_path=tmp_path / "meal_test.db")


@pytest.fixture
def repo(db: DatabaseConnection) -> MealLogRepository:
    return MealLogRepository(db)


@pytest.fixture
def today() -> date:
    return date.today()


@pytest.fixture
def breakfast(today: date) -> MealLog:
    return MealLog(
        human_name="Alice",
        food_name="Oatmeal",
        quantity_g=250.0,
        meal_type="breakfast",
        log_date=today,
        notes="With blueberries",
    )


@pytest.fixture
def lunch(today: date) -> MealLog:
    return MealLog(
        human_name="Bob",
        food_name="Chicken salad",
        quantity_g=350.0,
        meal_type="lunch",
        log_date=today,
    )


class TestMealLogRepositoryCreate:
    def test_create_returns_integer_id(
        self, repo: MealLogRepository, breakfast: MealLog
    ) -> None:
        record_id = repo.create(breakfast)
        assert isinstance(record_id, int)
        assert record_id >= 1

    def test_create_sequential_ids(
        self, repo: MealLogRepository, breakfast: MealLog, lunch: MealLog
    ) -> None:
        id1 = repo.create(breakfast)
        id2 = repo.create(lunch)
        assert id2 > id1


class TestMealLogRepositoryRead:
    def test_get_by_id_returns_correct_log(
        self, repo: MealLogRepository, breakfast: MealLog, today: date
    ) -> None:
        record_id = repo.create(breakfast)
        fetched = repo.get_by_id(record_id)
        assert fetched is not None
        assert fetched.human_name == "Alice"
        assert fetched.food_name == "Oatmeal"
        assert fetched.quantity_g == 250.0
        assert fetched.meal_type == "breakfast"
        assert fetched.log_date == today
        assert fetched.notes == "With blueberries"

    def test_get_by_id_returns_none_for_missing(self, repo: MealLogRepository) -> None:
        assert repo.get_by_id(999) is None

    def test_get_all_returns_all_logs(
        self, repo: MealLogRepository, breakfast: MealLog, lunch: MealLog
    ) -> None:
        repo.create(breakfast)
        repo.create(lunch)
        all_logs = repo.get_all()
        assert len(all_logs) == 2

    def test_get_all_empty_returns_empty_list(self, repo: MealLogRepository) -> None:
        assert repo.get_all() == []

    def test_get_by_human_filters_correctly(
        self, repo: MealLogRepository, breakfast: MealLog, lunch: MealLog
    ) -> None:
        repo.create(breakfast)
        repo.create(lunch)
        alice_logs = repo.get_by_human("Alice", days=365)
        assert all(m.human_name == "Alice" for m in alice_logs)
        assert len(alice_logs) == 1

    def test_get_by_date_filters_correctly(
        self, repo: MealLogRepository, breakfast: MealLog, today: date
    ) -> None:
        repo.create(breakfast)
        logs = repo.get_by_date(today)
        assert len(logs) == 1
        assert logs[0].food_name == "Oatmeal"

    def test_get_by_date_returns_empty_for_wrong_date(
        self, repo: MealLogRepository, breakfast: MealLog
    ) -> None:
        repo.create(breakfast)
        from datetime import timedelta
        logs = repo.get_by_date(date.today() - timedelta(days=1))
        assert logs == []

    def test_log_without_notes_has_none(
        self, repo: MealLogRepository, lunch: MealLog
    ) -> None:
        record_id = repo.create(lunch)
        fetched = repo.get_by_id(record_id)
        assert fetched is not None
        assert fetched.notes is None


class TestMealLogRepositoryUpdate:
    def test_update_modifies_log(
        self, repo: MealLogRepository, breakfast: MealLog, today: date
    ) -> None:
        record_id = repo.create(breakfast)
        updated = MealLog(
            human_name="Alice",
            food_name="Granola",
            quantity_g=200.0,
            meal_type="breakfast",
            log_date=today,
        )
        assert repo.update(record_id, updated) is True
        fetched = repo.get_by_id(record_id)
        assert fetched is not None
        assert fetched.food_name == "Granola"
        assert fetched.quantity_g == 200.0

    def test_update_nonexistent_returns_false(
        self, repo: MealLogRepository, breakfast: MealLog
    ) -> None:
        assert repo.update(999, breakfast) is False


class TestMealLogRepositoryDelete:
    def test_delete_removes_log(
        self, repo: MealLogRepository, breakfast: MealLog
    ) -> None:
        record_id = repo.create(breakfast)
        assert repo.delete(record_id) is True
        assert repo.get_by_id(record_id) is None

    def test_delete_nonexistent_returns_false(self, repo: MealLogRepository) -> None:
        assert repo.delete(999) is False
