"""MainAgent — the single interface the user communicates with.

NIRA (Nutrition, Information, Record, Advisor) is the top-level agent that
orchestrates NutritionAgent, HealthAgent, ExerciseAgent, and ShoppingAgent.
The user only ever talks to NIRA; NIRA decides which specialist(s) to consult.
"""

from datetime import date
from pathlib import Path
from typing import Any

from langchain_core.tools import tool

from nira_backend.agents.base_agent import BaseAgent
from nira_backend.agents.exercise_agent import ExerciseAgent
from nira_backend.agents.health_agent import HealthAgent
from nira_backend.agents.nutrition_agent import NutritionAgent
from nira_backend.agents.shopping_agent import ShoppingAgent
from nira_backend.config import get_database_path
from nira_backend.data_models.human import Human
from nira_backend.database.connection import DatabaseConnection
from nira_backend.database.repositories import HumanRepository
from nira_backend.llm.factory import build_llm

_SYSTEM_PROMPT = """\
You are NIRA, a personal AI assistant for family health and wellness management.
You are warm, supportive, and practical.

You manage four specialist agents:
- Nutrition Agent: food/meal logging, nutritional analysis, fridge/pantry inventory,
  dietary suggestions based on recent habits and available ingredients.
- Health Agent: blood pressure, blood glucose, heart rate, sleep tracking and trends,
  plus non-metric health events (illness, injury, pain, fatigue, stress).
- Exercise Agent: exercise sessions, activity history, personalised fitness
  recommendations based on recent training patterns.
- Shopping Agent: personalised weekly shopping lists based on eating habits, health
  conditions, nutritional gaps, seasonal produce, and fridge inventory.

How to handle requests:
- For food/meal/nutrition/fridge/inventory/dietary advice → delegate to the Nutrition Agent.
- For health readings, records, trends, or health incidents → delegate to the Health Agent.
- For exercise, workouts, activity, or fitness recommendations → delegate to the Exercise Agent.
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
        api_key: API key for the active LLM provider. Reads from env/file if absent.
        data_dir: Override data directory for memory storage (tests).
        temperature: LLM temperature for the main agent.
    """

    def __init__(
        self,
        db_path: Path | None = None,
        api_key: str | None = None,
        data_dir: Any = None,
        temperature: float = 0.5,
    ) -> None:
        resolved_db_path = db_path or get_database_path()
        self._db = DatabaseConnection(resolved_db_path)

        self._nutrition_agent = NutritionAgent(
            db=self._db, api_key=api_key, data_dir=data_dir
        )
        self._health_agent = HealthAgent(
            db=self._db, api_key=api_key, data_dir=data_dir
        )
        self._exercise_agent = ExerciseAgent(
            db=self._db, api_key=api_key, data_dir=data_dir
        )
        self._shopping_agent = ShoppingAgent(
            db=self._db, api_key=api_key, data_dir=data_dir
        )

        llm = build_llm("main", api_key=api_key, temperature=temperature)
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
        """No-op — DatabaseConnection manages connections per-cursor."""
        pass

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
            analysing eating habits, managing the fridge/pantry inventory,
            or getting personalised dietary suggestions.

            Args:
                query: The nutrition-related question or instruction.
            """
            return nutrition_agent.run(query)

        @tool
        def ask_health_agent(query: str) -> str:
            """
            Delegate a health-related question to the Health Agent.  Use for
            logging health metrics (blood pressure, glucose, heart rate, sleep),
            reviewing health history, recording non-metric health events
            (illness, injury, pain, fatigue, stress), or analysing trends.

            Args:
                query: The health-related question or instruction.
            """
            return health_agent.run(query)

        @tool
        def ask_exercise_agent(query: str) -> str:
            """
            Delegate an exercise-related question to the Exercise Agent.  Use
            for logging workouts, reviewing activity history, or getting
            personalised exercise recommendations based on recent training.

            Args:
                query: The exercise-related question or instruction.
            """
            return exercise_agent.run(query)

        @tool
        def ask_shopping_agent(query: str) -> str:
            """
            Delegate a shopping-related question to the Shopping Agent.  Use
            for generating weekly shopping lists based on eating habits, health
            conditions, nutritional gaps, and fridge inventory.

            Args:
                query: The shopping-related question or instruction.
            """
            return shopping_agent.run(query)

        @tool
        def add_family_member(
            name: str,
            date_of_birth: str,
            gender: str,
            weight_kg: float,
            height_cm: float,
        ) -> str:
            """
            Add a new person to the family profile.

            Args:
                name: Full name of the family member.
                date_of_birth: Date of birth in YYYY-MM-DD format.
                gender: 'male', 'female', or 'other'.
                weight_kg: Current weight in kilograms.
                height_cm: Height in centimetres.
            """
            human = Human(
                name=name,
                date_of_birth=date.fromisoformat(date_of_birth),
                gender=gender,  # type: ignore[arg-type]
                weight=weight_kg,
                height=height_cm,
            )
            repo = HumanRepository(db)
            hid = repo.create(human)
            return (
                f"Added {name} to the family "
                f"(DOB: {date_of_birth}, {gender}, "
                f"{weight_kg} kg, {height_cm} cm) [ID {hid}]"
            )

        @tool
        def list_family_members() -> str:
            """List all family members with their basic profile information."""
            repo = HumanRepository(db)
            members = repo.get_all()
            if not members:
                return "No family members found. Add someone with add_family_member."
            lines = []
            for m in members:
                age_str = f"{m.age} yrs" if m.age is not None else "age unknown"
                bmi_str = f"BMI {m.bmi:.1f}" if m.bmi is not None else ""
                lines.append(
                    f"- {m.name}: {m.gender}, {age_str}"
                    + (f", {bmi_str}" if bmi_str else "")
                )
            return "Family members:\n" + "\n".join(lines)

        @tool
        def get_todays_summary() -> str:
            """
            Return a brief summary of today's date and any context the agents
            have in memory.  Use this to orient yourself at the start of a
            session.
            """
            return f"Today is {date.today().isoformat()}."

        return [
            ask_nutrition_agent,
            ask_health_agent,
            ask_exercise_agent,
            ask_shopping_agent,
            add_family_member,
            list_family_members,
            get_todays_summary,
        ]
