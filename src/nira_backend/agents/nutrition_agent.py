"""NutritionAgent — handles all food and meal-related queries."""

from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI

from nira_backend.agents.base_agent import BaseAgent
from nira_backend.agents.tools.database_tools import make_shared_db_tools
from nira_backend.agents.tools.entry_tools import make_meal_entry_tools
from nira_backend.agents.tools.parsing_tools import make_meal_parsing_tools
from nira_backend.database.connection import DatabaseConnection
from nira_backend.llm.config import get_api_key

_SYSTEM_PROMPT = """\
You are NIRA's nutrition specialist.  You help the family track food intake,
log meals, analyse nutritional habits, and offer dietary guidance.

Your responsibilities:
- Log meals that family members eat (structured or from free-text descriptions).
- Add new food items to the food catalog when asked.
- Search the food catalog to find nutritional information.
- Retrieve and summarise meal history for any family member.
- Offer practical, supportive nutritional advice based on the data.

Guidelines:
- When logging a meal from free text, use the parse_and_log_meal tool.
- When the user gives specific numbers (grams, meal type), use log_meal.
- Always confirm what was logged so the user knows it was recorded.
- Be warm and encouraging — small, consistent habits matter.
- If you lack enough information to log something, ask one focused question.
"""


class NutritionAgent(BaseAgent):
    """
    Agent specialising in food, meals, and nutrition.

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
            + make_meal_entry_tools(db)
            + make_meal_parsing_tools(db, llm)
        )
        super().__init__(
            name="nutrition",
            system_prompt=_SYSTEM_PROMPT,
            tools=tools,
            llm=llm,
            data_dir=data_dir,
        )
