from datetime import date
from pydantic import BaseModel, Field


class Human(BaseModel):
    name: str
    gender: str
    date_of_birth: date
    weight: float = Field(gt=0)
    height: float = Field(gt=0)
