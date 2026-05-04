"""Tests for fridge entry tools and DB query tools — real DB, no LLM."""

from datetime import date, timedelta
from pathlib import Path

import pytest

from nira_backend.data_models.food_inventory import FridgeItem
from nira_backend.database.connection import DatabaseConnection
from nira_backend.database.repositories.fridge_repository import FridgeInventoryRepository
from nira_backend.agents.tools.entry_tools import make_fridge_entry_tools
from nira_backend.agents.tools.database_tools import make_fridge_db_tools, make_dietary_tools


@pytest.fixture
def db(tmp_path: Path) -> DatabaseConnection:
    return DatabaseConnection(db_path=tmp_path / "fridge_tools_test.db")


def _seed_fridge(db: DatabaseConnection) -> None:
    """Add some inventory items for testing."""
    repo = FridgeInventoryRepository(db)
    repo.create(FridgeItem(
        food_name="Eggs", quantity=6, unit="pieces",
        location="fridge", added_date=date.today(),
        expiry_date=date.today() + timedelta(days=10),
    ))
    repo.create(FridgeItem(
        food_name="Broccoli", quantity=300, unit="g",
        location="fridge", added_date=date.today(),
        expiry_date=date.today() + timedelta(days=2),
        notes="fresh",
    ))
    repo.create(FridgeItem(
        food_name="Chicken breast", quantity=1.0, unit="kg",
        location="freezer", added_date=date.today(),
    ))
    repo.create(FridgeItem(
        food_name="Rolled oats", quantity=500, unit="g",
        location="pantry", added_date=date.today(),
    ))


# ---------------------------------------------------------------------------
# Fridge entry tools
# ---------------------------------------------------------------------------


class TestFridgeEntryTools:
    def test_add_to_fridge_creates_item(self, db: DatabaseConnection) -> None:
        tools = make_fridge_entry_tools(db)
        tool = next(t for t in tools if t.name == "add_to_fridge")
        result = tool.invoke({
            "food_name": "Eggs",
            "quantity": 6.0,
            "unit": "pieces",
            "location": "fridge",
        })
        assert "Eggs" in result
        assert "fridge" in result
        assert "ID" in result

        repo = FridgeInventoryRepository(db)
        items = repo.search_by_name("Eggs")
        assert len(items) == 1
        assert items[0].quantity == 6.0

    def test_add_to_fridge_with_expiry(self, db: DatabaseConnection) -> None:
        tools = make_fridge_entry_tools(db)
        tool = next(t for t in tools if t.name == "add_to_fridge")
        expiry = (date.today() + timedelta(days=7)).isoformat()
        result = tool.invoke({
            "food_name": "Milk",
            "quantity": 1.0,
            "unit": "l",
            "expiry_date": expiry,
        })
        assert "expires" in result
        assert "Milk" in result

        repo = FridgeInventoryRepository(db)
        items = repo.search_by_name("Milk")
        assert items[0].expiry_date == date.today() + timedelta(days=7)

    def test_add_to_freezer(self, db: DatabaseConnection) -> None:
        tools = make_fridge_entry_tools(db)
        tool = next(t for t in tools if t.name == "add_to_fridge")
        result = tool.invoke({
            "food_name": "Chicken breast",
            "quantity": 500.0,
            "unit": "g",
            "location": "freezer",
        })
        assert "freezer" in result

    def test_update_fridge_quantity_reduces_stock(self, db: DatabaseConnection) -> None:
        _seed_fridge(db)
        tools = make_fridge_entry_tools(db)
        tool = next(t for t in tools if t.name == "update_fridge_quantity")
        result = tool.invoke({"food_name": "Eggs", "new_quantity": 3.0})
        assert "3.0" in result or "updated" in result.lower()

        repo = FridgeInventoryRepository(db)
        items = repo.search_by_name("Eggs")
        assert items[0].quantity == 3.0

    def test_update_fridge_quantity_removes_at_zero(self, db: DatabaseConnection) -> None:
        _seed_fridge(db)
        tools = make_fridge_entry_tools(db)
        tool = next(t for t in tools if t.name == "update_fridge_quantity")
        result = tool.invoke({"food_name": "Broccoli", "new_quantity": 0.0})
        assert "removed" in result.lower() or "0" in result

        repo = FridgeInventoryRepository(db)
        items = repo.search_by_name("Broccoli")
        assert items == []

    def test_update_fridge_quantity_not_found(self, db: DatabaseConnection) -> None:
        tools = make_fridge_entry_tools(db)
        tool = next(t for t in tools if t.name == "update_fridge_quantity")
        result = tool.invoke({"food_name": "Unicorn meat", "new_quantity": 100.0})
        assert "not found" in result.lower() or "no inventory" in result.lower()

    def test_remove_from_fridge_deletes_item(self, db: DatabaseConnection) -> None:
        _seed_fridge(db)
        tools = make_fridge_entry_tools(db)
        tool = next(t for t in tools if t.name == "remove_from_fridge")
        result = tool.invoke({"food_name": "Rolled oats"})
        assert "removed" in result.lower() or "oats" in result.lower()

        repo = FridgeInventoryRepository(db)
        assert repo.search_by_name("Rolled oats") == []

    def test_remove_from_fridge_not_found(self, db: DatabaseConnection) -> None:
        tools = make_fridge_entry_tools(db)
        tool = next(t for t in tools if t.name == "remove_from_fridge")
        result = tool.invoke({"food_name": "Dragon fruit"})
        assert "not found" in result.lower() or "no inventory" in result.lower()

    def test_all_fridge_entry_tools_returned(self, db: DatabaseConnection) -> None:
        tools = make_fridge_entry_tools(db)
        names = {t.name for t in tools}
        assert "add_to_fridge" in names
        assert "update_fridge_quantity" in names
        assert "remove_from_fridge" in names


# ---------------------------------------------------------------------------
# Fridge DB query tools
# ---------------------------------------------------------------------------


class TestFridgeDbTools:
    def test_list_fridge_contents_empty(self, db: DatabaseConnection) -> None:
        tools = make_fridge_db_tools(db)
        tool = next(t for t in tools if t.name == "list_fridge_contents")
        result = tool.invoke({})
        assert "nothing" in result.lower() or "empty" in result.lower()

    def test_list_fridge_contents_shows_items(self, db: DatabaseConnection) -> None:
        _seed_fridge(db)
        tools = make_fridge_db_tools(db)
        tool = next(t for t in tools if t.name == "list_fridge_contents")
        result = tool.invoke({})
        assert "Eggs" in result
        assert "Broccoli" in result
        assert "Chicken breast" in result
        assert "Rolled oats" in result

    def test_list_fridge_contents_filtered_by_location(
        self, db: DatabaseConnection
    ) -> None:
        _seed_fridge(db)
        tools = make_fridge_db_tools(db)
        tool = next(t for t in tools if t.name == "list_fridge_contents")
        result = tool.invoke({"location": "freezer"})
        assert "Chicken breast" in result
        assert "Rolled oats" not in result

    def test_list_fridge_warns_about_expiring_items(self, db: DatabaseConnection) -> None:
        _seed_fridge(db)
        tools = make_fridge_db_tools(db)
        tool = next(t for t in tools if t.name == "list_fridge_contents")
        result = tool.invoke({})
        assert "Broccoli" in result

    def test_get_expiring_items_finds_soon_expiring(self, db: DatabaseConnection) -> None:
        _seed_fridge(db)
        tools = make_fridge_db_tools(db)
        tool = next(t for t in tools if t.name == "get_expiring_items")
        result = tool.invoke({"days": 3})
        assert "Broccoli" in result

    def test_get_expiring_items_empty_when_none_expiring(
        self, db: DatabaseConnection
    ) -> None:
        tools = make_fridge_db_tools(db)
        tool = next(t for t in tools if t.name == "get_expiring_items")
        result = tool.invoke({"days": 1})
        assert "no items" in result.lower()


# ---------------------------------------------------------------------------
# Dietary context tool
# ---------------------------------------------------------------------------


class TestDietaryTools:
    def test_get_dietary_context_returns_string(self, db: DatabaseConnection) -> None:
        tools = make_dietary_tools(db)
        tool = next(t for t in tools if t.name == "get_dietary_context")
        result = tool.invoke({"human_name": "Alice"})
        assert isinstance(result, str)
        assert "Alice" in result

    def test_get_dietary_context_includes_fridge_section(
        self, db: DatabaseConnection
    ) -> None:
        _seed_fridge(db)
        tools = make_dietary_tools(db)
        tool = next(t for t in tools if t.name == "get_dietary_context")
        result = tool.invoke({"human_name": "Alice", "include_fridge": True})
        assert "FRIDGE" in result or "PANTRY" in result or "INVENTORY" in result
        assert "Eggs" in result

    def test_get_dietary_context_excludes_fridge_when_false(
        self, db: DatabaseConnection
    ) -> None:
        _seed_fridge(db)
        tools = make_dietary_tools(db)
        tool = next(t for t in tools if t.name == "get_dietary_context")
        result = tool.invoke({"human_name": "Alice", "include_fridge": False})
        assert "FRIDGE" not in result

    def test_get_dietary_context_mentions_expiring_items(
        self, db: DatabaseConnection
    ) -> None:
        _seed_fridge(db)
        tools = make_dietary_tools(db)
        tool = next(t for t in tools if t.name == "get_dietary_context")
        result = tool.invoke({"human_name": "Alice", "include_fridge": True})
        assert "Broccoli" in result

    def test_get_dietary_context_no_meals_message(
        self, db: DatabaseConnection
    ) -> None:
        tools = make_dietary_tools(db)
        tool = next(t for t in tools if t.name == "get_dietary_context")
        result = tool.invoke({"human_name": "Bob"})
        assert "none logged" in result.lower() or "no meal" in result.lower() or "None logged" in result
