"""Smoke tests for agent classes — LLM is mocked, DB is real (tmp_path)."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage

from nira_backend.database.connection import DatabaseConnection


@pytest.fixture
def db(tmp_path: Path) -> DatabaseConnection:
    return DatabaseConnection(db_path=tmp_path / "agent_test.db")


def _make_mock_llm(response_text: str = "Done!") -> MagicMock:
    """Return a mock LLM that always responds with plain text (no tool calls)."""
    mock_llm = MagicMock()
    response = AIMessage(content=response_text)
    bound = MagicMock()
    bound.invoke.return_value = response
    mock_llm.bind_tools.return_value = bound
    mock_llm.invoke.return_value = response
    return mock_llm


# ---------------------------------------------------------------------------
# NutritionAgent
# ---------------------------------------------------------------------------


class TestNutritionAgent:
    @patch("nira_backend.agents.nutrition_agent.ChatGoogleGenerativeAI")
    def test_run_returns_string(
        self, mock_cls: MagicMock, db: DatabaseConnection, tmp_path: Path
    ) -> None:
        from nira_backend.agents.nutrition_agent import NutritionAgent

        mock_cls.return_value = _make_mock_llm("Meal logged!")
        agent = NutritionAgent(db=db, api_key="fake_key", data_dir=tmp_path)
        result = agent.run("Log oatmeal for breakfast")
        assert isinstance(result, str)
        assert result == "Meal logged!"

    @patch("nira_backend.agents.nutrition_agent.ChatGoogleGenerativeAI")
    def test_memory_is_saved_after_run(
        self, mock_cls: MagicMock, db: DatabaseConnection, tmp_path: Path
    ) -> None:
        from nira_backend.agents.nutrition_agent import NutritionAgent

        mock_cls.return_value = _make_mock_llm("Got it!")
        agent = NutritionAgent(db=db, api_key="fake_key", data_dir=tmp_path)
        agent.run("Hello")
        assert agent.memory_exchange_count == 1

    @patch("nira_backend.agents.nutrition_agent.ChatGoogleGenerativeAI")
    def test_clear_memory_resets_count(
        self, mock_cls: MagicMock, db: DatabaseConnection, tmp_path: Path
    ) -> None:
        from nira_backend.agents.nutrition_agent import NutritionAgent

        mock_cls.return_value = _make_mock_llm("OK")
        agent = NutritionAgent(db=db, api_key="fake_key", data_dir=tmp_path)
        agent.run("Test")
        agent.clear_memory()
        assert agent.memory_exchange_count == 0


# ---------------------------------------------------------------------------
# HealthAgent
# ---------------------------------------------------------------------------


class TestHealthAgent:
    @patch("nira_backend.agents.health_agent.ChatGoogleGenerativeAI")
    def test_run_returns_string(
        self, mock_cls: MagicMock, db: DatabaseConnection, tmp_path: Path
    ) -> None:
        from nira_backend.agents.health_agent import HealthAgent

        mock_cls.return_value = _make_mock_llm("Blood pressure logged.")
        agent = HealthAgent(db=db, api_key="fake_key", data_dir=tmp_path)
        result = agent.run("Log blood pressure 120/80")
        assert isinstance(result, str)
        assert result == "Blood pressure logged."

    @patch("nira_backend.agents.health_agent.ChatGoogleGenerativeAI")
    def test_memory_accumulates(
        self, mock_cls: MagicMock, db: DatabaseConnection, tmp_path: Path
    ) -> None:
        from nira_backend.agents.health_agent import HealthAgent

        mock_cls.return_value = _make_mock_llm("OK")
        agent = HealthAgent(db=db, api_key="fake_key", data_dir=tmp_path)
        agent.run("msg 1")
        agent.run("msg 2")
        assert agent.memory_exchange_count == 2


# ---------------------------------------------------------------------------
# ExerciseAgent
# ---------------------------------------------------------------------------


class TestExerciseAgent:
    @patch("nira_backend.agents.exercise_agent.ChatGoogleGenerativeAI")
    def test_run_returns_string(
        self, mock_cls: MagicMock, db: DatabaseConnection, tmp_path: Path
    ) -> None:
        from nira_backend.agents.exercise_agent import ExerciseAgent

        mock_cls.return_value = _make_mock_llm("Exercise logged!")
        agent = ExerciseAgent(db=db, api_key="fake_key", data_dir=tmp_path)
        result = agent.run("I went for a 5km run")
        assert isinstance(result, str)
        assert result == "Exercise logged!"


# ---------------------------------------------------------------------------
# BaseAgent tool-calling loop
# ---------------------------------------------------------------------------


class TestBaseAgentLoop:
    @patch("nira_backend.agents.nutrition_agent.ChatGoogleGenerativeAI")
    def test_agent_executes_tool_call_and_continues(
        self, mock_cls: MagicMock, db: DatabaseConnection, tmp_path: Path
    ) -> None:
        """Verify the loop handles one tool call then a final text response."""
        from langchain_core.messages import AIMessage
        from nira_backend.agents.nutrition_agent import NutritionAgent

        mock_llm = MagicMock()
        mock_cls.return_value = mock_llm

        tool_call_response = AIMessage(content="")
        tool_call_response.tool_calls = [
            {
                "id": "call_1",
                "name": "search_food_catalog",
                "args": {"query": "banana"},
            }
        ]
        final_response = AIMessage(content="Here is what I found.")
        final_response.tool_calls = []

        bound = MagicMock()
        bound.invoke.side_effect = [tool_call_response, final_response]
        mock_llm.bind_tools.return_value = bound

        agent = NutritionAgent(db=db, api_key="fake_key", data_dir=tmp_path)
        result = agent.run("Find bananas")
        assert result == "Here is what I found."

    @patch("nira_backend.agents.nutrition_agent.ChatGoogleGenerativeAI")
    def test_unknown_tool_name_returns_error_string(
        self, mock_cls: MagicMock, db: DatabaseConnection, tmp_path: Path
    ) -> None:
        from langchain_core.messages import AIMessage
        from nira_backend.agents.nutrition_agent import NutritionAgent

        mock_llm = MagicMock()
        mock_cls.return_value = mock_llm

        bad_tool_response = AIMessage(content="")
        bad_tool_response.tool_calls = [
            {"id": "call_x", "name": "nonexistent_tool", "args": {}}
        ]
        final = AIMessage(content="Handled gracefully.")
        final.tool_calls = []

        bound = MagicMock()
        bound.invoke.side_effect = [bad_tool_response, final]
        mock_llm.bind_tools.return_value = bound

        agent = NutritionAgent(db=db, api_key="fake_key", data_dir=tmp_path)
        result = agent.run("Do something weird")
        assert result == "Handled gracefully."
