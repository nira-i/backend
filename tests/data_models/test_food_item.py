"""Tests for FoodItem and NutritionalInfo data models."""

import pytest
from pydantic import ValidationError

from nira_backend.data_models.food_item import FoodCategory, FoodItem, NutritionalInfo


@pytest.fixture
def base_nutrition() -> NutritionalInfo:
    return NutritionalInfo(
        calories=89.0,
        protein_g=1.1,
        carbohydrates_g=23.0,
        fat_g=0.3,
        fiber_g=2.6,
        sugar_g=12.2,
        sodium_mg=1.0,
    )


@pytest.fixture
def banana(base_nutrition: NutritionalInfo) -> FoodItem:
    return FoodItem(
        name="Banana",
        category=FoodCategory.FRUIT,
        nutritional_info=base_nutrition,
        serving_size_g=120.0,
    )


class TestNutritionalInfo:
    def test_create_valid(self, base_nutrition: NutritionalInfo) -> None:
        assert base_nutrition.calories == 89.0
        assert base_nutrition.protein_g == 1.1

    def test_negative_calories_raises(self) -> None:
        with pytest.raises(ValidationError):
            NutritionalInfo(calories=-1, protein_g=1, carbohydrates_g=1, fat_g=1)

    def test_negative_protein_raises(self) -> None:
        with pytest.raises(ValidationError):
            NutritionalInfo(calories=100, protein_g=-1, carbohydrates_g=1, fat_g=1)

    def test_scale_to_grams_half(self, base_nutrition: NutritionalInfo) -> None:
        scaled = base_nutrition.scale_to_grams(50.0)
        assert scaled.calories == round(89.0 * 0.5, 2)
        assert scaled.protein_g == round(1.1 * 0.5, 2)

    def test_scale_to_grams_double(self, base_nutrition: NutritionalInfo) -> None:
        scaled = base_nutrition.scale_to_grams(200.0)
        assert scaled.calories == round(89.0 * 2.0, 2)

    def test_scale_to_zero_grams(self, base_nutrition: NutritionalInfo) -> None:
        scaled = base_nutrition.scale_to_grams(0.0)
        assert scaled.calories == 0.0

    def test_scale_to_negative_grams_raises(self, base_nutrition: NutritionalInfo) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            base_nutrition.scale_to_grams(-10.0)

    def test_default_fiber_sugar_sodium(self) -> None:
        n = NutritionalInfo(calories=100, protein_g=5, carbohydrates_g=10, fat_g=2)
        assert n.fiber_g == 0.0
        assert n.sugar_g == 0.0
        assert n.sodium_mg == 0.0


class TestFoodItem:
    def test_create_valid(self, banana: FoodItem) -> None:
        assert banana.name == "Banana"
        assert banana.category == FoodCategory.FRUIT
        assert banana.serving_size_g == 120.0

    def test_name_stripped(self, base_nutrition: NutritionalInfo) -> None:
        item = FoodItem(name="  Apple  ", category=FoodCategory.FRUIT, nutritional_info=base_nutrition)
        assert item.name == "Apple"

    def test_empty_name_raises(self, base_nutrition: NutritionalInfo) -> None:
        with pytest.raises(ValidationError):
            FoodItem(name="", category=FoodCategory.FRUIT, nutritional_info=base_nutrition)

    def test_whitespace_name_raises(self, base_nutrition: NutritionalInfo) -> None:
        with pytest.raises(ValidationError):
            FoodItem(name="   ", category=FoodCategory.FRUIT, nutritional_info=base_nutrition)

    def test_invalid_category_raises(self, base_nutrition: NutritionalInfo) -> None:
        with pytest.raises(ValidationError):
            FoodItem(name="X", category="superfluous", nutritional_info=base_nutrition)  # type: ignore[arg-type]

    def test_nutrition_for_serving(self, banana: FoodItem) -> None:
        serving_info = banana.nutrition_for_serving()
        assert serving_info is not None
        assert serving_info.calories == round(89.0 * 1.2, 2)

    def test_nutrition_for_serving_none_when_no_serving_size(
        self, base_nutrition: NutritionalInfo
    ) -> None:
        item = FoodItem(name="Test", category=FoodCategory.OTHER, nutritional_info=base_nutrition)
        assert item.nutrition_for_serving() is None

    def test_nutrition_for_grams(self, banana: FoodItem) -> None:
        info = banana.nutrition_for_grams(50.0)
        assert info.calories == round(89.0 * 0.5, 2)

    def test_optional_fields_default_to_none(self, base_nutrition: NutritionalInfo) -> None:
        item = FoodItem(name="Plain", category=FoodCategory.OTHER, nutritional_info=base_nutrition)
        assert item.description is None
        assert item.brand is None
        assert item.serving_size_g is None

    def test_all_categories_valid(self, base_nutrition: NutritionalInfo) -> None:
        for category in FoodCategory:
            item = FoodItem(name="X", category=category, nutritional_info=base_nutrition)
            assert item.category == category
