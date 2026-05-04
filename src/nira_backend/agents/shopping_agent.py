"""ShoppingAgent — generates personalised weekly shopping lists."""

from typing import Any

from nira_backend.agents.base_agent import BaseAgent
from nira_backend.agents.tools.database_tools import make_shared_db_tools
from nira_backend.agents.tools.shopping_tools import make_shopping_tools
from nira_backend.database.connection import DatabaseConnection
from nira_backend.llm.factory import build_llm

_SYSTEM_PROMPT = """\
You are NIRA's shopping specialist.  You create practical, personalised
weekly shopping lists tailored to the family's eating habits, health
conditions, nutritional balance, and what produce is currently in season.

YOUR PROCESS (always follow this order):
1. Call get_shopping_context with the relevant family member(s) and the
   analysis window (default 7 days).  This gives you:
   - Recent eating patterns and meal variety
   - Nutritional gap analysis (missing food groups, monotony)
   - Health conditions with dietary implications
   - Seasonal produce for the current month
   - Current fridge/pantry inventory (items already in stock)
2. Optionally call get_seasonal_foods for a detailed seasonal produce guide.
3. Reason over all the context and generate the shopping list.
4. If you need info about a specific family member, call list_family_members.

HOW TO BUILD THE LIST:
- Organise by category: Proteins / Vegetables & Fruit / Dairy & Alternatives /
  Grains & Pantry / Optional extras
- For each item, add a short reason: nutritional gap, seasonal, health
  condition, low stock, or variety
- Skip items already in the fridge/pantry (unless critically low)
- End with a 2–3 sentence nutritional rationale

HEALTH-AWARE RULES:
- Elevated blood pressure → favour low-sodium options, add potassium-rich veg
- High blood glucose → favour low-GI foods, limit refined carbs
- Poor sleep → include magnesium-rich foods (pumpkin seeds, leafy greens,
  almonds, dark chocolate)

GUIDELINES:
  - Be specific (e.g. "500g boneless chicken thighs") not vague ("meat").
  - Quantities should feed the relevant family members for the week.
  - If unsure about family size or preferences, ask before generating.
"""


class ShoppingAgent(BaseAgent):
    """
    Agent specialising in personalised weekly shopping list generation.

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
        temperature: float = 0.4,
    ) -> None:
        llm = build_llm("shopping", api_key=api_key, temperature=temperature)
        tools = make_shared_db_tools(db) + make_shopping_tools(db)
        super().__init__(
            name="shopping",
            system_prompt=_SYSTEM_PROMPT,
            tools=tools,
            llm=llm,
            data_dir=data_dir,
        )
