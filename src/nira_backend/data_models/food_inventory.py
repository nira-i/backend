"""Fridge and pantry inventory data models."""

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class FridgeItem(BaseModel):
    """
    A food item currently held in the household inventory (fridge, freezer, or pantry).

    Quantities are stored in the unit provided — the system does **not** normalise
    to grams so that natural units like "6 eggs" or "2 litres of milk" are preserved.

    Attributes:
        food_name: Name of the food item.
        quantity: Amount currently available (in ``unit``).
        unit: Unit of measurement.
        location: Where the item is stored.
        added_date: Date the item was added to the inventory.
        expiry_date: Best-before or use-by date (optional).
        notes: Free-text notes, e.g. "opened", "homemade", "organic".
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "food_name": "Eggs",
                    "quantity": 6,
                    "unit": "pieces",
                    "location": "fridge",
                    "added_date": "2024-01-15",
                    "expiry_date": "2024-01-29",
                },
                {
                    "food_name": "Oat milk",
                    "quantity": 1.0,
                    "unit": "l",
                    "location": "fridge",
                    "added_date": "2024-01-15",
                },
            ]
        }
    )

    food_name: str = Field(min_length=1, description="Name of the food item")
    quantity: float = Field(ge=0, description="Amount currently available")
    unit: Literal["g", "kg", "pieces", "ml", "l"] = Field(
        default="g", description="Unit of measurement"
    )
    location: Literal["fridge", "freezer", "pantry", "other"] = Field(
        default="fridge", description="Storage location"
    )
    added_date: date = Field(description="Date added to the inventory")
    expiry_date: Optional[date] = Field(
        default=None, description="Best-before or use-by date"
    )
    notes: Optional[str] = Field(default=None, description="Free-text notes")

    @field_validator("food_name")
    @classmethod
    def strip_whitespace(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Food name cannot be empty or just whitespace")
        return stripped

    @model_validator(mode="after")
    def expiry_after_added(self) -> "FridgeItem":
        if self.expiry_date is not None and self.expiry_date < self.added_date:
            raise ValueError("expiry_date cannot be before added_date")
        return self

    @property
    def quantity_display(self) -> str:
        """Human-readable quantity string, e.g. '6 pieces' or '250 g'."""
        n = int(self.quantity) if self.quantity == int(self.quantity) else self.quantity
        if self.unit == "pieces":
            return f"{n} piece{'s' if n != 1 else ''}"
        return f"{n} {self.unit}"

    @property
    def days_until_expiry(self) -> Optional[int]:
        """Number of days until expiry, or None if no expiry date."""
        if self.expiry_date is None:
            return None
        return (self.expiry_date - date.today()).days

    @property
    def is_expired(self) -> bool:
        """True if the item has passed its expiry date."""
        if self.expiry_date is None:
            return False
        return date.today() > self.expiry_date
