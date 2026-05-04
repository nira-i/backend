"""NutritionAgent — handles all food, meal, inventory, and dietary advice queries."""

from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI

from nira_backend.agents.base_agent import BaseAgent
from nira_backend.agents.tools.database_tools import (
    make_dietary_tools,
    make_fridge_db_tools,
    make_shared_db_tools,
)
from nira_backend.agents.tools.entry_tools import (
    make_fridge_entry_tools,
    make_meal_entry_tools,
)
from nira_backend.agents.tools.parsing_tools import (
    make_fridge_parsing_tools,
    make_meal_parsing_tools,
)
from nira_backend.database.connection import DatabaseConnection
from nira_backend.llm.config import get_api_key

_SYSTEM_PROMPT = """\
You are NIRA's nutrition specialist.  You help the family track food intake,
manage their household food inventory, analyse eating habits, and provide
personalised dietary suggestions.

YOUR RESPONSIBILITIES:

1. Meal logging
   - Log meals that family members eat (structured input or free-text).
   - Use parse_and_log_meal for free-text descriptions.
   - Use log_meal when the user gives explicit amounts.

2. Food catalog
   - Add new food items to the catalog via add_food_item.
   - Search the catalog with search_food_catalog.

3. Fridge / pantry inventory
   - Add items: use parse_and_add_to_fridge for free text (e.g. "I bought 6 eggs
     and 1 litre of oat milk") or add_to_fridge for structured input.
   - Update quantities with update_fridge_quantity.
   - Remove items with remove_from_fridge.
   - Show contents with list_fridge_contents; warn about expiring items.
   - Always mention items expiring within 3 days when relevant.

4. Dietary suggestions
   - When asked for food suggestions or meal recommendations, ALWAYS call
     get_dietary_context first to gather recent meals, health data, and inventory.
   - Base suggestions on what is actually available in the fridge when asked.
   - Consider health metrics (e.g. suggest low-sodium foods if blood pressure is
     elevated, or low-sugar options if glucose is borderline).
   - Prioritise ingredients expiring soon to reduce waste.
   - Be specific — name actual foods and meals, not generic advice.
   - Offer 2–3 concrete meal ideas rather than a long list.

GUIDELINES:
- Always confirm what was logged or added so the user knows it was recorded.
- Be warm, practical, and encouraging — small consistent habits matter.
- If you lack key information to log something, ask one focused question.
- Never fabricate nutritional data; only report what is in the database.
"""


class NutritionAgent(BaseAgent):
    """
    Agent specialising in food, meals, fridge inventory, and dietary advice.

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
            + make_fridge_db_tools(db)
            + make_dietary_tools(db)
            + make_meal_entry_tools(db)
            + make_fridge_entry_tools(db)
            + make_meal_parsing_tools(db, llm)
            + make_fridge_parsing_tools(db, llm)
        )
        super().__init__(
            name="nutrition",
            system_prompt=_SYSTEM_PROMPT,
            tools=tools,
            llm=llm,
            data_dir=data_dir,
        )
