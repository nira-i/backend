"""Natural-language parsing tools.

These tools represent the *AI entry* path: the user describes something in
free text and the LLM extracts structured data from it, which is then stored
in the database.

Each factory receives the main LLM instance and the database connection so
tools can both parse and persist in one step.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Literal, Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from nira_backend.data_models.exercise import ExerciseEntry, MealLog
from nira_backend.data_models.health_record import (
    BloodGlucoseRecord,
    BloodPressureRecord,
    HeartRateRecord,
    HealthRecord,
    SleepRecord,
)
from nira_backend.database.connection import DatabaseConnection
from nira_backend.database.repositories import (
    ExerciseRepository,
    HealthRecordRepository,
    MealLogRepository,
)


# ---------------------------------------------------------------------------
# Intermediate extraction schemas (simpler for the LLM to fill in)
# ---------------------------------------------------------------------------


class _BloodPressureExtract(BaseModel):
    systolic_mmhg: int = Field(description="Systolic pressure in mmHg")
    diastolic_mmhg: int = Field(description="Diastolic pressure in mmHg")
    pulse_bpm: Optional[int] = Field(default=None, description="Pulse rate in bpm")
    notes: Optional[str] = Field(default=None)


class _BloodGlucoseExtract(BaseModel):
    glucose_mmol_l: float = Field(description="Blood glucose in mmol/L")
    measurement_context: Literal["fasting", "post_meal_1h", "post_meal_2h", "random"] = "random"
    notes: Optional[str] = Field(default=None)


class _HeartRateExtract(BaseModel):
    bpm: int = Field(description="Heart rate in beats per minute")
    measurement_context: Literal["resting", "active", "post_exercise", "sleeping"] = "resting"
    notes: Optional[str] = Field(default=None)


class _SleepExtract(BaseModel):
    duration_hours: float = Field(description="Total sleep duration in hours")
    quality: int = Field(ge=1, le=5, description="Quality 1 (very poor) to 5 (excellent)")
    notes: Optional[str] = Field(default=None)


class _MealExtract(BaseModel):
    food_name: str = Field(description="Name of the food")
    quantity_g: float = Field(description="Amount eaten in grams")
    meal_type: Literal["breakfast", "lunch", "dinner", "snack", "other"] = "other"
    notes: Optional[str] = Field(default=None)


class _ExerciseExtract(BaseModel):
    activity: str = Field(description="Activity name, e.g. 'running', 'yoga'")
    duration_minutes: int = Field(description="Duration in minutes")
    intensity: Literal["light", "moderate", "vigorous"] = "moderate"
    calories_burned: Optional[float] = Field(default=None)
    distance_km: Optional[float] = Field(default=None)
    notes: Optional[str] = Field(default=None)


_HEALTH_TYPE_MAP = {
    "blood_pressure": _BloodPressureExtract,
    "blood_glucose": _BloodGlucoseExtract,
    "heart_rate": _HeartRateExtract,
    "sleep": _SleepExtract,
}


# ---------------------------------------------------------------------------
# Health parsing tools
# ---------------------------------------------------------------------------


def make_health_parsing_tools(db: DatabaseConnection, llm: Any) -> list:
    """
    Return NL-parsing tools for health records.

    Args:
        db: Active database connection.
        llm: ChatGoogleGenerativeAI (or compatible) LangChain chat model.

    Returns:
        List of LangChain tool callables.
    """
    health_repo = HealthRecordRepository(db)

    @tool
    def parse_and_log_health(human_name: str, text: str) -> str:
        """
        Parse a natural-language health description and log it as a health record.

        Use this when the user describes a health reading in free text, e.g.:
        'My blood pressure this morning was 120 over 80' or
        'I slept 7.5 hours last night and feel pretty good'.

        Args:
            human_name: Full name of the family member the reading belongs to.
            text: Free-text description of the health reading.
        """
        classify_prompt = (
            f"Classify this text into exactly one health record type.\n"
            f"Types: blood_pressure, blood_glucose, heart_rate, sleep\n"
            f"Text: {text}\n"
            f"Reply with only the type name, nothing else."
        )
        type_response = llm.invoke(classify_prompt)
        record_type = type_response.content.strip().lower().replace(" ", "_")

        if record_type not in _HEALTH_TYPE_MAP:
            return (
                f"Could not classify '{text}' as a known health record type. "
                f"Please be more specific or use a structured entry tool."
            )

        extract_schema = _HEALTH_TYPE_MAP[record_type]
        structured_llm = llm.with_structured_output(extract_schema)
        extract_prompt = f"Extract health data from this text: {text}"

        try:
            extracted = structured_llm.invoke(extract_prompt)
        except Exception as exc:
            return f"Failed to extract health data: {exc}"

        measurement_map = {
            "blood_pressure": lambda e: BloodPressureRecord(
                systolic_mmhg=e.systolic_mmhg,
                diastolic_mmhg=e.diastolic_mmhg,
                pulse_bpm=e.pulse_bpm,
            ),
            "blood_glucose": lambda e: BloodGlucoseRecord(
                glucose_mmol_l=e.glucose_mmol_l,
                measurement_context=e.measurement_context,
            ),
            "heart_rate": lambda e: HeartRateRecord(
                bpm=e.bpm,
                measurement_context=e.measurement_context,
            ),
            "sleep": lambda e: SleepRecord(
                duration_hours=e.duration_hours,
                quality=e.quality,
            ),
        }

        try:
            measurement = measurement_map[record_type](extracted)
            record = HealthRecord(
                human_name=human_name,
                record_date=date.today(),
                record_type=record_type,  # type: ignore[arg-type]
                measurement=measurement,
                notes=getattr(extracted, "notes", None),
            )
            rid = health_repo.create(record)
            return (
                f"Parsed and logged {record_type} for {human_name} "
                f"[ID {rid}]: {measurement.model_dump_json()}"
            )
        except Exception as exc:
            return f"Failed to create health record: {exc}"

    return [parse_and_log_health]


# ---------------------------------------------------------------------------
# Meal parsing tools
# ---------------------------------------------------------------------------


def make_meal_parsing_tools(db: DatabaseConnection, llm: Any) -> list:
    """
    Return NL-parsing tools for meal logs.

    Args:
        db: Active database connection.
        llm: LangChain chat model.

    Returns:
        List of LangChain tool callables.
    """
    meal_repo = MealLogRepository(db)

    @tool
    def parse_and_log_meal(human_name: str, text: str) -> str:
        """
        Parse a natural-language meal description and log it.

        Use this when the user describes what they ate in free text, e.g.:
        'I had a bowl of oatmeal with banana for breakfast, about 250 grams'.

        Args:
            human_name: Full name of the family member who ate.
            text: Free-text description of the meal.
        """
        structured_llm = llm.with_structured_output(_MealExtract)
        prompt = (
            f"Extract the meal details from this text. "
            f"Estimate quantity_g if not stated explicitly.\n"
            f"Text: {text}"
        )
        try:
            extracted: _MealExtract = structured_llm.invoke(prompt)
        except Exception as exc:
            return f"Failed to extract meal data: {exc}"

        try:
            entry = MealLog(
                human_name=human_name,
                food_name=extracted.food_name,
                quantity_g=extracted.quantity_g,
                meal_type=extracted.meal_type,
                log_date=date.today(),
                notes=extracted.notes,
            )
            mid = meal_repo.create(entry)
            return (
                f"Parsed and logged meal for {human_name}: "
                f"{extracted.quantity_g}g of {extracted.food_name} "
                f"({extracted.meal_type}) [ID {mid}]"
            )
        except Exception as exc:
            return f"Failed to create meal log: {exc}"

    return [parse_and_log_meal]


# ---------------------------------------------------------------------------
# Exercise parsing tools
# ---------------------------------------------------------------------------


def make_exercise_parsing_tools(db: DatabaseConnection, llm: Any) -> list:
    """
    Return NL-parsing tools for exercise entries.

    Args:
        db: Active database connection.
        llm: LangChain chat model.

    Returns:
        List of LangChain tool callables.
    """
    exercise_repo = ExerciseRepository(db)

    @tool
    def parse_and_log_exercise(human_name: str, text: str) -> str:
        """
        Parse a natural-language exercise description and log it.

        Use this when the user describes an exercise session in free text, e.g.:
        'I went for a 5km run this morning, took about 30 minutes, felt intense'.

        Args:
            human_name: Full name of the family member who exercised.
            text: Free-text description of the exercise session.
        """
        structured_llm = llm.with_structured_output(_ExerciseExtract)
        prompt = (
            f"Extract the exercise session details from this text. "
            f"Estimate duration_minutes if not stated explicitly.\n"
            f"Text: {text}"
        )
        try:
            extracted: _ExerciseExtract = structured_llm.invoke(prompt)
        except Exception as exc:
            return f"Failed to extract exercise data: {exc}"

        try:
            entry = ExerciseEntry(
                human_name=human_name,
                exercise_date=date.today(),
                activity=extracted.activity,
                duration_minutes=extracted.duration_minutes,
                intensity=extracted.intensity,
                calories_burned=extracted.calories_burned,
                distance_km=extracted.distance_km,
                notes=extracted.notes,
            )
            eid = exercise_repo.create(entry)
            return (
                f"Parsed and logged exercise for {human_name}: "
                f"{extracted.activity} {extracted.duration_minutes} min "
                f"({extracted.intensity})"
                f"{f', {extracted.distance_km} km' if extracted.distance_km else ''}"
                f" [ID {eid}]"
            )
        except Exception as exc:
            return f"Failed to create exercise entry: {exc}"

    return [parse_and_log_exercise]
