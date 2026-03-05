"""Health record data models for tracking various health metrics."""

from datetime import date, time
from typing import Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict


class BloodPressureRecord(BaseModel):
    """
    A single blood pressure reading.

    Attributes:
        systolic_mmhg: Systolic pressure in mmHg (upper value).
        diastolic_mmhg: Diastolic pressure in mmHg (lower value).
        pulse_bpm: Optional pulse rate in beats per minute.

    Example:
        >>> bp = BloodPressureRecord(systolic_mmhg=120, diastolic_mmhg=80)
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"systolic_mmhg": 120, "diastolic_mmhg": 80, "pulse_bpm": 72}]
        }
    )

    systolic_mmhg: int = Field(
        ge=50, le=300, description="Systolic blood pressure in mmHg"
    )
    diastolic_mmhg: int = Field(
        ge=30, le=200, description="Diastolic blood pressure in mmHg"
    )
    pulse_bpm: Optional[int] = Field(
        default=None, ge=20, le=300, description="Pulse rate in beats per minute"
    )

    @field_validator("diastolic_mmhg")
    @classmethod
    def validate_diastolic_less_than_systolic(cls, diastolic: int) -> int:
        return diastolic

    def model_post_init(self, __context: object) -> None:
        if self.diastolic_mmhg >= self.systolic_mmhg:
            raise ValueError(
                "Diastolic pressure must be less than systolic pressure"
            )

    @property
    def category(self) -> str:
        """Classify blood pressure according to standard ranges."""
        if self.systolic_mmhg < 120 and self.diastolic_mmhg < 80:
            return "Normal"
        elif self.systolic_mmhg < 130 and self.diastolic_mmhg < 80:
            return "Elevated"
        elif self.systolic_mmhg < 140 or self.diastolic_mmhg < 90:
            return "High Blood Pressure Stage 1"
        else:
            return "High Blood Pressure Stage 2"


class BloodGlucoseRecord(BaseModel):
    """
    A single blood glucose reading.

    Attributes:
        glucose_mmol_l: Blood glucose in mmol/L.
        measurement_context: Whether the reading was fasting, post-meal, etc.

    Example:
        >>> glucose = BloodGlucoseRecord(glucose_mmol_l=5.5, measurement_context="fasting")
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"glucose_mmol_l": 5.5, "measurement_context": "fasting"}]
        }
    )

    glucose_mmol_l: float = Field(
        ge=0.5, le=50.0, description="Blood glucose concentration in mmol/L"
    )
    measurement_context: Literal["fasting", "post_meal_1h", "post_meal_2h", "random"] = Field(
        default="random", description="Context in which the measurement was taken"
    )

    @property
    def glucose_mg_dl(self) -> float:
        """Convert glucose value to mg/dL."""
        return round(self.glucose_mmol_l * 18.0182, 1)

    @property
    def category(self) -> str:
        """Classify glucose level based on fasting reference ranges (mmol/L)."""
        if self.measurement_context == "fasting":
            if self.glucose_mmol_l < 3.9:
                return "Low"
            elif self.glucose_mmol_l <= 5.5:
                return "Normal"
            elif self.glucose_mmol_l <= 6.9:
                return "Pre-diabetic"
            else:
                return "Diabetic range"
        return "Unknown (non-fasting)"


class HeartRateRecord(BaseModel):
    """
    A resting or active heart rate reading.

    Attributes:
        bpm: Heart rate in beats per minute.
        measurement_context: Whether it was resting, active, etc.
    """

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"bpm": 65, "measurement_context": "resting"}]}
    )

    bpm: int = Field(ge=20, le=300, description="Heart rate in beats per minute")
    measurement_context: Literal["resting", "active", "post_exercise", "sleeping"] = Field(
        default="resting", description="Context in which the heart rate was measured"
    )

    @property
    def category(self) -> str:
        """Classify resting heart rate (only applies to resting context)."""
        if self.measurement_context != "resting":
            return "N/A (non-resting)"
        if self.bpm < 60:
            return "Bradycardic (low)"
        elif self.bpm <= 100:
            return "Normal"
        else:
            return "Tachycardic (high)"


class SleepRecord(BaseModel):
    """
    A sleep record capturing duration and quality.

    Attributes:
        duration_hours: Total sleep duration in hours.
        quality: Subjective quality rating 1-5 (1=very poor, 5=excellent).
        bedtime: Optional time of going to bed.
        wake_time: Optional time of waking up.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"duration_hours": 7.5, "quality": 4}]
        }
    )

    duration_hours: float = Field(
        ge=0.0, le=24.0, description="Total sleep duration in hours"
    )
    quality: int = Field(
        ge=1, le=5, description="Subjective quality rating 1 (very poor) to 5 (excellent)"
    )
    bedtime: Optional[time] = Field(default=None, description="Time of going to bed")
    wake_time: Optional[time] = Field(default=None, description="Time of waking up")

    @property
    def quality_label(self) -> str:
        """Human-readable quality label."""
        labels = {1: "Very Poor", 2: "Poor", 3: "Fair", 4: "Good", 5: "Excellent"}
        return labels[self.quality]


HealthMeasurement = Union[BloodPressureRecord, BloodGlucoseRecord, HeartRateRecord, SleepRecord]


class HealthRecord(BaseModel):
    """
    A health record for a person, linking a date to a specific measurement.

    Attributes:
        human_name: Name of the person this record belongs to.
        record_date: Date of the measurement.
        record_type: Type of measurement stored in `measurement`.
        measurement: The actual measurement data.
        notes: Optional free-text notes.

    Example:
        >>> record = HealthRecord(
        ...     human_name="John Doe",
        ...     record_date=date(2024, 1, 15),
        ...     record_type="blood_pressure",
        ...     measurement=BloodPressureRecord(systolic_mmhg=118, diastolic_mmhg=76),
        ... )
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "human_name": "John Doe",
                    "record_date": "2024-01-15",
                    "record_type": "blood_pressure",
                    "measurement": {"systolic_mmhg": 118, "diastolic_mmhg": 76},
                    "notes": "Measured after rest",
                }
            ]
        }
    )

    human_name: str = Field(min_length=1, description="Name of the person this record belongs to")
    record_date: date = Field(description="Date the measurement was taken")
    record_type: Literal[
        "blood_pressure", "blood_glucose", "heart_rate", "sleep"
    ] = Field(description="Type of health measurement")
    measurement: HealthMeasurement = Field(description="The measurement data")
    notes: Optional[str] = Field(default=None, description="Optional free-text notes")

    @field_validator("human_name")
    @classmethod
    def validate_human_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Human name cannot be empty or just whitespace")
        return stripped

    @field_validator("record_date")
    @classmethod
    def validate_record_date(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("Record date cannot be in the future")
        return value
