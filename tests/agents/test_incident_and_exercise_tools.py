"""Tests for incident entry/query tools and exercise analysis tool — no LLM."""

from datetime import date, timedelta
from pathlib import Path

import pytest

from nira_backend.data_models.exercise import ExerciseEntry
from nira_backend.data_models.health_incident import HealthIncident
from nira_backend.database.connection import DatabaseConnection
from nira_backend.database.repositories import (
    ExerciseRepository,
    HealthIncidentRepository,
)
from nira_backend.agents.tools.entry_tools import make_incident_entry_tools
from nira_backend.agents.tools.database_tools import (
    make_incident_db_tools,
    make_exercise_analysis_tools,
    _classify_exercise,
)


@pytest.fixture
def db(tmp_path: Path) -> DatabaseConnection:
    return DatabaseConnection(db_path=tmp_path / "incident_exercise_test.db")


def _seed_incidents(db: DatabaseConnection) -> None:
    repo = HealthIncidentRepository(db)
    repo.create(HealthIncident(
        human_name="Alice",
        incident_date=date.today(),
        description="Fever and sore throat",
        symptoms=["fever", "sore throat"],
        severity="moderate",
        incident_type="illness",
    ))
    repo.create(HealthIncident(
        human_name="Alice",
        incident_date=date.today() - timedelta(days=5),
        description="Shoulder pain from desk work",
        symptoms=["shoulder pain"],
        severity="mild",
        body_part="shoulder",
        incident_type="pain",
    ))
    repo.create(HealthIncident(
        human_name="John",
        incident_date=date.today(),
        description="Feeling stressed from work",
        incident_type="stress",
    ))


def _seed_exercise(db: DatabaseConnection, human_name: str = "Alice") -> None:
    repo = ExerciseRepository(db)
    today = date.today()
    sessions = [
        ("Running", 30, "vigorous", 0, 5.0),
        ("Yoga", 45, "light", 2, None),
        ("Running", 25, "moderate", 3, 4.0),
        ("Weight training", 40, "moderate", 5, None),
        ("Cycling", 60, "vigorous", 7, 20.0),
        ("Running", 35, "vigorous", 10, 5.5),
        ("Yoga", 30, "light", 12, None),
        ("Swimming", 45, "moderate", 14, None),
    ]
    for activity, duration, intensity, days_ago, distance in sessions:
        entry = ExerciseEntry(
            human_name=human_name,
            exercise_date=today - timedelta(days=days_ago),
            activity=activity,
            duration_minutes=duration,
            intensity=intensity,
            distance_km=distance,
        )
        repo.create(entry)


# ---------------------------------------------------------------------------
# Exercise category classification
# ---------------------------------------------------------------------------


class TestClassifyExercise:
    def test_running_is_cardio(self) -> None:
        assert _classify_exercise("Running") == "cardio"

    def test_yoga_is_flexibility(self) -> None:
        assert _classify_exercise("Yoga flow") == "flexibility"

    def test_weight_training_is_strength(self) -> None:
        assert _classify_exercise("Weight training") == "strength"

    def test_football_is_sports(self) -> None:
        assert _classify_exercise("Football") == "sports"

    def test_unknown_returns_other(self) -> None:
        assert _classify_exercise("Napping on a hammock") == "other"

    def test_case_insensitive(self) -> None:
        assert _classify_exercise("RUNNING") == "cardio"
        assert _classify_exercise("Pilates") == "flexibility"


# ---------------------------------------------------------------------------
# Incident entry tools
# ---------------------------------------------------------------------------


class TestIncidentEntryTools:
    def test_log_health_incident_creates_record(self, db: DatabaseConnection) -> None:
        tools = make_incident_entry_tools(db)
        tool = next(t for t in tools if t.name == "log_health_incident")
        result = tool.invoke({
            "human_name": "Alice",
            "description": "Fever and sore throat",
            "incident_type": "illness",
            "severity": "moderate",
            "symptoms": "fever, sore throat",
        })
        assert "Alice" in result
        assert "illness" in result
        assert "ID" in result

        repo = HealthIncidentRepository(db)
        incidents = repo.get_by_human("Alice", days=1)
        assert len(incidents) == 1
        assert incidents[0].severity == "moderate"

    def test_log_incident_with_body_part(self, db: DatabaseConnection) -> None:
        tools = make_incident_entry_tools(db)
        tool = next(t for t in tools if t.name == "log_health_incident")
        result = tool.invoke({
            "human_name": "John",
            "description": "Shoulder pain",
            "incident_type": "pain",
            "body_part": "shoulder",
        })
        assert "shoulder" in result.lower()

        repo = HealthIncidentRepository(db)
        incidents = repo.get_by_human("John", days=1)
        assert incidents[0].body_part == "shoulder"

    def test_log_incident_minimal_fields(self, db: DatabaseConnection) -> None:
        tools = make_incident_entry_tools(db)
        tool = next(t for t in tools if t.name == "log_health_incident")
        result = tool.invoke({
            "human_name": "Alice",
            "description": "Feeling unwell today",
        })
        assert "Alice" in result
        assert "ID" in result

    def test_log_incident_symptoms_parsed_from_csv(self, db: DatabaseConnection) -> None:
        tools = make_incident_entry_tools(db)
        tool = next(t for t in tools if t.name == "log_health_incident")
        tool.invoke({
            "human_name": "Alice",
            "description": "Cold symptoms",
            "symptoms": "runny nose, sneezing, sore throat",
        })
        repo = HealthIncidentRepository(db)
        incidents = repo.get_by_human("Alice", days=1)
        assert "runny nose" in incidents[0].symptoms
        assert "sneezing" in incidents[0].symptoms

    def test_tool_list_contains_expected_tool(self, db: DatabaseConnection) -> None:
        tools = make_incident_entry_tools(db)
        names = {t.name for t in tools}
        assert "log_health_incident" in names


# ---------------------------------------------------------------------------
# Incident DB query tools
# ---------------------------------------------------------------------------


class TestIncidentDbTools:
    def test_get_incident_history_empty(self, db: DatabaseConnection) -> None:
        tools = make_incident_db_tools(db)
        tool = next(t for t in tools if t.name == "get_incident_history")
        result = tool.invoke({"human_name": "Alice"})
        assert "no" in result.lower() or "not found" in result.lower()

    def test_get_incident_history_returns_incidents(self, db: DatabaseConnection) -> None:
        _seed_incidents(db)
        tools = make_incident_db_tools(db)
        tool = next(t for t in tools if t.name == "get_incident_history")
        result = tool.invoke({"human_name": "Alice"})
        assert "ILLNESS" in result or "illness" in result.lower()
        assert "PAIN" in result or "pain" in result.lower()

    def test_get_incident_history_shows_symptoms(self, db: DatabaseConnection) -> None:
        _seed_incidents(db)
        tools = make_incident_db_tools(db)
        tool = next(t for t in tools if t.name == "get_incident_history")
        result = tool.invoke({"human_name": "Alice"})
        assert "fever" in result

    def test_get_incident_history_filters_by_person(self, db: DatabaseConnection) -> None:
        _seed_incidents(db)
        tools = make_incident_db_tools(db)
        tool = next(t for t in tools if t.name == "get_incident_history")
        result = tool.invoke({"human_name": "John"})
        assert "stress" in result.lower()
        assert "ILLNESS" not in result

    def test_get_incident_history_respects_days(self, db: DatabaseConnection) -> None:
        _seed_incidents(db)
        tools = make_incident_db_tools(db)
        tool = next(t for t in tools if t.name == "get_incident_history")
        result = tool.invoke({"human_name": "Alice", "days": 3})
        assert "ILLNESS" in result or "illness" in result.lower()
        assert "Shoulder pain" not in result

    def test_tool_list_contains_expected_tool(self, db: DatabaseConnection) -> None:
        tools = make_incident_db_tools(db)
        names = {t.name for t in tools}
        assert "get_incident_history" in names


# ---------------------------------------------------------------------------
# Exercise analysis tools
# ---------------------------------------------------------------------------


class TestExerciseAnalysisTools:
    def test_returns_string(self, db: DatabaseConnection) -> None:
        tools = make_exercise_analysis_tools(db)
        tool = next(t for t in tools if t.name == "get_exercise_analysis_context")
        result = tool.invoke({"human_name": "Alice"})
        assert isinstance(result, str)

    def test_no_data_returns_helpful_message(self, db: DatabaseConnection) -> None:
        tools = make_exercise_analysis_tools(db)
        tool = next(t for t in tools if t.name == "get_exercise_analysis_context")
        result = tool.invoke({"human_name": "Alice"})
        assert "no exercise" in result.lower() or "no" in result.lower()

    def test_includes_human_name(self, db: DatabaseConnection) -> None:
        _seed_exercise(db)
        tools = make_exercise_analysis_tools(db)
        tool = next(t for t in tools if t.name == "get_exercise_analysis_context")
        result = tool.invoke({"human_name": "Alice"})
        assert "Alice" in result

    def test_includes_volume_stats(self, db: DatabaseConnection) -> None:
        _seed_exercise(db)
        tools = make_exercise_analysis_tools(db)
        tool = next(t for t in tools if t.name == "get_exercise_analysis_context")
        result = tool.invoke({"human_name": "Alice"})
        assert "Sessions" in result or "session" in result.lower()

    def test_includes_activity_type_breakdown(self, db: DatabaseConnection) -> None:
        _seed_exercise(db)
        tools = make_exercise_analysis_tools(db)
        tool = next(t for t in tools if t.name == "get_exercise_analysis_context")
        result = tool.invoke({"human_name": "Alice"})
        assert "Cardio" in result or "cardio" in result.lower()
        assert "Flexibility" in result or "flexibility" in result.lower()

    def test_flags_missing_exercise_type(self, db: DatabaseConnection) -> None:
        repo = ExerciseRepository(db)
        repo.create(ExerciseEntry(
            human_name="Alice",
            exercise_date=date.today(),
            activity="Running",
            duration_minutes=30,
            intensity="vigorous",
        ))
        tools = make_exercise_analysis_tools(db)
        tool = next(t for t in tools if t.name == "get_exercise_analysis_context")
        result = tool.invoke({"human_name": "Alice"})
        assert "Missing" in result or "missing" in result.lower() or "⚠️" in result

    def test_includes_intensity_distribution(self, db: DatabaseConnection) -> None:
        _seed_exercise(db)
        tools = make_exercise_analysis_tools(db)
        tool = next(t for t in tools if t.name == "get_exercise_analysis_context")
        result = tool.invoke({"human_name": "Alice"})
        assert "INTENSITY" in result or "intensity" in result.lower()

    def test_includes_rest_and_recovery(self, db: DatabaseConnection) -> None:
        _seed_exercise(db)
        tools = make_exercise_analysis_tools(db)
        tool = next(t for t in tools if t.name == "get_exercise_analysis_context")
        result = tool.invoke({"human_name": "Alice"})
        assert "REST" in result or "rest" in result.lower() or "Rest" in result

    def test_tool_list_contains_expected_tool(self, db: DatabaseConnection) -> None:
        tools = make_exercise_analysis_tools(db)
        names = {t.name for t in tools}
        assert "get_exercise_analysis_context" in names
