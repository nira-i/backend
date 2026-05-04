"""MainAgent — the single interface the user communicates with.

NIRA (Nutrition, Information, Record, Advisor) is the top-level agent that
orchestrates NutritionAgent, HealthAgent, and ExerciseAgent.  The user only
ever talks to NIRA; NIRA decides which specialist(s) to consult.
"""

from datetime import date
from pathlib import Path
from typing import Any

from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

from nira_backend.agents.base_agent import BaseAgent
from nira_backend.agents.exercise_agent import ExerciseAgent
from nira_backend.agents.health_agent import HealthAgent
from nira_backend.agents.nutrition_agent import NutritionAgent
from nira_backend.agents.shopping_agent import ShoppingAgent
from nira_backend.config import get_database_path
from nira_backend.data_models.human import Human
from nira_backend.database.connection import DatabaseConnection
from nira_backend.database.repositories import HumanRepository
from nira_backend.llm.config import get_api_key

_SYSTEM_PROMPT = """\
You are NIRA, a personal AI assistant for family health and wellness management.
You are warm, supportive, and practical.

You manage four specialist agents:
- Nutrition Agent: food/meal logging, nutritional analysis, fridge/pantry inventory,
  dietary suggestions based on recent habits and available ingredients.
- Health Agent: blood pressure, blood glucose, heart rate, sleep tracking and trends.
- Exercise Agent: exercise sessions, activity history, fitness motivation.
- Shopping Agent: personalised weekly shopping lists based on eating habits, health
  conditions, nutritional gaps, seasonal produce, and fridge inventory.

How to handle requests:
- For food/meal/nutrition/fridge/inventory/dietary advice → delegate to the Nutrition Agent.
- For health readings, records, or trends → delegate to the Health Agent.
- For exercise, workouts, or activity → delegate to the Exercise Agent.
- For shopping lists, groceries, what to buy, weekly shop → delegate to the Shopping Agent.
- For general family management (adding members, listing family) → handle directly.
- When a request spans multiple domains, consult each relevant agent in turn.

After getting a specialist's response, synthesise it into a clear, friendly
reply for the user.  Do not expose raw tool outputs verbatim unless the user
asks for details.

Always:
- Address the user's actual intent, not just the literal words.
- Be concise but complete.
- If you are unsure who sent the message or which family member it concerns,
  ask one focused clarifying question.
"""


class MainAgent(BaseAgent):
    """
    Top-level orchestrating agent.  This is the only class the caller
    (future API layer) needs to interact with.

    Args:
        db_path: Path to the SQLite database.  Defaults to the path from config.
        api_key: Gemini API key.  Reads from secrets file if not provided.
        data_dir: Override data directory for memory storage (tests).
        llm_model: Gemini model name.
        temperature: LLM temperature for the main agent.
    """

    def __init__(
        self,
        db_path: Path | None = None,
        api_key: str | None = None,
        data_dir: Any = None,
        llm_model: str = "gemini-2.0-flash",
        temperature: float = 0.5,
    ) -> None:
        resolved_api_key = api_key or get_api_key("gemini")
        resolved_db_path = db_path or get_database_path()

        self._db = DatabaseConnection(str(resolved_db_path))
        self._db.connect()

        self._nutrition_agent = NutritionAgent(
            db=self._db, api_key=resolved_api_key, data_dir=data_dir
        )
        self._health_agent = HealthAgent(
            db=self._db, api_key=resolved_api_key, data_dir=data_dir
        )
        self._exercise_agent = ExerciseAgent(
            db=self._db, api_key=resolved_api_key, data_dir=data_dir
        )
        self._shopping_agent = ShoppingAgent(
            db=self._db, api_key=resolved_api_key, data_dir=data_dir
        )

        llm = ChatGoogleGenerativeAI(
            model=llm_model,
            google_api_key=resolved_api_key,
            temperature=temperature,
        )

        tools = self._make_tools()

        super().__init__(
            name="main",
            system_prompt=_SYSTEM_PROMPT,
            tools=tools,
            llm=llm,
            data_dir=data_dir,
        )

    # ------------------------------------------------------------------
    # Public convenience method
    # ------------------------------------------------------------------

    def chat(self, message: str) -> str:
        """
        Send a message to NIRA and receive a response.

        This is the primary entry point for external callers.

        Args:
            message: The user's message.

        Returns:
            NIRA's response as a string.
        """
        return self.run(message)

    def close(self) -> None:
        """Close the database connection."""
        self._db.disconnect()

    def __enter__(self) -> "MainAgent":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Tool factory
    # ------------------------------------------------------------------

    def _make_tools(self) -> list:
        nutrition_agent = self._nutrition_agent
        health_agent = self._health_agent
        exercise_agent = self._exercise_agent
        shopping_agent = self._shopping_agent
        db = self._db

        @tool
        def ask_nutrition_agent(query: str) -> str:
            """
            Delegate a nutrition, food, or meal-related question to the
            Nutrition Agent.  Use for logging meals, searching food items,
            analysing eating habits, or any food-related request.

            Args:
                query: The specific question or task for the Nutrition Agent.
            """
            return nutrition_agent.run(query)

        @tool
        def ask_health_agent(query: str) -> str:
            """
            Delegate a health-record question to the Health Agent.  Use for
            logging blood pressure, blood glucose, heart rate, or sleep, and
            for reviewing health trends.

            Args:
                query: The specific question or task for the Health Agent.
            """
            return health_agent.run(query)

        @tool
        def ask_exercise_agent(query: str) -> str:
            """
            Delegate an exercise or physical activity question to the Exercise
            Agent.  Use for logging workouts, reviewing activity history, or
            exercise-related advice.

            Args:
                query: The specific question or task for the Exercise Agent.
            """
            return exercise_agent.run(query)

        @tool
        def ask_shopping_agent(query: str) -> str:
            """
            Delegate a shopping list or grocery planning request to the Shopping
            Agent.  Use for generating weekly shopping lists, recommending what
            to buy based on eating habits and health, or asking what groceries
            would improve the family's nutritional balance.

            Args:
                query: The specific shopping or grocery question.
            """
            return shopping_agent.run(query)

        @tool
        def add_family_member(
            name: str,
            gender: str,
            date_of_birth: str,
            weight_kg: float,
            height_cm: float,
        ) -> str:
            """
            Register a new family member in the system.

            Args:
                name: Full name of the person.
                gender: One of 'male', 'female', 'undisclosed'.
                date_of_birth: Date of birth in YYYY-MM-DD format.
                weight_kg: Current weight in kilograms.
                height_cm: Height in centimetres.
            """
            human_repo = HumanRepository(db)
            human = Human(
                name=name,
                gender=gender,  # type: ignore[arg-type]
                date_of_birth=date.fromisoformat(date_of_birth),
                weight=weight_kg,
                height=height_cm,
            )
            hid = human_repo.create(human)
            return (
                f"Family member '{name}' registered successfully [ID {hid}]. "
                f"BMI: {human.bmi} ({human.bmi_category})."
            )

        @tool
        def list_family_members() -> str:
            """List all family members currently registered in the system."""
            human_repo = HumanRepository(db)
            humans = human_repo.get_all()
            if not humans:
                return "No family members registered yet. Use add_family_member to add one."
            today = date.today()
            lines = []
            for h in humans:
                age = (
                    today.year
                    - h.date_of_birth.year
                    - (
                        (today.month, today.day)
                        < (h.date_of_birth.month, h.date_of_birth.day)
                    )
                )
                lines.append(
                    f"- {h.name}: {h.gender.value}, age {age}, "
                    f"BMI {h.bmi} ({h.bmi_category})"
                )
            return "Family members:\n" + "\n".join(lines)

        @tool
        def get_todays_summary(human_name: str) -> str:
            """
            Get a brief summary of today's logged data across all domains
            for a family member.

            Args:
                human_name: Name of the family member.
            """
            parts = []
            meal_summary = nutrition_agent.run(
                f"Summarise all meals logged today for {human_name} in one or two sentences."
            )
            parts.append(f"Nutrition: {meal_summary}")

            health_summary = health_agent.run(
                f"Summarise any health readings logged today for {human_name} briefly."
            )
            parts.append(f"Health: {health_summary}")

            exercise_summary = exercise_agent.run(
                f"Summarise any exercise logged today for {human_name} briefly."
            )
            parts.append(f"Exercise: {exercise_summary}")

            return "\n".join(parts)

        return [
            ask_nutrition_agent,
            ask_health_agent,
            ask_exercise_agent,
            ask_shopping_agent,
            add_family_member,
            list_family_members,
            get_todays_summary,
        ]
