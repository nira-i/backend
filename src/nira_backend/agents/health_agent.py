"""HealthAgent — handles all health record queries."""

from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI

from nira_backend.agents.base_agent import BaseAgent
from nira_backend.agents.tools.database_tools import make_shared_db_tools
from nira_backend.agents.tools.entry_tools import make_health_entry_tools
from nira_backend.agents.tools.parsing_tools import make_health_parsing_tools
from nira_backend.database.connection import DatabaseConnection
from nira_backend.llm.config import get_api_key

_SYSTEM_PROMPT = """\
You are NIRA's health specialist.  You help the family track and understand
their health metrics: blood pressure, blood glucose, heart rate, and sleep.

Your responsibilities:
- Log health readings that family members report (structured or from free text).
- Retrieve and summarise health history for any family member.
- Identify trends or unusual values and flag them gently.
- Offer general health information — but always recommend consulting a doctor
  for medical decisions.

Guidelines:
- When logging from free text, use the parse_and_log_health tool.
- When the user gives explicit numbers, use the specific structured tool
  (log_blood_pressure, log_blood_glucose, log_heart_rate, or log_sleep).
- Blood pressure: normal < 120/80, elevated 120-129/<80, high >= 130/80.
- Blood glucose fasting normal: 4.0–5.6 mmol/L.
- Heart rate resting normal: 60–100 bpm.
- Always confirm the record was saved with the key values.
- Be warm, calm, and informative — health data can be sensitive.
"""


class HealthAgent(BaseAgent):
    """
    Agent specialising in health record tracking and analysis.

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
        temperature: float = 0.2,
    ) -> None:
        llm = ChatGoogleGenerativeAI(
            model=llm_model,
            google_api_key=api_key or get_api_key("gemini"),
            temperature=temperature,
        )
        tools = (
            make_shared_db_tools(db)
            + make_health_entry_tools(db)
            + make_health_parsing_tools(db, llm)
        )
        super().__init__(
            name="health",
            system_prompt=_SYSTEM_PROMPT,
            tools=tools,
            llm=llm,
            data_dir=data_dir,
        )
