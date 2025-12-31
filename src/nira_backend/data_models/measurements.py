from datetime import date, timedelta
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_serializer, field_validator, ConfigDict


class BaseMeasurement(BaseModel):
    """
    Base class for measurement quantities like length, mass, volume, etc.
    """
    
    measurement_date: date = Field(description="Date of the measurement")
    measurement_time: timedelta = Field(description="Time of the measurement since midnight")
    value: float = Field(description="Value of the measurement")
    unit: str = Field(description="Unit of the measurement")
    
    @field_validator("value")
    def validate_value(cls, value: float) -> float:
        """Validate that the measurement value is non-negative."""
        if value < 0:
            raise ValueError("Measurement value must be non-negative")
        return value


class WeightMeasurement(BaseMeasurement):
    """
    Represents a weight measurement.
    
    Example:
        >>> weight = WeightMeasurement(
        ...     measurement_date=date(2023, 10, 1),
        ...     measurement_time=timedelta(hours=8, minutes=30),
        ...     value=70.5,
        ...     unit="kg"
        ... )
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "measurement_date": "2023-10-01",
                    "measurement_time": "08:30:00",
                    "value": 70.5,
                    "unit": "kg"
                }
            ]
        }
    )
    value: float = Field(gt=0.5, le=150, description="Weight value")
    unit: Literal["kg", "lb", "g"] = Field(default="kg", description="Unit of the measurement (kg)")
    
    def convert_to_kg(self) -> float:
        """Convert the measurement to kilograms (kg)."""
        if self.unit == "kg":
            return self.value
        elif self.unit == "lb":
            return self.value * 0.453592
        elif self.unit == "g":
            return self.value / 1000
        else:
            raise ValueError(f"Unsupported unit for weight conversion: {self.unit}")
        
    def set_unit_to_kg(self) -> None:
        """Set the unit to kilograms (kg) and convert the value accordingly."""
        if self.unit != "kg":
            self.value = self.convert_to_kg()
            self.unit = "kg"


class LengthMeasurement(BaseMeasurement):
    """
    Represents a length measurement.
    
    Example:
        >>> length = LengthMeasurement(
        ...     measurement_date=date(2023, 10, 1),
        ...     measurement_time=timedelta(hours=9, minutes=0),
        ...     value=180.0,
        ...     unit="cm"
        ... )
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "measurement_date": "2023-10-01",
                    "measurement_time": "09:00:00",
                    "value": 180.0,
                    "unit": "cm"
                }
            ]
        }
    )
    value: float = Field(ge=30, le=300, description="Length value")
    unit: Literal["cm", "m", "in", "ft"] = Field(default="cm", description="Unit of the measurement (cm)")
    
    def convert_to_cm(self) -> float:
        """Convert the measurement to centimeters (cm)."""
        if self.unit == "cm":
            return self.value
        elif self.unit == "m":
            return self.value * 100
        elif self.unit == "in":
            return self.value * 2.54
        elif self.unit == "ft":
            return self.value * 30.48
        else:
            raise ValueError(f"Unsupported unit for length conversion: {self.unit}")
        
    def set_unit_to_cm(self) -> None:
        """Set the unit to centimeters (cm) and convert the value accordingly."""
        if self.unit != "cm":
            self.value = self.convert_to_cm()
            self.unit = "cm"


class BodyShapeMeasurements(BaseModel):
    """
    Represents various human body measurements.
    
    Attributes:
        neck_circumference: Neck circumference
        waist_circumference: Waist circumference
        hip_circumference: Hip circumference
        wrist_circumference: Wrist circumference
        forearm_circumference: Forearm circumference
    
    Example:
        >>> measurements = BodyShapeMeasurements(
        ...     neck_circumference=LengthMeasurement(
        ...         measurement_date=date(2023, 10, 1),
        ...         measurement_time=timedelta(hours=8, minutes=30),
        ...         value=40.0,
        ...         unit="cm"
        ...     ),
        ...     waist_circumference=LengthMeasurement(
        ...         measurement_date=date(2023, 10, 1),
        ...         measurement_time=timedelta(hours=8, minutes=30),
        ...         value=80.0,
        ...         unit="cm"
        ...     ),
        ...     hip_circumference=LengthMeasurement(
        ...         measurement_date=date(2023, 10, 1),
        ...         measurement_time=timedelta(hours=8, minutes=30),
        ...         value=90.0,
        ...         unit="cm"
        ...     ),
        ...     wrist_circumference=LengthMeasurement(
        ...         measurement_date=date(2023, 10, 1),
        ...         measurement_time=timedelta(hours=8, minutes=30),
        ...         value=18.0,
        ...         unit="cm"
        ...     ),
        ...     forearm_circumference=LengthMeasurement(
        ...         measurement_date=date(2023, 10, 1),
        ...         measurement_time=timedelta(hours=8, minutes=30),
        ...         value=30.0,
        ...         unit="cm"
        ...     )
        ... )
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "neck_circumference": {
                        "measurement_date": "2023-10-01",
                        "measurement_time": "08:30:00",
                        "value": 38.0,
                        "unit": "cm"
                    },
                    "waist_circumference": {
                        "measurement_date": "2023-10-01",
                        "measurement_time": "08:30:00",
                        "value": 75.0,
                        "unit": "cm"
                    },
                    "hip_circumference": {
                        "measurement_date": "2023-10-01",
                        "measurement_time": "08:30:00",
                        "value": 85.0,
                        "unit": "cm"
                    },
                    "wrist_circumference": {
                        "measurement_date": "2023-10-01",
                        "measurement_time": "08:30:00",
                        "value": 17.0,
                        "unit": "cm"
                    },
                    "forearm_circumference": {
                        "measurement_date": "2023-10-01",
                        "measurement_time": "08:30:00",
                        "value": 28.0,
                        "unit": "cm"
                    }
                }
            ]
        }
    )
    
    neck_circumference: Optional[LengthMeasurement] = Field(default=None, description="Neck circumference")
    waist_circumference: Optional[LengthMeasurement] = Field(default=None, description="Waist circumference")
    hip_circumference: Optional[LengthMeasurement] = Field(default=None, description="Hip circumference")
    wrist_circumference: Optional[LengthMeasurement] = Field(default=None, description="Wrist circumference")
    forearm_circumference: Optional[LengthMeasurement] = Field(default=None, description="Forearm circumference")

    @field_validator("*", mode="after")
    def set_measurement_in_cm(cls, bodyshape: Optional[LengthMeasurement]) -> Optional[LengthMeasurement]:
        if bodyshape is not None:
            bodyshape.set_unit_to_cm()
        return bodyshape

    @field_validator("neck_circumference", mode="after")
    def validate_neck(cls, neck: Optional[LengthMeasurement]) -> Optional[LengthMeasurement]:
        if neck is not None and not (8 <= neck.convert_to_cm() <= 60):
            raise ValueError("Neck circumference must be between 8 cm and 60 cm")
        return neck
    
    @field_validator("waist_circumference", mode="after")
    def validate_waist(cls, waist: Optional[LengthMeasurement]) -> Optional[LengthMeasurement]:
        if waist is not None and not (20 <= waist.convert_to_cm() <= 150):
            raise ValueError("Waist circumference must be between 20 cm and 150 cm")
        return waist
    
    @field_validator("hip_circumference", mode="after")
    def validate_hip(cls, hip: Optional[LengthMeasurement]) -> Optional[LengthMeasurement]:
        if hip is not None and not (20 <= hip.convert_to_cm() <= 200):
            raise ValueError("Hip circumference must be between 20 cm and 200 cm")
        return hip
    
    @field_validator("wrist_circumference", mode="after")
    def validate_wrist(cls, wrist: Optional[LengthMeasurement]) -> Optional[LengthMeasurement]:
        if wrist is not None and not (5 <= wrist.convert_to_cm() <= 40):
            raise ValueError("Wrist circumference must be between 5 cm and 40 cm")
        return wrist