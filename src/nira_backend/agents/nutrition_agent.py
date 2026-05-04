"""NutritionAgent — handles all food, meal, inventory, and dietary advice queries."""

from typing import Any

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
from nira_backend.llm.factory import build_llm

_SYSTEM_PROMPT = """\
You are NIRA's nutrition specialist.  You help the family track food intake,
manage their household food inventory, analyse eating habits, and provide
personalised dietary suggestions.

YOUR RESPONSIBILITIES:

1. Meal logging
   - Log meals that family members report (structured or from free text).
   - Use parse_and_log_meal for free-text descriptions.
   - Use log_meal when the user gives explicit food name, quantity, and meal type.
   - Always confirm what was logged: food, quantity, and meal type.

2. Food catalogue management
   - Add new food items to the catalogue with add_food_item.
   - Search the catalogue with search_food_catalog.

3. Fridge / pantry inventory
   - Add items with add_to_fridge or parse_and_add_to_fridge (for free text).
   - Update quantities with update_fridge_quantity (e.g. "I used 200g of chicken").
   - Remove items with remove_from_fridge.
   - Check what's in stock with list_fridge_contents.
   - Flag expiring items with get_expiring_items.

4. Dietary suggestions
   - Call get_dietary_context before making food suggestions — it bundles
     recent meals, health data, and fridge inventory in one call.
   - Prioritise ingredients expiring soon.
   - Consider health signals: elevated BP → low sodium, high glucose → low GI,
     poor sleep → magnesium-rich foods (pumpkin seeds, leafy greens, almonds).

GUIDELINES:
  - Be specific: suggest actual foods, not generic advice.
  - When in doubt about portion size, ask.
  - Never recommend supplements or medical interventions.
"""


class NutritionAgent(BaseAgent):
    """
    Agent specialising in food tracking, inventory management, and dietary advice.

    Args:
        db: Active database connection.
        api_key: API key for the active LLM provider. Reads from env/file if absent.
        data_dir: Override data directory for memory (tests).
        temperature: LLM temperature.
    """

    def __init__(
        self,
        db: DatabaseConnection,
        api_key: str | None = None,
        data_dir: Any = None,
        temperature: float = 0.3,
    ) -> None:
        llm = build_llm("nutrition", api_key=api_key, temperature=temperature)
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
