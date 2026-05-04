"""LangChain tool factories for NIRA agents."""

from nira_backend.agents.tools.database_tools import (
    make_shared_db_tools,
    make_fridge_db_tools,
    make_dietary_tools,
)
from nira_backend.agents.tools.shopping_tools import make_shopping_tools
from nira_backend.agents.tools.entry_tools import (
    make_health_entry_tools,
    make_meal_entry_tools,
    make_exercise_entry_tools,
    make_fridge_entry_tools,
)
from nira_backend.agents.tools.parsing_tools import (
    make_health_parsing_tools,
    make_meal_parsing_tools,
    make_exercise_parsing_tools,
    make_fridge_parsing_tools,
)

__all__ = [
    "make_shared_db_tools",
    "make_fridge_db_tools",
    "make_dietary_tools",
    "make_shopping_tools",
    "make_health_entry_tools",
    "make_meal_entry_tools",
    "make_exercise_entry_tools",
    "make_fridge_entry_tools",
    "make_health_parsing_tools",
    "make_meal_parsing_tools",
    "make_exercise_parsing_tools",
    "make_fridge_parsing_tools",
]
