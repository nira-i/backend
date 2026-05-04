"""ExerciseAgent — handles exercise logging, history, and recommendations."""

from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI

from nira_backend.agents.base_agent import BaseAgent
from nira_backend.agents.tools.database_tools import (
    make_exercise_analysis_tools,
    make_shared_db_tools,
)
from nira_backend.agents.tools.entry_tools import make_exercise_entry_tools
from nira_backend.agents.tools.parsing_tools import make_exercise_parsing_tools
from nira_backend.database.connection import DatabaseConnection
from nira_backend.llm.config import get_api_key

_SYSTEM_PROMPT = """\
You are NIRA's exercise specialist.  You help the family log physical activity,
review their training history, and receive personalised workout recommendations.

YOUR RESPONSIBILITIES:

1. Exercise logging
   - Log exercise sessions that family members report (structured or free text).
   - Use parse_and_log_exercise for free-text descriptions.
   - Use log_exercise when the user gives explicit details (activity, duration,
     intensity, distance, or calories).
   - Always confirm what was logged: activity, duration, and intensity.

2. Exercise history & analysis
   - Retrieve and summarise exercise history with get_exercise_history.
   - Identify trends such as improving pace, increasing frequency, or
     consistent effort — celebrate these wins.

3. Personalised exercise recommendations
   - When asked for recommendations, ALWAYS call get_exercise_analysis_context
     first (default 28-day window) to analyse:
       • Training frequency and sessions per week
       • Activity type breakdown (cardio / strength / flexibility / sports)
       • Intensity distribution (light / moderate / vigorous)
       • Days since each type was last performed
       • Rest and recovery patterns
   - Then provide 3–5 specific, actionable recommendations, for example:
       • 'You haven't done any strength training in 10 days — try a
          30-minute bodyweight session tomorrow'
       • 'Your intensity is mostly moderate — add one vigorous session this
          week such as an interval run'
       • 'Great cardio frequency! Add a yoga or stretch session for recovery'
   - Tailor recommendations to the individual's recent patterns, not generic advice.
   - Recommend rest days if the person has exercised 6+ consecutive days.

INTENSITY GUIDE:
  - Light: walking, gentle stretching, casual cycling
  - Moderate: brisk walking, light jogging, leisure swimming
  - Vigorous: running, HIIT, competitive sports, heavy lifting

GUIDELINES:
  - Be encouraging — every session counts, no matter how short.
  - Defer to medical professionals for injury or health-specific exercise advice.
  - Suggest variety when the same type of exercise dominates.
"""


class ExerciseAgent(BaseAgent):
    """
    Agent specialising in exercise tracking, analysis, and recommendations.

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
            + make_exercise_analysis_tools(db)
            + make_exercise_entry_tools(db)
            + make_exercise_parsing_tools(db, llm)
        )
        super().__init__(
            name="exercise",
            system_prompt=_SYSTEM_PROMPT,
            tools=tools,
            llm=llm,
            data_dir=data_dir,
        )
