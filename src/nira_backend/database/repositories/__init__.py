"""Repository implementations for each data model."""

from nira_backend.database.repositories.human_repository import HumanRepository
from nira_backend.database.repositories.food_repository import (
    FoodItemRepository,
    FoodRecipeRepository,
)
from nira_backend.database.repositories.health_repository import HealthRecordRepository

__all__ = [
    "HumanRepository",
    "FoodItemRepository",
    "FoodRecipeRepository",
    "HealthRecordRepository",
]
