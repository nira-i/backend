"""Tests for shopping tools — real DB, no LLM."""

from datetime import date, timedelta
from pathlib import Path

import pytest

from nira_backend.data_models.exercise import MealLog
from nira_backend.data_models.food_inventory import FridgeItem
from nira_backend.data_models.health_record import (
    BloodPressureRecord,
    HealthRecord,
)
from nira_backend.database.connection import DatabaseConnection
from nira_backend.database.repositories import (
    FridgeInventoryRepository,
    HealthRecordRepository,
    MealLogRepository,
)
from nira_backend.agents.tools.shopping_tools import (
    make_shopping_tools,
    _classify_food,
    _analyse_meal_variety,
    _SEASONAL,
)


@pytest.fixture
def db(tmp_path: Path) -> DatabaseConnection:
    return DatabaseConnection(db_path=tmp_path / "shopping_test.db")


def _seed_meals(db: DatabaseConnection, human_name: str = "Alice") -> None:
    repo = MealLogRepository(db)
    today = date.today()
    meal_data = [
        ("Oatmeal", 200, "breakfast", 0),
        ("Chicken salad", 350, "lunch", 0),
        ("Salmon with rice", 400, "dinner", 0),
        ("Oatmeal", 200, "breakfast", 1),
        ("Tuna sandwich", 300, "lunch", 1),
        ("Pasta bolognese", 450, "dinner", 1),
        ("Oatmeal", 200, "breakfast", 2),
        ("Eggs on toast", 250, "breakfast", 3),
    ]
    for food_name, qty, meal_type, days_ago in meal_data:
        repo.create(MealLog(
            human_name=human_name,
            food_name=food_name,
            quantity_g=qty,
            meal_type=meal_type,
            log_date=today - timedelta(days=days_ago),
        ))


def _seed_health(db: DatabaseConnection, human_name: str = "Alice") -> None:
    repo = HealthRecordRepository(db)
    bp = BloodPressureRecord(systolic_mmhg=135, diastolic_mmhg=88)
    record = HealthRecord(
        human_name=human_name,
        record_date=date.today(),
        record_type="blood_pressure",
        measurement=bp,
    )
    repo.create(record)


def _seed_fridge(db: DatabaseConnection) -> None:
    repo = FridgeInventoryRepository(db)
    repo.create(FridgeItem(
        food_name="Eggs", quantity=6, unit="pieces",
        location="fridge", added_date=date.today(),
        expiry_date=date.today() + timedelta(days=7),
    ))
    repo.create(FridgeItem(
        food_name="Oat milk", quantity=1, unit="l",
        location="fridge", added_date=date.today(),
        expiry_date=date.today() + timedelta(days=4),
    ))
    repo.create(FridgeItem(
        food_name="Rolled oats", quantity=400, unit="g",
        location="pantry", added_date=date.today(),
    ))


# ---------------------------------------------------------------------------
# Food classification helpers
# ---------------------------------------------------------------------------


class TestClassifyFood:
    def test_chicken_is_protein(self) -> None:
        assert "proteins" in _classify_food("Chicken breast")

    def test_broccoli_is_vegetable(self) -> None:
        assert "vegetables" in _classify_food("Broccoli florets")

    def test_banana_is_fruit(self) -> None:
        assert "fruits" in _classify_food("Banana")

    def test_milk_is_dairy(self) -> None:
        assert "dairy" in _classify_food("Whole milk")

    def test_oatmeal_is_carb(self) -> None:
        assert "carbs" in _classify_food("Oatmeal")

    def test_unknown_food_returns_other(self) -> None:
        assert _classify_food("Truffle oil dressing") == ["other"]

    def test_eggs_are_protein(self) -> None:
        assert "proteins" in _classify_food("Scrambled eggs")


class TestAnalyseMealVariety:
    def test_empty_meals_returns_message(self) -> None:
        result = _analyse_meal_variety([])
        assert "no meal data" in result.lower()

    def test_detects_missing_fruit_group(self, db: DatabaseConnection) -> None:
        _seed_meals(db)
        repo = MealLogRepository(db)
        meals = repo.get_by_human("Alice", days=7)
        result = _analyse_meal_variety(meals)
        assert "fruits" in result.lower()
        assert "NONE" in result

    def test_counts_unique_foods(self, db: DatabaseConnection) -> None:
        _seed_meals(db)
        repo = MealLogRepository(db)
        meals = repo.get_by_human("Alice", days=7)
        result = _analyse_meal_variety(meals)
        assert "Unique foods" in result

    def test_detects_repeated_food(self, db: DatabaseConnection) -> None:
        _seed_meals(db)
        repo = MealLogRepository(db)
        meals = repo.get_by_human("Alice", days=7)
        result = _analyse_meal_variety(meals)
        assert "Oatmeal" in result or "monotony" in result.lower()


# ---------------------------------------------------------------------------
# Seasonal data integrity
# ---------------------------------------------------------------------------


class TestSeasonalData:
    def test_all_twelve_months_present(self) -> None:
        assert set(_SEASONAL.keys()) == set(range(1, 13))

    def test_each_month_has_required_keys(self) -> None:
        for month, info in _SEASONAL.items():
            assert "season" in info, f"Month {month} missing 'season'"
            assert "vegetables" in info, f"Month {month} missing 'vegetables'"
            assert "fruits" in info, f"Month {month} missing 'fruits'"
            assert "note" in info, f"Month {month} missing 'note'"
            assert isinstance(info["vegetables"], list)
            assert isinstance(info["fruits"], list)
            assert len(info["vegetables"]) >= 3
            assert len(info["fruits"]) >= 2


# ---------------------------------------------------------------------------
# Shopping tools (real DB, no LLM)
# ---------------------------------------------------------------------------


class TestGetSeasonalFoodsTool:
    def test_returns_string(self, db: DatabaseConnection) -> None:
        tools = make_shopping_tools(db)
        tool = next(t for t in tools if t.name == "get_seasonal_foods")
        result = tool.invoke({})
        assert isinstance(result, str)
        assert len(result) > 50

    def test_contains_current_month_name(self, db: DatabaseConnection) -> None:
        tools = make_shopping_tools(db)
        tool = next(t for t in tools if t.name == "get_seasonal_foods")
        result = tool.invoke({})
        current_month = date.today().strftime("%B")
        assert current_month in result

    def test_contains_vegetables_and_fruits_sections(self, db: DatabaseConnection) -> None:
        tools = make_shopping_tools(db)
        tool = next(t for t in tools if t.name == "get_seasonal_foods")
        result = tool.invoke({})
        assert "VEGETABLE" in result.upper()
        assert "FRUIT" in result.upper()

    def test_contains_seasonal_note(self, db: DatabaseConnection) -> None:
        tools = make_shopping_tools(db)
        tool = next(t for t in tools if t.name == "get_seasonal_foods")
        result = tool.invoke({})
        assert "NOTE" in result.upper() or "note" in result.lower()


class TestGetShoppingContextTool:
    def test_returns_string(self, db: DatabaseConnection) -> None:
        tools = make_shopping_tools(db)
        tool = next(t for t in tools if t.name == "get_shopping_context")
        result = tool.invoke({"human_names": "Alice"})
        assert isinstance(result, str)

    def test_includes_human_name(self, db: DatabaseConnection) -> None:
        tools = make_shopping_tools(db)
        tool = next(t for t in tools if t.name == "get_shopping_context")
        result = tool.invoke({"human_names": "Alice"})
        assert "ALICE" in result

    def test_includes_season(self, db: DatabaseConnection) -> None:
        tools = make_shopping_tools(db)
        tool = next(t for t in tools if t.name == "get_shopping_context")
        result = tool.invoke({"human_names": "Alice"})
        assert "SEASON" in result

    def test_includes_seasonal_produce(self, db: DatabaseConnection) -> None:
        tools = make_shopping_tools(db)
        tool = next(t for t in tools if t.name == "get_shopping_context")
        result = tool.invoke({"human_names": "Alice"})
        assert "SEASONAL" in result

    def test_includes_meal_patterns(self, db: DatabaseConnection) -> None:
        _seed_meals(db)
        tools = make_shopping_tools(db)
        tool = next(t for t in tools if t.name == "get_shopping_context")
        result = tool.invoke({"human_names": "Alice"})
        assert "MEAL PATTERN" in result.upper()
        assert "Oatmeal" in result

    def test_includes_nutritional_gap_analysis(self, db: DatabaseConnection) -> None:
        _seed_meals(db)
        tools = make_shopping_tools(db)
        tool = next(t for t in tools if t.name == "get_shopping_context")
        result = tool.invoke({"human_names": "Alice"})
        assert "GAP" in result.upper() or "NUTRITIONAL" in result.upper()

    def test_includes_health_conditions(self, db: DatabaseConnection) -> None:
        _seed_health(db)
        tools = make_shopping_tools(db)
        tool = next(t for t in tools if t.name == "get_shopping_context")
        result = tool.invoke({"human_names": "Alice"})
        assert "HEALTH" in result.upper()
        assert "blood_pressure" in result

    def test_includes_inventory_when_requested(self, db: DatabaseConnection) -> None:
        _seed_fridge(db)
        tools = make_shopping_tools(db)
        tool = next(t for t in tools if t.name == "get_shopping_context")
        result = tool.invoke({"human_names": "Alice", "include_fridge": True})
        assert "INVENTORY" in result.upper() or "FRIDGE" in result.upper()
        assert "Eggs" in result

    def test_excludes_inventory_when_not_requested(self, db: DatabaseConnection) -> None:
        _seed_fridge(db)
        tools = make_shopping_tools(db)
        tool = next(t for t in tools if t.name == "get_shopping_context")
        result = tool.invoke({"human_names": "Alice", "include_fridge": False})
        assert "INVENTORY" not in result.upper()

    def test_no_meals_shows_message(self, db: DatabaseConnection) -> None:
        tools = make_shopping_tools(db)
        tool = next(t for t in tools if t.name == "get_shopping_context")
        result = tool.invoke({"human_names": "Bob"})
        assert "no meal" in result.lower() or "none" in result.lower() or "not" in result.lower()

    def test_multiple_people(self, db: DatabaseConnection) -> None:
        _seed_meals(db, "Alice")
        _seed_meals(db, "John")
        tools = make_shopping_tools(db)
        tool = next(t for t in tools if t.name == "get_shopping_context")
        result = tool.invoke({"human_names": "Alice, John"})
        assert "ALICE" in result
        assert "JOHN" in result

    def test_expiring_items_flagged(self, db: DatabaseConnection) -> None:
        _seed_fridge(db)
        tools = make_shopping_tools(db)
        tool = next(t for t in tools if t.name == "get_shopping_context")
        result = tool.invoke({"human_names": "Alice", "include_fridge": True})
        assert "expir" in result.lower() or "Oat milk" in result

    def test_all_tools_returned(self, db: DatabaseConnection) -> None:
        tools = make_shopping_tools(db)
        names = {t.name for t in tools}
        assert "get_seasonal_foods" in names
        assert "get_shopping_context" in names
