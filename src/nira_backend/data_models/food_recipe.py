"""Food recipe data model."""

from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict

from nira_backend.data_models.food_item import FoodItem, NutritionalInfo


class RecipeIngredient(BaseModel):
    """
    Represents one ingredient in a recipe: a food item with its quantity.

    Attributes:
        food_item: The food item used.
        quantity_g: Amount used in grams.
        notes: Optional preparation note (e.g. "diced", "peeled").
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "food_item": {"name": "Banana", "category": "fruit"},
                    "quantity_g": 120.0,
                    "notes": "sliced",
                }
            ]
        }
    )

    food_item: FoodItem = Field(description="The food item used in the recipe")
    quantity_g: float = Field(gt=0, description="Amount of the food item in grams")
    notes: Optional[str] = Field(
        default=None, description="Optional preparation note, e.g. 'diced', 'peeled'"
    )

    def nutritional_contribution(self) -> NutritionalInfo:
        """
        Calculate the nutritional contribution of this ingredient at its quantity.

        Returns:
            NutritionalInfo scaled to quantity_g.
        """
        return self.food_item.nutrition_for_grams(self.quantity_g)


class FoodRecipe(BaseModel):
    """
    Represents a food recipe composed of multiple ingredients.

    Attributes:
        name: Name of the recipe.
        description: Short description of the recipe.
        ingredients: List of recipe ingredients.
        instructions: Ordered list of preparation steps.
        servings: Number of servings the recipe yields.
        prep_time_minutes: Preparation time in minutes.
        cook_time_minutes: Cooking time in minutes.
        tags: Optional list of tags (e.g. "vegan", "gluten-free").

    Example:
        >>> recipe = FoodRecipe(
        ...     name="Banana Smoothie",
        ...     ingredients=[...],
        ...     instructions=["Peel bananas", "Blend all ingredients"],
        ...     servings=2,
        ... )
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Banana Smoothie",
                    "description": "A simple banana smoothie.",
                    "ingredients": [],
                    "instructions": ["Peel bananas", "Blend all ingredients"],
                    "servings": 2,
                    "prep_time_minutes": 5,
                    "cook_time_minutes": 0,
                    "tags": ["vegan", "quick"],
                }
            ]
        }
    )

    name: str = Field(min_length=1, description="Name of the recipe")
    description: Optional[str] = Field(default=None, description="Short description of the recipe")
    ingredients: list[RecipeIngredient] = Field(
        default_factory=list, description="List of recipe ingredients"
    )
    instructions: list[str] = Field(
        default_factory=list, description="Ordered list of preparation steps"
    )
    servings: int = Field(ge=1, default=1, description="Number of servings the recipe yields")
    prep_time_minutes: Optional[int] = Field(
        default=None, ge=0, description="Preparation time in minutes"
    )
    cook_time_minutes: Optional[int] = Field(
        default=None, ge=0, description="Cooking time in minutes"
    )
    tags: list[str] = Field(default_factory=list, description="Tags such as 'vegan', 'gluten-free'")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Recipe name cannot be empty or just whitespace")
        return stripped

    @field_validator("instructions")
    @classmethod
    def validate_instructions(cls, steps: list[str]) -> list[str]:
        return [step.strip() for step in steps if step.strip()]

    @property
    def total_time_minutes(self) -> Optional[int]:
        """Total time (prep + cook) in minutes, or None if neither is set."""
        if self.prep_time_minutes is None and self.cook_time_minutes is None:
            return None
        return (self.prep_time_minutes or 0) + (self.cook_time_minutes or 0)

    def total_nutritional_info(self) -> NutritionalInfo:
        """
        Sum the nutritional contributions of all ingredients for the whole recipe.

        Returns:
            NutritionalInfo representing the full recipe (all servings).
        """
        total_calories = 0.0
        total_protein = 0.0
        total_carbs = 0.0
        total_fat = 0.0
        total_fiber = 0.0
        total_sugar = 0.0
        total_sodium = 0.0

        for ingredient in self.ingredients:
            contrib = ingredient.nutritional_contribution()
            total_calories += contrib.calories
            total_protein += contrib.protein_g
            total_carbs += contrib.carbohydrates_g
            total_fat += contrib.fat_g
            total_fiber += contrib.fiber_g
            total_sugar += contrib.sugar_g
            total_sodium += contrib.sodium_mg

        return NutritionalInfo(
            calories=round(total_calories, 2),
            protein_g=round(total_protein, 2),
            carbohydrates_g=round(total_carbs, 2),
            fat_g=round(total_fat, 2),
            fiber_g=round(total_fiber, 2),
            sugar_g=round(total_sugar, 2),
            sodium_mg=round(total_sodium, 2),
        )

    def nutritional_info_per_serving(self) -> NutritionalInfo:
        """
        Nutritional info scaled to a single serving.

        Returns:
            NutritionalInfo per serving.
        """
        total = self.total_nutritional_info()
        factor = 1.0 / self.servings
        return NutritionalInfo(
            calories=round(total.calories * factor, 2),
            protein_g=round(total.protein_g * factor, 2),
            carbohydrates_g=round(total.carbohydrates_g * factor, 2),
            fat_g=round(total.fat_g * factor, 2),
            fiber_g=round(total.fiber_g * factor, 2),
            sugar_g=round(total.sugar_g * factor, 2),
            sodium_mg=round(total.sodium_mg * factor, 2),
        )
