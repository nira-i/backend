"""Food item data model with nutritional information."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


class FoodCategory(str, Enum):
    """Categories for food items."""

    FRUIT = "fruit"
    VEGETABLE = "vegetable"
    GRAIN = "grain"
    PROTEIN = "protein"
    DAIRY = "dairy"
    FAT = "fat"
    BEVERAGE = "beverage"
    SNACK = "snack"
    CONDIMENT = "condiment"
    OTHER = "other"


class NutritionalInfo(BaseModel):
    """
    Nutritional information per 100 grams of a food item.

    All values are per 100g unless stated otherwise.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "calories": 89.0,
                    "protein_g": 1.1,
                    "carbohydrates_g": 23.0,
                    "fat_g": 0.3,
                    "fiber_g": 2.6,
                    "sugar_g": 12.2,
                    "sodium_mg": 1.0,
                }
            ]
        }
    )

    calories: float = Field(ge=0, description="Calories (kcal) per 100g")
    protein_g: float = Field(ge=0, description="Protein in grams per 100g")
    carbohydrates_g: float = Field(ge=0, description="Carbohydrates in grams per 100g")
    fat_g: float = Field(ge=0, description="Fat in grams per 100g")
    fiber_g: float = Field(ge=0, default=0.0, description="Dietary fiber in grams per 100g")
    sugar_g: float = Field(ge=0, default=0.0, description="Sugar in grams per 100g")
    sodium_mg: float = Field(ge=0, default=0.0, description="Sodium in milligrams per 100g")

    @field_validator("sugar_g")
    @classmethod
    def validate_sugar_vs_carbs(cls, sugar: float) -> float:
        return sugar

    def scale_to_grams(self, grams: float) -> "NutritionalInfo":
        """
        Return a new NutritionalInfo scaled to a given serving size in grams.

        Args:
            grams: Serving size in grams to scale to.

        Returns:
            New NutritionalInfo scaled proportionally.
        """
        if grams < 0:
            raise ValueError("Serving size must be non-negative")
        factor = grams / 100.0
        return NutritionalInfo(
            calories=round(self.calories * factor, 2),
            protein_g=round(self.protein_g * factor, 2),
            carbohydrates_g=round(self.carbohydrates_g * factor, 2),
            fat_g=round(self.fat_g * factor, 2),
            fiber_g=round(self.fiber_g * factor, 2),
            sugar_g=round(self.sugar_g * factor, 2),
            sodium_mg=round(self.sodium_mg * factor, 2),
        )


class FoodItem(BaseModel):
    """
    Represents a food item with its nutritional information.

    Attributes:
        name: Name of the food item.
        category: Category of the food item.
        nutritional_info: Nutritional info per 100g.
        serving_size_g: Typical serving size in grams (optional).
        description: Optional description of the food item.
        brand: Optional brand name.

    Example:
        >>> banana = FoodItem(
        ...     name="Banana",
        ...     category=FoodCategory.FRUIT,
        ...     nutritional_info=NutritionalInfo(
        ...         calories=89.0,
        ...         protein_g=1.1,
        ...         carbohydrates_g=23.0,
        ...         fat_g=0.3,
        ...     ),
        ...     serving_size_g=120.0,
        ... )
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Banana",
                    "category": "fruit",
                    "nutritional_info": {
                        "calories": 89.0,
                        "protein_g": 1.1,
                        "carbohydrates_g": 23.0,
                        "fat_g": 0.3,
                        "fiber_g": 2.6,
                        "sugar_g": 12.2,
                        "sodium_mg": 1.0,
                    },
                    "serving_size_g": 120.0,
                    "description": "Fresh ripe banana",
                }
            ]
        }
    )

    name: str = Field(min_length=1, description="Name of the food item")
    category: FoodCategory = Field(description="Category of the food item")
    nutritional_info: NutritionalInfo = Field(description="Nutritional info per 100g")
    serving_size_g: Optional[float] = Field(
        default=None, gt=0, description="Typical serving size in grams"
    )
    description: Optional[str] = Field(default=None, description="Description of the food item")
    brand: Optional[str] = Field(default=None, description="Brand name, if applicable")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Name cannot be empty or just whitespace")
        return stripped

    def nutrition_for_serving(self) -> Optional[NutritionalInfo]:
        """
        Return nutritional info scaled to the default serving size.

        Returns:
            Scaled NutritionalInfo if serving_size_g is set, else None.
        """
        if self.serving_size_g is None:
            return None
        return self.nutritional_info.scale_to_grams(self.serving_size_g)

    def nutrition_for_grams(self, grams: float) -> NutritionalInfo:
        """
        Return nutritional info scaled to a custom amount in grams.

        Args:
            grams: Amount in grams.

        Returns:
            Scaled NutritionalInfo.
        """
        return self.nutritional_info.scale_to_grams(grams)
