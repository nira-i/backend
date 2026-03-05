"""Tests for HumanRepository."""

import pytest
from datetime import date
from pathlib import Path

from nira_backend.data_models.human import Human
from nira_backend.database.connection import DatabaseConnection
from nira_backend.database.repositories.human_repository import HumanRepository


@pytest.fixture
def db(tmp_path: Path) -> DatabaseConnection:
    return DatabaseConnection(db_path=tmp_path / "test.db")


@pytest.fixture
def repo(db: DatabaseConnection) -> HumanRepository:
    return HumanRepository(db)


@pytest.fixture
def john() -> Human:
    return Human(
        name="John Doe",
        gender="male",
        date_of_birth=date(1990, 5, 15),
        weight=75.0,
        height=178.0,
    )


@pytest.fixture
def jane() -> Human:
    return Human(
        name="Jane Smith",
        gender="female",
        date_of_birth=date(1985, 3, 20),
        weight=60.0,
        height=165.0,
    )


class TestHumanRepository:
    def test_create_returns_id(self, repo: HumanRepository, john: Human) -> None:
        record_id = repo.create(john)
        assert isinstance(record_id, int)
        assert record_id >= 1

    def test_get_by_id(self, repo: HumanRepository, john: Human) -> None:
        record_id = repo.create(john)
        retrieved = repo.get_by_id(record_id)
        assert retrieved is not None
        assert retrieved.name == "John Doe"
        assert retrieved.gender == "male"
        assert retrieved.date_of_birth == date(1990, 5, 15)

    def test_get_by_id_not_found(self, repo: HumanRepository) -> None:
        assert repo.get_by_id(9999) is None

    def test_get_all_empty(self, repo: HumanRepository) -> None:
        assert repo.get_all() == []

    def test_get_all_multiple(self, repo: HumanRepository, john: Human, jane: Human) -> None:
        repo.create(john)
        repo.create(jane)
        all_humans = repo.get_all()
        assert len(all_humans) == 2

    def test_get_by_name(self, repo: HumanRepository, john: Human, jane: Human) -> None:
        repo.create(john)
        repo.create(jane)
        results = repo.get_by_name("John")
        assert len(results) == 1
        assert results[0].name == "John Doe"

    def test_update(self, repo: HumanRepository, john: Human) -> None:
        record_id = repo.create(john)
        updated = Human(
            name="John Updated",
            gender="male",
            date_of_birth=date(1990, 5, 15),
            weight=80.0,
            height=178.0,
        )
        result = repo.update(record_id, updated)
        assert result is True
        retrieved = repo.get_by_id(record_id)
        assert retrieved is not None
        assert retrieved.name == "John Updated"
        assert retrieved.weight == 80.0

    def test_update_not_found(self, repo: HumanRepository, john: Human) -> None:
        assert repo.update(9999, john) is False

    def test_delete(self, repo: HumanRepository, john: Human) -> None:
        record_id = repo.create(john)
        result = repo.delete(record_id)
        assert result is True
        assert repo.get_by_id(record_id) is None

    def test_delete_not_found(self, repo: HumanRepository) -> None:
        assert repo.delete(9999) is False

    def test_bmi_preserved(self, repo: HumanRepository, john: Human) -> None:
        record_id = repo.create(john)
        retrieved = repo.get_by_id(record_id)
        assert retrieved is not None
        assert abs(retrieved.bmi - john.bmi) < 0.01
