from datetime import date, timedelta
from typing import Literal
from pydantic import BaseModel, Field, field_serializer, field_validator, ConfigDict


class Human(BaseModel):
    """
    Represents a human with basic physical attributes.
    
    Attributes:
        name: Full name of the person
        gender: Gender (male, female, or undisclosed)
        date_of_birth: Date of birth (serialized as dd-mm-yyyy)
        weight: Weight in kilograms (kg)
        height: Height in centimeters (cm)
    
    Example:
        >>> human = Human(
        ...     name="John Doe",
        ...     gender="male",
        ...     date_of_birth=date(1990, 5, 15),
        ...     weight=75.5,
        ...     height=175.0
        ... )
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Jane Smith",
                    "gender": "female",
                    "date_of_birth": "15-05-1990",
                    "weight": 65.0,
                    "height": 165.0
                }
            ]
        }
    )
    
    name: str = Field(min_length=1, description="Full name of the person")
    gender: Literal["male", "female", "undisclosed"]
    date_of_birth: date
    weight: float = Field(gt=0.5, le=500, description="Weight in kilograms (kg)")
    height: float = Field(ge=30, le=300, description="Height in centimeters (cm)")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """Validate that name is not empty or just whitespace."""
        stripped = value.strip()
        if not stripped:
            raise ValueError("Name cannot be empty or just whitespace")
        return stripped

    @field_serializer("date_of_birth", when_used="json")
    def serialize_date(self, dt: date) -> str:
        return dt.strftime("%d-%m-%Y")
    
    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, value: date) -> date:
        """Validate that date of birth is not in the future and not more than 150 years ago."""
        today = date.today()
        if value > today:
            raise ValueError("Date of birth cannot be later than today")
        
        max_age_date = today - timedelta(days=150 * 365.25)
        if value < max_age_date:
            raise ValueError("Date of birth cannot be more than 150 years ago")
        
        return value
    
    def get_age(self) -> int:
        """Calculate the age of the human based on the date of birth."""
        today = date.today()
        age = today.year - self.date_of_birth.year
        # Adjust if birthday hasn't occurred yet this year
        if (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day):
            age -= 1
        return age
    
    @property
    def bmi(self) -> float:
        """
        Calculate Body Mass Index (BMI).
        
        Returns:
            BMI value calculated as weight (kg) / (height (m))^2
        """
        height_in_meters = self.height / 100
        return round(self.weight / (height_in_meters ** 2), 2)
    
    @property
    def bmi_category(self) -> str:
        """
        Get the BMI category based on WHO classification.
        
        Returns:
            BMI category string
        """
        bmi_value = self.bmi
        if bmi_value < 18.5:
            return "Underweight"
        elif bmi_value < 25:
            return "Normal weight"
        elif bmi_value < 30:
            return "Overweight"
        else:
            return "Obese"
