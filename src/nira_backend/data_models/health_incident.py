"""Health incident data model for logging symptoms and non-metric health events."""

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


IncidentType = Literal["illness", "injury", "pain", "fatigue", "stress", "other"]
Severity = Literal["mild", "moderate", "severe"]


class HealthIncident(BaseModel):
    """
    A discrete health event experienced by a family member.

    Unlike structured metric readings (blood pressure, glucose), incidents
    capture qualitative events described in free text — a fever, shoulder pain
    from long hours at a desk, a headache, work-related fatigue, etc.

    Attributes:
        human_name: Name of the family member who experienced the incident.
        incident_date: Date the incident occurred.
        description: Clear, human-readable summary of what happened.
        symptoms: List of specific symptoms extracted from the description.
        severity: Perceived severity — mild, moderate, or severe.
        body_part: Body part affected (e.g. "shoulder", "head", "chest").
        incident_type: Broad category of the incident.
        notes: Any additional context or follow-up notes.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "human_name": "Alice",
                    "incident_date": "2024-01-15",
                    "description": "Felt sick with a fever and sore throat",
                    "symptoms": ["fever", "sore throat", "fatigue"],
                    "severity": "moderate",
                    "body_part": None,
                    "incident_type": "illness",
                },
                {
                    "human_name": "John",
                    "incident_date": "2024-01-15",
                    "description": "Shoulder pain after working long hours at desk",
                    "symptoms": ["shoulder pain", "stiffness"],
                    "severity": "mild",
                    "body_part": "shoulder",
                    "incident_type": "pain",
                },
            ]
        }
    )

    human_name: str = Field(min_length=1, description="Name of the affected person")
    incident_date: date = Field(description="Date the incident occurred")
    description: str = Field(
        min_length=3,
        description="Clear summary of the health event",
    )
    symptoms: list[str] = Field(
        default_factory=list,
        description="Specific symptoms or complaints",
    )
    severity: Optional[Severity] = Field(
        default=None,
        description="Perceived severity: mild, moderate, or severe",
    )
    body_part: Optional[str] = Field(
        default=None,
        description="Body part primarily affected, if applicable",
    )
    incident_type: IncidentType = Field(
        default="other",
        description="Category: illness, injury, pain, fatigue, stress, or other",
    )
    notes: Optional[str] = Field(
        default=None, description="Additional context or follow-up"
    )

    @field_validator("human_name", "description")
    @classmethod
    def strip_and_require(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field cannot be empty or just whitespace")
        return stripped

    @field_validator("symptoms")
    @classmethod
    def strip_symptoms(cls, symptoms: list[str]) -> list[str]:
        return [s.strip() for s in symptoms if s.strip()]

    @field_validator("body_part")
    @classmethod
    def normalise_body_part(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return value.strip().lower() or None
