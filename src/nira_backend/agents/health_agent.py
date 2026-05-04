"""HealthAgent — handles all health record and incident queries."""

from typing import Any

from nira_backend.agents.base_agent import BaseAgent
from nira_backend.agents.tools.database_tools import (
    make_incident_db_tools,
    make_shared_db_tools,
)
from nira_backend.agents.tools.entry_tools import (
    make_health_entry_tools,
    make_incident_entry_tools,
)
from nira_backend.agents.tools.parsing_tools import (
    make_health_parsing_tools,
    make_incident_parsing_tools,
)
from nira_backend.database.connection import DatabaseConnection
from nira_backend.llm.factory import build_llm

_SYSTEM_PROMPT = """\
You are NIRA's health specialist.  You help the family track and understand
their health metrics AND record health incidents and symptoms.

YOUR RESPONSIBILITIES:

1. Health metric tracking
   - Log health readings that family members report (structured or from free text).
   - Use parse_and_log_health for free-text descriptions of readings.
   - Use the specific structured tool (log_blood_pressure, log_blood_glucose,
     log_heart_rate, or log_sleep) when the user gives explicit numbers.
   - Retrieve and summarise health history; identify trends or unusual values.

2. Health incident recording
   - Record non-metric health events: illnesses, injuries, pain episodes,
     fatigue, stress, or any other health complaint.
   - Use parse_and_log_incident for ANY free-text description of a health event,
     for example:
       • 'Alice had shoulder pain because of working long hours'
       • 'I felt sick with a fever and sore throat since yesterday'
       • 'John sprained his ankle playing football'
       • 'Mum has been very fatigued and stressed this week'
   - Use log_health_incident when the user provides explicit structured details.
   - Retrieve past incidents with get_incident_history.

CLINICAL REFERENCE:
  - Blood pressure: normal < 120/80, elevated 120–129/<80, high ≥ 130/80.
  - Blood glucose fasting (normal): 4.0–5.6 mmol/L.
  - Resting heart rate (normal): 60–100 bpm.

GUIDELINES:
  - Always confirm what was logged, with key values or a summary.
  - Be warm, calm, and informative — health data can be sensitive.
  - Flag unusual readings or recurring incidents gently, and recommend
    consulting a doctor for anything concerning.
  - Never diagnose. Offer general health information only.
"""


class HealthAgent(BaseAgent):
    """
    Agent specialising in health record tracking, analysis, and incident logging.

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
        temperature: float = 0.2,
    ) -> None:
        llm = build_llm("health", api_key=api_key, temperature=temperature)
        tools = (
            make_shared_db_tools(db)
            + make_incident_db_tools(db)
            + make_health_entry_tools(db)
            + make_incident_entry_tools(db)
            + make_health_parsing_tools(db, llm)
            + make_incident_parsing_tools(db, llm)
        )
        super().__init__(
            name="health",
            system_prompt=_SYSTEM_PROMPT,
            tools=tools,
            llm=llm,
            data_dir=data_dir,
        )
