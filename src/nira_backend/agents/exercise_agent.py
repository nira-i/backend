"""ExerciseAgent — handles exercise logging and history."""

from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI

from nira_backend.agents.base_agent import BaseAgent
from nira_backend.agents.tools.database_tools import make_shared_db_tools
from nira_backend.agents.tools.entry_tools import make_exercise_entry_tools
from nira_backend.agents.tools.parsing_tools import make_exercise_parsing_tools
from nira_backend.database.connection import DatabaseConnection
from nira_backend.llm.config import get_api_key

_SYSTEM_PROMPT = """\
You are NIRA's exercise specialist.  You help the family log and review
physical activity sessions and offer motivational guidance.

Your responsibilities:
- Log exercise sessions that family members report (structured or free text).
- Retrieve and summarise exercise history for any family member.
- Celebrate consistency and progress — motivation matters.
- Offer general exercise tips, but defer to professionals for medical advice.

Guidelines:
- When logging from free text, use the parse_and_log_exercise tool.
- When the user gives explicit details, use the log_exercise tool.
- Always confirm what was logged (activity, duration, intensity).
- Intensity guide: light = walking/stretching, moderate = brisk walk/light jog,
  vigorous = running/HIIT/cycling hard.
- Be encouraging — every session counts, no matter how short.
"""


class ExerciseAgent(BaseAgent):
    """
    Agent specialising in exercise tracking and motivation.

    Args:
        db: Active database connection.
        api_key: Gemini API key.  Reads from secrets file if not provided.
        data_dir: Override data directory for memory (tests).
        llm_model: Gemini model name.
        temperature: LLM temperature.
    """

    def __init__(
        self,
        db: DatabaseConnection,
        api_key: str | None = None,
        data_dir: Any = None,
        llm_model: str = "gemini-2.0-flash",
        temperature: float = 0.3,
    ) -> None:
        llm = ChatGoogleGenerativeAI(
            model=llm_model,
            google_api_key=api_key or get_api_key("gemini"),
            temperature=temperature,
        )
        tools = (
            make_shared_db_tools(db)
            + make_exercise_entry_tools(db)
            + make_exercise_parsing_tools(db, llm)
        )
        super().__init__(
            name="exercise",
            system_prompt=_SYSTEM_PROMPT,
            tools=tools,
            llm=llm,
            data_dir=data_dir,
        )
