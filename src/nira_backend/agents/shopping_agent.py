"""ShoppingAgent — generates personalised weekly shopping lists."""

from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI

from nira_backend.agents.base_agent import BaseAgent
from nira_backend.agents.tools.database_tools import make_shared_db_tools
from nira_backend.agents.tools.shopping_tools import make_shopping_tools
from nira_backend.database.connection import DatabaseConnection
from nira_backend.llm.config import get_api_key

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

Structure the list by category:
  PROTEINS        — meat, fish, eggs, legumes, dairy proteins
  VEGETABLES      — prioritise seasonal and any missing groups
  FRUITS          — prioritise seasonal; aim for variety
  DAIRY & EGGS    — if not covered above
  PANTRY STAPLES  — grains, legumes, oils, spices, condiments
  OPTIONAL / NICE TO HAVE — items that would improve variety or nutrition

For each item include a brief reason in parentheses, e.g.:
  • Salmon (2 portions) — omega-3s; no fish detected in last 7 days
  • Kale (1 bunch) — in season; no leafy greens logged this week
  • Clementines (bag) — seasonal vitamin C; immune support in winter

HEALTH-AWARE RULES:
  - Elevated BP (systolic >130): favour low-sodium options; flag salty items
  - High blood glucose: prefer low-GI carbs; reduce simple sugars
  - Poor sleep logged: suggest magnesium-rich foods (leafy greens, nuts, seeds)
  - Low exercise logged recently: slightly lighter calorie density

GENERAL GUIDELINES:
  - Do NOT suggest items already well-stocked in the fridge/pantry.
  - DO suggest items that are running low or expiring soon as a "use first" note.
  - Keep the list practical — 15–25 items total, not an overwhelming catalogue.
  - Prioritise whole, minimally processed foods.
  - If multiple people are in the family, balance everyone's needs.
  - End with a brief (2–3 sentence) NUTRITIONAL RATIONALE explaining the
    key choices you made and what gaps they address.
"""


class ShoppingAgent(BaseAgent):
    """
    Agent that generates personalised weekly shopping lists.

    Analyses eating patterns, health conditions, nutritional gaps, seasonal
    produce, and fridge inventory to produce practical, health-aware lists.

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
        temperature: float = 0.4,
    ) -> None:
        llm = ChatGoogleGenerativeAI(
            model=llm_model,
            google_api_key=api_key or get_api_key("gemini"),
            temperature=temperature,
        )
        tools = make_shared_db_tools(db) + make_shopping_tools(db)
        super().__init__(
            name="shopping",
            system_prompt=_SYSTEM_PROMPT,
            tools=tools,
            llm=llm,
            data_dir=data_dir,
        )
