"""Tests for FoodItemRepository and FoodRecipeRepository."""

import pytest
from pathlib import Path

from nira_backend.data_models.food_item import FoodCategory, FoodItem, NutritionalInfo
from nira_backend.data_models.food_recipe import FoodRecipe, RecipeIngredient
from nira_backend.database.connection import DatabaseConnection
from nira_backend.database.repositories.food_repository import (
    FoodItemRepository,
    FoodRecipeRepository,
)


@pytest.fixture
def db(tmp_path: Path) -> DatabaseConnection:
    return DatabaseConnection(db_path=tmp_path / "test.db")


@pytest.fixture
def item_repo(db: DatabaseConnection) -> FoodItemRepository:
    return FoodItemRepository(db)


@pytest.fixture
def recipe_repo(db: DatabaseConnection, item_repo: FoodItemRepository) -> FoodRecipeRepository:
    return FoodRecipeRepository(db, item_repo)


@pytest.fixture
def banana() -> FoodItem:
    return FoodItem(
        name="Banana",
        category=FoodCategory.FRUIT,
        nutritional_info=NutritionalInfo(
            calories=89.0,
            protein_g=1.1,
            carbohydrates_g=23.0,
            fat_g=0.3,
            fiber_g=2.6,
            sugar_g=12.2,
            sodium_mg=1.0,
        ),
        serving_size_g=120.0,
        description="Fresh banana",
    )


@pytest.fixture
def oats() -> FoodItem:
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


class TestFoodItemRepository:
    def test_create_returns_id(self, item_repo: FoodItemRepository, banana: FoodItem) -> None:
        fid = item_repo.create(banana)
        assert isinstance(fid, int)

    def test_get_by_id(self, item_repo: FoodItemRepository, banana: FoodItem) -> None:
        fid = item_repo.create(banana)
        retrieved = item_repo.get_by_id(fid)
        assert retrieved is not None
        assert retrieved.name == "Banana"
        assert retrieved.category == FoodCategory.FRUIT
        assert retrieved.nutritional_info.calories == 89.0

    def test_get_by_id_not_found(self, item_repo: FoodItemRepository) -> None:
        assert item_repo.get_by_id(9999) is None

    def test_get_all_empty(self, item_repo: FoodItemRepository) -> None:
        assert item_repo.get_all() == []

    def test_get_all_multiple(
        self, item_repo: FoodItemRepository, banana: FoodItem, oats: FoodItem
    ) -> None:
        item_repo.create(banana)
        item_repo.create(oats)
        all_items = item_repo.get_all()
        assert len(all_items) == 2

    def test_get_by_category(
        self, item_repo: FoodItemRepository, banana: FoodItem, oats: FoodItem
    ) -> None:
        item_repo.create(banana)
        item_repo.create(oats)
        fruits = item_repo.get_by_category(FoodCategory.FRUIT)
        assert len(fruits) == 1
        assert fruits[0].name == "Banana"

    def test_search_by_name(
        self, item_repo: FoodItemRepository, banana: FoodItem, oats: FoodItem
    ) -> None:
        item_repo.create(banana)
        item_repo.create(oats)
        results = item_repo.search_by_name("ban")
        assert len(results) == 1
        assert results[0].name == "Banana"

    def test_update(self, item_repo: FoodItemRepository, banana: FoodItem) -> None:
        fid = item_repo.create(banana)
        updated = FoodItem(
            name="Ripe Banana",
            category=FoodCategory.FRUIT,
            nutritional_info=banana.nutritional_info,
        )
        assert item_repo.update(fid, updated) is True
        retrieved = item_repo.get_by_id(fid)
        assert retrieved is not None
        assert retrieved.name == "Ripe Banana"

    def test_update_not_found(self, item_repo: FoodItemRepository, banana: FoodItem) -> None:
        assert item_repo.update(9999, banana) is False

    def test_delete(self, item_repo: FoodItemRepository, banana: FoodItem) -> None:
        fid = item_repo.create(banana)
        assert item_repo.delete(fid) is True
        assert item_repo.get_by_id(fid) is None

    def test_delete_not_found(self, item_repo: FoodItemRepository) -> None:
        assert item_repo.delete(9999) is False

    def test_optional_fields_roundtrip(
        self, item_repo: FoodItemRepository, banana: FoodItem
    ) -> None:
        fid = item_repo.create(banana)
        retrieved = item_repo.get_by_id(fid)
        assert retrieved is not None
        assert retrieved.description == "Fresh banana"
        assert retrieved.serving_size_g == 120.0


class TestFoodRecipeRepository:
    def test_create_and_get(
        self,
        recipe_repo: FoodRecipeRepository,
        banana: FoodItem,
        oats: FoodItem,
    ) -> None:
        recipe = FoodRecipe(
            name="Banana Oat Bowl",
            ingredients=[
                RecipeIngredient(food_item=banana, quantity_g=100.0),
                RecipeIngredient(food_item=oats, quantity_g=80.0),
            ],
            instructions=["Slice banana", "Mix with oats"],
            servings=1,
            tags=["healthy"],
        )
        rid = recipe_repo.create(recipe)
        retrieved = recipe_repo.get_by_id(rid)
        assert retrieved is not None
        assert retrieved.name == "Banana Oat Bowl"
        assert len(retrieved.ingredients) == 2
        assert retrieved.tags == ["healthy"]
        assert retrieved.instructions == ["Slice banana", "Mix with oats"]

    def test_get_by_id_not_found(self, recipe_repo: FoodRecipeRepository) -> None:
        assert recipe_repo.get_by_id(9999) is None

    def test_get_all_empty(self, recipe_repo: FoodRecipeRepository) -> None:
        assert recipe_repo.get_all() == []

    def test_search_by_name(
        self, recipe_repo: FoodRecipeRepository, banana: FoodItem
    ) -> None:
        recipe_repo.create(FoodRecipe(name="Banana Smoothie"))
        recipe_repo.create(FoodRecipe(name="Oat Porridge"))
        results = recipe_repo.search_by_name("banana")
        assert len(results) == 1
        assert results[0].name == "Banana Smoothie"

    def test_delete(self, recipe_repo: FoodRecipeRepository) -> None:
        rid = recipe_repo.create(FoodRecipe(name="Temp Recipe"))
        assert recipe_repo.delete(rid) is True
        assert recipe_repo.get_by_id(rid) is None

    def test_delete_not_found(self, recipe_repo: FoodRecipeRepository) -> None:
        assert recipe_repo.delete(9999) is False
