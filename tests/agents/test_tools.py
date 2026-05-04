"""Tests for tool factory functions — uses a real in-memory DB, no LLM."""

from datetime import date
from pathlib import Path

import pytest

from nira_backend.database.connection import DatabaseConnection
from nira_backend.database.repositories import (
    ExerciseRepository,
    HealthRecordRepository,
    MealLogRepository,
)
from nira_backend.agents.tools.database_tools import make_shared_db_tools
from nira_backend.agents.tools.entry_tools import (
    make_exercise_entry_tools,
    make_health_entry_tools,
    make_meal_entry_tools,
)


@pytest.fixture
def db(tmp_path: Path) -> DatabaseConnection:
    return DatabaseConnection(db_path=tmp_path / "test_tools.db")


# ---------------------------------------------------------------------------
# Shared DB tools
# ---------------------------------------------------------------------------


class TestSharedDbTools:
    def test_list_family_members_empty(self, db: DatabaseConnection) -> None:
        tools = make_shared_db_tools(db)
        tool = next(t for t in tools if t.name == "list_family_members")
        result = tool.invoke({})
        assert "No family members" in result

    def test_get_health_history_empty(self, db: DatabaseConnection) -> None:
        tools = make_shared_db_tools(db)
        tool = next(t for t in tools if t.name == "get_health_history")
        result = tool.invoke({"human_name": "Alice"})
        assert "No" in result

    def test_get_meal_history_empty(self, db: DatabaseConnection) -> None:
        tools = make_shared_db_tools(db)
        tool = next(t for t in tools if t.name == "get_meal_history")
        result = tool.invoke({"human_name": "Bob"})
        assert "No" in result

    def test_get_exercise_history_empty(self, db: DatabaseConnection) -> None:
        tools = make_shared_db_tools(db)
        tool = next(t for t in tools if t.name == "get_exercise_history")
        result = tool.invoke({"human_name": "Charlie"})
        assert "No" in result


# ---------------------------------------------------------------------------
# Health entry tools
# ---------------------------------------------------------------------------


class TestHealthEntryTools:
    def test_log_blood_pressure_creates_record(self, db: DatabaseConnection) -> None:
        tools = make_health_entry_tools(db)
        tool = next(t for t in tools if t.name == "log_blood_pressure")
        result = tool.invoke(
            {
                "human_name": "Alice",
                "systolic_mmhg": 120,
                "diastolic_mmhg": 80,
            }
        )
        assert "Alice" in result
        assert "120/80" in result
        assert "ID" in result

        repo = HealthRecordRepository(db)
        records = repo.get_by_human_name("Alice")
        assert len(records) == 1
        assert records[0].record_type == "blood_pressure"

    def test_log_blood_pressure_with_pulse_and_notes(
        self, db: DatabaseConnection
    ) -> None:
        tools = make_health_entry_tools(db)
        tool = next(t for t in tools if t.name == "log_blood_pressure")
        result = tool.invoke(
            {
                "human_name": "Bob",
                "systolic_mmhg": 130,
                "diastolic_mmhg": 85,
                "pulse_bpm": 72,
                "notes": "after exercise",
            }
        )
        assert "Bob" in result

    def test_log_blood_glucose_creates_record(self, db: DatabaseConnection) -> None:
        tools = make_health_entry_tools(db)
        tool = next(t for t in tools if t.name == "log_blood_glucose")
        result = tool.invoke(
            {
                "human_name": "Carol",
                "glucose_mmol_l": 5.2,
                "measurement_context": "fasting",
            }
        )
        assert "Carol" in result
        assert "5.2" in result

        repo = HealthRecordRepository(db)
        records = repo.get_by_human_name("Carol")
        assert len(records) == 1
        assert records[0].record_type == "blood_glucose"

    def test_log_heart_rate_creates_record(self, db: DatabaseConnection) -> None:
        tools = make_health_entry_tools(db)
        tool = next(t for t in tools if t.name == "log_heart_rate")
        result = tool.invoke({"human_name": "Dave", "bpm": 68})
        assert "Dave" in result
        assert "68" in result

    def test_log_sleep_creates_record(self, db: DatabaseConnection) -> None:
        tools = make_health_entry_tools(db)
        tool = next(t for t in tools if t.name == "log_sleep")
        result = tool.invoke(
            {"human_name": "Eve", "duration_hours": 7.5, "quality": 4}
        )
        assert "Eve" in result
        assert "7.5" in result

    def test_all_health_tools_are_returned(self, db: DatabaseConnection) -> None:
        tools = make_health_entry_tools(db)
        names = {t.name for t in tools}
        assert "log_blood_pressure" in names
        assert "log_blood_glucose" in names
        assert "log_heart_rate" in names
        assert "log_sleep" in names


# ---------------------------------------------------------------------------
# Meal entry tools
# ---------------------------------------------------------------------------


class TestMealEntryTools:
    def test_log_meal_creates_record(self, db: DatabaseConnection) -> None:
        tools = make_meal_entry_tools(db)
        tool = next(t for t in tools if t.name == "log_meal")
        result = tool.invoke(
            {
                "human_name": "Alice",
                "food_name": "Oatmeal",
                "quantity_g": 250.0,
                "meal_type": "breakfast",
            }
        )
        assert "Alice" in result
        assert "Oatmeal" in result
        assert "250" in result

        repo = MealLogRepository(db)
        logs = repo.get_by_human("Alice")
        assert len(logs) == 1
        assert logs[0].food_name == "Oatmeal"

    def test_add_food_item_creates_catalog_entry(self, db: DatabaseConnection) -> None:
        tools = make_meal_entry_tools(db)
        tool = next(t for t in tools if t.name == "add_food_item")
        result = tool.invoke(
            {
                "name": "Banana",
                "category": "fruit",
                "calories": 89.0,
                "protein_g": 1.1,
                "carbohydrates_g": 23.0,
                "fat_g": 0.3,
            }
        )
        assert "Banana" in result
        assert "ID" in result

    def test_search_food_catalog_returns_results(self, db: DatabaseConnection) -> None:
        tools = make_meal_entry_tools(db)
        add_tool = next(t for t in tools if t.name == "add_food_item")
        add_tool.invoke(
            {
                "name": "Apple",
                "category": "fruit",
                "calories": 52.0,
                "protein_g": 0.3,
                "carbohydrates_g": 14.0,
                "fat_g": 0.2,
            }
        )

        search_tool = next(t for t in tools if t.name == "search_food_catalog")
        result = search_tool.invoke({"query": "Apple"})
        assert "Apple" in result

    def test_search_food_catalog_empty(self, db: DatabaseConnection) -> None:
        tools = make_meal_entry_tools(db)
        search_tool = next(t for t in tools if t.name == "search_food_catalog")
        result = search_tool.invoke({"query": "NothingLikeThis"})
        assert "No food items" in result

    def test_log_meal_multiple_entries(self, db: DatabaseConnection) -> None:
        tools = make_meal_entry_tools(db)
        tool = next(t for t in tools if t.name == "log_meal")
        tool.invoke({"human_name": "Bob", "food_name": "Rice", "quantity_g": 200.0})
        tool.invoke({"human_name": "Bob", "food_name": "Chicken", "quantity_g": 150.0})

        repo = MealLogRepository(db)
        logs = repo.get_by_human("Bob")
        assert len(logs) == 2


# ---------------------------------------------------------------------------
# Exercise entry tools
# ---------------------------------------------------------------------------


class TestExerciseEntryTools:
    def test_log_exercise_creates_record(self, db: DatabaseConnection) -> None:
        tools = make_exercise_entry_tools(db)
        tool = next(t for t in tools if t.name == "log_exercise")
        result = tool.invoke(
            {
                "human_name": "Alice",
                "activity": "running",
                "duration_minutes": 30,
                "intensity": "moderate",
            }
        )
        assert "Alice" in result
        assert "running" in result
        assert "30" in result

        repo = ExerciseRepository(db)
        entries = repo.get_by_human("Alice")
        assert len(entries) == 1
        assert entries[0].activity == "running"

    def test_log_exercise_with_optional_fields(self, db: DatabaseConnection) -> None:
        tools = make_exercise_entry_tools(db)
        tool = next(t for t in tools if t.name == "log_exercise")
        result = tool.invoke(
            {
                "human_name": "Bob",
                "activity": "cycling",
                "duration_minutes": 45,
                "intensity": "vigorous",
                "calories_burned": 400.0,
                "distance_km": 15.0,
            }
        )
        assert "Bob" in result
        assert "15.0 km" in result
        assert "400.0 kcal" in result

    def test_log_exercise_default_intensity(self, db: DatabaseConnection) -> None:
        tools = make_exercise_entry_tools(db)
        tool = next(t for t in tools if t.name == "log_exercise")
        tool.invoke(
            {
                "human_name": "Carol",
                "activity": "yoga",
                "duration_minutes": 60,
            }
        )
        repo = ExerciseRepository(db)
        entries = repo.get_by_human("Carol")
        assert entries[0].intensity == "moderate"
