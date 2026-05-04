"""Exercise and meal-log data models."""

from datetime import date
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


class ExerciseEntry(BaseModel):
    """
    A single exercise session.

    Attributes:
        human_name: Name of the person who exercised.
        exercise_date: Date of the session.
        activity: Activity name, e.g. "running", "yoga", "cycling".
        duration_minutes: Duration of the session in minutes.
        intensity: Subjective intensity level.
        calories_burned: Optional estimated calories burned.
        distance_km: Optional distance covered (for cardio).
        notes: Optional free-text notes.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "human_name": "John Doe",
                    "exercise_date": "2024-01-15",
                    "activity": "running",
                    "duration_minutes": 30,
                    "intensity": "moderate",
                    "calories_burned": 300.0,
                    "distance_km": 5.0,
                }
            ]
        }
    )

    human_name: str = Field(min_length=1, description="Name of the person who exercised")
    exercise_date: date = Field(description="Date of the exercise session")
    activity: str = Field(min_length=1, description="Name of the activity")
    duration_minutes: int = Field(ge=1, description="Duration in minutes")
    intensity: Literal["light", "moderate", "vigorous"] = Field(
        default="moderate", description="Intensity level"
    )
    calories_burned: Optional[float] = Field(
        default=None, ge=0, description="Estimated calories burned"
    )
    distance_km: Optional[float] = Field(
        default=None, ge=0, description="Distance covered in kilometres"
    )
    notes: Optional[str] = Field(default=None, description="Free-text notes")

    @field_validator("human_name", "activity")
    @classmethod
    def strip_whitespace(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field cannot be empty or just whitespace")
        return stripped

    @field_validator("exercise_date")
    @classmethod
    def not_in_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("Exercise date cannot be in the future")
        return value


class MealLog(BaseModel):
    """
    A log entry for what a person ate at a given meal.

    Attributes:
        human_name: Name of the person who ate.
        food_name: Name of the food (free text, not necessarily in the food DB).
        quantity_g: Amount eaten in grams.
        meal_type: Which meal of the day.
        log_date: Date the meal was eaten.
        notes: Optional free-text notes.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "human_name": "Jane Smith",
                    "food_name": "Banana",
                    "quantity_g": 120.0,
                    "meal_type": "breakfast",
                    "log_date": "2024-01-15",
                }
            ]
        }
    )

    human_name: str = Field(min_length=1, description="Name of the person who ate")
    food_name: str = Field(min_length=1, description="Name of the food")
    quantity_g: float = Field(gt=0, description="Amount eaten in grams")
    meal_type: Literal["breakfast", "lunch", "dinner", "snack", "other"] = Field(
        default="other", description="Meal of the day"
    )
    log_date: date = Field(description="Date the meal was eaten")
    notes: Optional[str] = Field(default=None, description="Free-text notes")

    @field_validator("human_name", "food_name")
    @classmethod
    def strip_whitespace(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field cannot be empty or just whitespace")
        return stripped

    @field_validator("log_date")
    @classmethod
    def not_in_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("Log date cannot be in the future")
        return value
