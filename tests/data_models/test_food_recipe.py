"""Tests for FoodRecipe and RecipeIngredient data models."""

import pytest
from pydantic import ValidationError

from nira_backend.data_models.food_item import FoodCategory, FoodItem, NutritionalInfo
from nira_backend.data_models.food_recipe import FoodRecipe, RecipeIngredient


@pytest.fixture
def apple_item() -> FoodItem:
    return FoodItem(
        name="Apple",
        category=FoodCategory.FRUIT,
        nutritional_info=NutritionalInfo(
            calories=52.0,
            protein_g=0.3,
            carbohydrates_g=14.0,
            fat_g=0.2,
            fiber_g=2.4,
            sugar_g=10.0,
            sodium_mg=1.0,
        ),
    )


@pytest.fixture
def oat_item() -> FoodItem:
    return FoodItem(
        name="Oats",
        category=FoodCategory.GRAIN,
        nutritional_info=NutritionalInfo(
            calories=389.0,
            protein_g=17.0,
            carbohydrates_g=66.0,
            fat_g=7.0,
        ),
    )


@pytest.fixture
def apple_ingredient(apple_item: FoodItem) -> RecipeIngredient:
    return RecipeIngredient(food_item=apple_item, quantity_g=150.0, notes="sliced")


@pytest.fixture
def oat_ingredient(oat_item: FoodItem) -> RecipeIngredient:
    return RecipeIngredient(food_item=oat_item, quantity_g=80.0)


@pytest.fixture
def simple_recipe(
    apple_ingredient: RecipeIngredient, oat_ingredient: RecipeIngredient
) -> FoodRecipe:
    return FoodRecipe(
        name="Apple Oat Bowl",
        description="A healthy breakfast.",
        ingredients=[apple_ingredient, oat_ingredient],
        instructions=["Slice apple", "Mix with oats", "Serve"],
        servings=2,
        prep_time_minutes=5,
        cook_time_minutes=10,
        tags=["healthy", "breakfast"],
    )


class TestRecipeIngredient:
    def test_create_valid(self, apple_ingredient: RecipeIngredient) -> None:
        assert apple_ingredient.quantity_g == 150.0
        assert apple_ingredient.notes == "sliced"

    def test_zero_quantity_raises(self, apple_item: FoodItem) -> None:
        with pytest.raises(ValidationError):
            RecipeIngredient(food_item=apple_item, quantity_g=0.0)

    def test_negative_quantity_raises(self, apple_item: FoodItem) -> None:
        with pytest.raises(ValidationError):
            RecipeIngredient(food_item=apple_item, quantity_g=-10.0)

    def test_nutritional_contribution(self, apple_ingredient: RecipeIngredient) -> None:
        contrib = apple_ingredient.nutritional_contribution()
        assert contrib.calories == round(52.0 * 1.5, 2)


class TestFoodRecipe:
    def test_create_valid(self, simple_recipe: FoodRecipe) -> None:
        assert simple_recipe.name == "Apple Oat Bowl"
        assert simple_recipe.servings == 2

    def test_name_stripped(self) -> None:
        recipe = FoodRecipe(name="  Salad  ")
        assert recipe.name == "Salad"

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValidationError):
            FoodRecipe(name="")

    def test_whitespace_name_raises(self) -> None:
        with pytest.raises(ValidationError):
            FoodRecipe(name="   ")

    def test_zero_servings_raises(self) -> None:
        with pytest.raises(ValidationError):
            FoodRecipe(name="Test", servings=0)

    def test_total_time_minutes(self, simple_recipe: FoodRecipe) -> None:
        assert simple_recipe.total_time_minutes == 15

    def test_total_time_minutes_none_when_both_unset(self) -> None:
        recipe = FoodRecipe(name="X")
        assert recipe.total_time_minutes is None

    def test_total_nutritional_info(
        self, simple_recipe: FoodRecipe, apple_ingredient: RecipeIngredient, oat_ingredient: RecipeIngredient
    ) -> None:
        total = simple_recipe.total_nutritional_info()
        expected_calories = (
            apple_ingredient.nutritional_contribution().calories
            + oat_ingredient.nutritional_contribution().calories
        )
        assert abs(total.calories - expected_calories) < 0.01

    def test_nutritional_info_per_serving(self, simple_recipe: FoodRecipe) -> None:
        total = simple_recipe.total_nutritional_info()
        per_serving = simple_recipe.nutritional_info_per_serving()
        assert abs(per_serving.calories - total.calories / 2) < 0.01

    def test_instructions_whitespace_stripped(self) -> None:
        recipe = FoodRecipe(name="X", instructions=["  Step 1  ", "  ", "Step 2"])
        assert recipe.instructions == ["Step 1", "Step 2"]

    def test_empty_recipe_totals_zero(self) -> None:
        recipe = FoodRecipe(name="Empty")
        total = recipe.total_nutritional_info()
        assert total.calories == 0.0

    def test_default_fields(self) -> None:
        recipe = FoodRecipe(name="Minimal")
        assert recipe.description is None
        assert recipe.ingredients == []
        assert recipe.instructions == []
        assert recipe.tags == []
        assert recipe.prep_time_minutes is None
        assert recipe.cook_time_minutes is None
