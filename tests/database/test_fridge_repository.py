"""Tests for FridgeInventoryRepository."""

from datetime import date, timedelta
from pathlib import Path

import pytest

from nira_backend.data_models.food_inventory import FridgeItem
from nira_backend.database.connection import DatabaseConnection
from nira_backend.database.repositories.fridge_repository import FridgeInventoryRepository


@pytest.fixture
def db(tmp_path: Path) -> DatabaseConnection:
    return DatabaseConnection(db_path=tmp_path / "fridge_test.db")


@pytest.fixture
def repo(db: DatabaseConnection) -> FridgeInventoryRepository:
    return FridgeInventoryRepository(db)


@pytest.fixture
def eggs() -> FridgeItem:
    return FridgeItem(
        food_name="Eggs",
        quantity=6,
        unit="pieces",
        location="fridge",
        added_date=date.today(),
        expiry_date=date.today() + timedelta(days=14),
    )


@pytest.fixture
def broccoli() -> FridgeItem:
    return FridgeItem(
        food_name="Broccoli",
        quantity=500,
        unit="g",
        location="fridge",
        added_date=date.today(),
        expiry_date=date.today() + timedelta(days=2),
        notes="fresh",
    )


@pytest.fixture
def chicken() -> FridgeItem:
    return FridgeItem(
        food_name="Chicken breast",
        quantity=1.0,
        unit="kg",
        location="freezer",
        added_date=date.today(),
    )


@pytest.fixture
def oats() -> FridgeItem:
    return FridgeItem(
        food_name="Rolled oats",
        quantity=500,
        unit="g",
        location="pantry",
        added_date=date.today(),
    )


class TestFridgeRepositoryCreate:
    def test_create_returns_integer_id(
        self, repo: FridgeInventoryRepository, eggs: FridgeItem
    ) -> None:
        iid = repo.create(eggs)
        assert isinstance(iid, int)
        assert iid >= 1

    def test_create_multiple_items(
        self,
        repo: FridgeInventoryRepository,
        eggs: FridgeItem,
        chicken: FridgeItem,
    ) -> None:
        id1 = repo.create(eggs)
        id2 = repo.create(chicken)
        assert id2 > id1


class TestFridgeRepositoryRead:
    def test_get_by_id_returns_correct_item(
        self, repo: FridgeInventoryRepository, eggs: FridgeItem
    ) -> None:
        iid = repo.create(eggs)
        fetched = repo.get_by_id(iid)
        assert fetched is not None
        assert fetched.food_name == "Eggs"
        assert fetched.quantity == 6
        assert fetched.unit == "pieces"
        assert fetched.location == "fridge"
        assert fetched.expiry_date == eggs.expiry_date

    def test_get_by_id_returns_none_for_missing(
        self, repo: FridgeInventoryRepository
    ) -> None:
        assert repo.get_by_id(999) is None

    def test_get_all_returns_all_items(
        self, repo: FridgeInventoryRepository, eggs: FridgeItem, chicken: FridgeItem, oats: FridgeItem
    ) -> None:
        repo.create(eggs)
        repo.create(chicken)
        repo.create(oats)
        assert len(repo.get_all()) == 3

    def test_get_all_empty_returns_empty_list(
        self, repo: FridgeInventoryRepository
    ) -> None:
        assert repo.get_all() == []

    def test_get_by_location_filters_correctly(
        self,
        repo: FridgeInventoryRepository,
        eggs: FridgeItem,
        chicken: FridgeItem,
        oats: FridgeItem,
    ) -> None:
        repo.create(eggs)
        repo.create(chicken)
        repo.create(oats)
        fridge_items = repo.get_by_location("fridge")
        assert all(i.location == "fridge" for i in fridge_items)
        freezer_items = repo.get_by_location("freezer")
        assert len(freezer_items) == 1
        assert freezer_items[0].food_name == "Chicken breast"

    def test_search_by_name_case_insensitive(
        self, repo: FridgeInventoryRepository, eggs: FridgeItem
    ) -> None:
        repo.create(eggs)
        results = repo.search_by_name("egg")
        assert len(results) == 1
        assert results[0].food_name == "Eggs"

    def test_search_by_name_no_match(self, repo: FridgeInventoryRepository) -> None:
        assert repo.search_by_name("truffle") == []

    def test_item_without_expiry_has_none(
        self, repo: FridgeInventoryRepository, chicken: FridgeItem
    ) -> None:
        iid = repo.create(chicken)
        fetched = repo.get_by_id(iid)
        assert fetched is not None
        assert fetched.expiry_date is None

    def test_item_with_notes_preserved(
        self, repo: FridgeInventoryRepository, broccoli: FridgeItem
    ) -> None:
        iid = repo.create(broccoli)
        fetched = repo.get_by_id(iid)
        assert fetched is not None
        assert fetched.notes == "fresh"


class TestFridgeRepositoryExpiry:
    def test_get_expiring_soon_finds_item(
        self, repo: FridgeInventoryRepository, broccoli: FridgeItem
    ) -> None:
        repo.create(broccoli)
        expiring = repo.get_expiring_soon(days=3)
        assert len(expiring) == 1
        assert expiring[0].food_name == "Broccoli"

    def test_get_expiring_soon_excludes_far_future(
        self,
        repo: FridgeInventoryRepository,
        broccoli: FridgeItem,
        eggs: FridgeItem,
    ) -> None:
        repo.create(broccoli)
        repo.create(eggs)
        expiring = repo.get_expiring_soon(days=3)
        names = {i.food_name for i in expiring}
        assert "Broccoli" in names
        assert "Eggs" not in names

    def test_get_expiring_soon_excludes_no_expiry(
        self, repo: FridgeInventoryRepository, chicken: FridgeItem
    ) -> None:
        repo.create(chicken)
        expiring = repo.get_expiring_soon(days=365)
        assert all(i.food_name != "Chicken breast" for i in expiring)

    def test_get_expired_finds_past_expiry(
        self, repo: FridgeInventoryRepository
    ) -> None:
        expired_item = FridgeItem(
            food_name="Old yogurt",
            quantity=200,
            unit="g",
            location="fridge",
            added_date=date.today() - timedelta(days=10),
            expiry_date=date.today() - timedelta(days=2),
        )
        repo.create(expired_item)
        expired = repo.get_expired()
        assert len(expired) == 1
        assert expired[0].food_name == "Old yogurt"


class TestFridgeRepositoryUpdate:
    def test_update_modifies_item(
        self, repo: FridgeInventoryRepository, eggs: FridgeItem
    ) -> None:
        iid = repo.create(eggs)
        updated = FridgeItem(
            food_name="Eggs",
            quantity=4,
            unit="pieces",
            location="fridge",
            added_date=date.today(),
            notes="used two",
        )
        assert repo.update(iid, updated) is True
        fetched = repo.get_by_id(iid)
        assert fetched is not None
        assert fetched.quantity == 4
        assert fetched.notes == "used two"

    def test_update_quantity_only(
        self, repo: FridgeInventoryRepository, eggs: FridgeItem
    ) -> None:
        iid = repo.create(eggs)
        assert repo.update_quantity(iid, 3.0) is True
        fetched = repo.get_by_id(iid)
        assert fetched is not None
        assert fetched.quantity == 3.0

    def test_update_nonexistent_returns_false(
        self, repo: FridgeInventoryRepository, eggs: FridgeItem
    ) -> None:
        assert repo.update(999, eggs) is False

    def test_update_quantity_nonexistent_returns_false(
        self, repo: FridgeInventoryRepository
    ) -> None:
        assert repo.update_quantity(999, 5.0) is False


class TestFridgeRepositoryDelete:
    def test_delete_removes_item(
        self, repo: FridgeInventoryRepository, eggs: FridgeItem
    ) -> None:
        iid = repo.create(eggs)
        assert repo.delete(iid) is True
        assert repo.get_by_id(iid) is None

    def test_delete_nonexistent_returns_false(
        self, repo: FridgeInventoryRepository
    ) -> None:
        assert repo.delete(999) is False


class TestFridgeItemProperties:
    def test_quantity_display_pieces(self) -> None:
        item = FridgeItem(
            food_name="Eggs", quantity=6, unit="pieces",
            location="fridge", added_date=date.today()
        )
        assert item.quantity_display == "6 pieces"

    def test_quantity_display_singular_piece(self) -> None:
        item = FridgeItem(
            food_name="Avocado", quantity=1, unit="pieces",
            location="fridge", added_date=date.today()
        )
        assert item.quantity_display == "1 piece"

    def test_quantity_display_grams(self) -> None:
        item = FridgeItem(
            food_name="Broccoli", quantity=500, unit="g",
            location="fridge", added_date=date.today()
        )
        assert item.quantity_display == "500 g"

    def test_quantity_display_decimal(self) -> None:
        item = FridgeItem(
            food_name="Oat milk", quantity=1.5, unit="l",
            location="fridge", added_date=date.today()
        )
        assert item.quantity_display == "1.5 l"

    def test_days_until_expiry(self) -> None:
        item = FridgeItem(
            food_name="Milk", quantity=1, unit="l",
            location="fridge", added_date=date.today(),
            expiry_date=date.today() + timedelta(days=5),
        )
        assert item.days_until_expiry == 5

    def test_days_until_expiry_none_when_no_expiry(self) -> None:
        item = FridgeItem(
            food_name="Salt", quantity=500, unit="g",
            location="pantry", added_date=date.today()
        )
        assert item.days_until_expiry is None

    def test_is_expired_true(self) -> None:
        item = FridgeItem(
            food_name="Old milk", quantity=200, unit="ml",
            location="fridge",
            added_date=date.today() - timedelta(days=10),
            expiry_date=date.today() - timedelta(days=1),
        )
        assert item.is_expired is True

    def test_is_expired_false_for_future(self) -> None:
        item = FridgeItem(
            food_name="Fresh milk", quantity=1, unit="l",
            location="fridge", added_date=date.today(),
            expiry_date=date.today() + timedelta(days=7),
        )
        assert item.is_expired is False

    def test_expiry_before_added_raises(self) -> None:
        with pytest.raises(Exception):
            FridgeItem(
                food_name="Bad item", quantity=1, unit="g",
                location="fridge",
                added_date=date.today(),
                expiry_date=date.today() - timedelta(days=1),
            )
