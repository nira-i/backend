"""Repository implementations for each data model."""

from nira_backend.database.repositories.human_repository import HumanRepository
from nira_backend.database.repositories.food_repository import (
    FoodItemRepository,
    FoodRecipeRepository,
)
from nira_backend.database.repositories.health_repository import HealthRecordRepository
from nira_backend.database.repositories.meal_repository import MealLogRepository
from nira_backend.database.repositories.exercise_repository import ExerciseRepository
from nira_backend.database.repositories.fridge_repository import FridgeInventoryRepository
from nira_backend.database.repositories.incident_repository import HealthIncidentRepository

__all__ = [
    "HumanRepository",
    "FoodItemRepository",
    "FoodRecipeRepository",
    "HealthRecordRepository",
    "MealLogRepository",
    "ExerciseRepository",
    "FridgeInventoryRepository",
    "HealthIncidentRepository",
]
