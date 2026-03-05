"""Repositories for FoodItem and FoodRecipe data models."""

import json
from typing import Optional

from nira_backend.data_models.food_item import FoodCategory, FoodItem, NutritionalInfo
from nira_backend.data_models.food_recipe import FoodRecipe, RecipeIngredient
from nira_backend.database.repositories.base_repository import BaseRepository


class FoodItemRepository(BaseRepository[FoodItem]):
    """CRUD operations for :class:`~nira_backend.data_models.food_item.FoodItem` records."""

    _TABLE = "food_items"

    def create(self, model: FoodItem) -> int:
        with self._db.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO food_items
                    (name, category, calories, protein_g, carbohydrates_g, fat_g,
                     fiber_g, sugar_g, sodium_mg, serving_size_g, description, brand)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    model.name,
                    model.category.value,
                    model.nutritional_info.calories,
                    model.nutritional_info.protein_g,
                    model.nutritional_info.carbohydrates_g,
                    model.nutritional_info.fat_g,
                    model.nutritional_info.fiber_g,
                    model.nutritional_info.sugar_g,
                    model.nutritional_info.sodium_mg,
                    model.serving_size_g,
                    model.description,
                    model.brand,
                ),
            )
            return cursor.lastrowid  # type: ignore[return-value]

    def get_by_id(self, record_id: int) -> Optional[FoodItem]:
        with self._db.get_cursor() as cursor:
            cursor.execute("SELECT * FROM food_items WHERE id = ?", (record_id,))
            row = cursor.fetchone()
        return self._row_to_model(row) if row else None

    def get_all(self) -> list[FoodItem]:
        with self._db.get_cursor() as cursor:
            cursor.execute("SELECT * FROM food_items ORDER BY name")
            rows = cursor.fetchall()
        return [self._row_to_model(row) for row in rows]

    def get_by_category(self, category: FoodCategory) -> list[FoodItem]:
        """Return all food items belonging to a given category."""
        with self._db.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM food_items WHERE category = ? ORDER BY name",
                (category.value,),
            )
            rows = cursor.fetchall()
        return [self._row_to_model(row) for row in rows]

    def search_by_name(self, name: str) -> list[FoodItem]:
        """Search food items by name (case-insensitive substring match)."""
        with self._db.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM food_items WHERE name LIKE ? ORDER BY name",
                (f"%{name}%",),
            )
            rows = cursor.fetchall()
        return [self._row_to_model(row) for row in rows]

    def update(self, record_id: int, model: FoodItem) -> bool:
        with self._db.get_cursor() as cursor:
            if not self._row_exists(cursor, self._TABLE, record_id):
                return False
            cursor.execute(
                """
                UPDATE food_items
                SET name = ?, category = ?, calories = ?, protein_g = ?,
                    carbohydrates_g = ?, fat_g = ?, fiber_g = ?, sugar_g = ?,
                    sodium_mg = ?, serving_size_g = ?, description = ?, brand = ?,
                    updated_at = datetime('now')
                WHERE id = ?
                """,
                (
                    model.name,
                    model.category.value,
                    model.nutritional_info.calories,
                    model.nutritional_info.protein_g,
                    model.nutritional_info.carbohydrates_g,
                    model.nutritional_info.fat_g,
                    model.nutritional_info.fiber_g,
                    model.nutritional_info.sugar_g,
                    model.nutritional_info.sodium_mg,
                    model.serving_size_g,
                    model.description,
                    model.brand,
                    record_id,
                ),
            )
            return True

    def delete(self, record_id: int) -> bool:
        with self._db.get_cursor() as cursor:
            if not self._row_exists(cursor, self._TABLE, record_id):
                return False
            cursor.execute("DELETE FROM food_items WHERE id = ?", (record_id,))
            return True

    @staticmethod
    def _row_to_model(row: object) -> FoodItem:
        nutritional_info = NutritionalInfo(
            calories=row["calories"],  # type: ignore[index]
            protein_g=row["protein_g"],  # type: ignore[index]
            carbohydrates_g=row["carbohydrates_g"],  # type: ignore[index]
            fat_g=row["fat_g"],  # type: ignore[index]
            fiber_g=row["fiber_g"],  # type: ignore[index]
            sugar_g=row["sugar_g"],  # type: ignore[index]
            sodium_mg=row["sodium_mg"],  # type: ignore[index]
        )
        return FoodItem(
            name=row["name"],  # type: ignore[index]
            category=FoodCategory(row["category"]),  # type: ignore[index]
            nutritional_info=nutritional_info,
            serving_size_g=row["serving_size_g"],  # type: ignore[index]
            description=row["description"],  # type: ignore[index]
            brand=row["brand"],  # type: ignore[index]
        )


class FoodRecipeRepository(BaseRepository[FoodRecipe]):
    """CRUD operations for :class:`~nira_backend.data_models.food_recipe.FoodRecipe` records."""

    _TABLE = "food_recipes"

    def __init__(self, connection: object, food_item_repo: FoodItemRepository) -> None:
        super().__init__(connection)
        self._food_item_repo = food_item_repo

    def create(self, model: FoodRecipe) -> int:
        food_ids = [
            self._food_item_repo.create(ingredient.food_item)
            for ingredient in model.ingredients
        ]

        with self._db.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO food_recipes
                    (name, description, servings, prep_time_minutes, cook_time_minutes,
                     instructions, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    model.name,
                    model.description,
                    model.servings,
                    model.prep_time_minutes,
                    model.cook_time_minutes,
                    json.dumps(model.instructions),
                    json.dumps(model.tags),
                ),
            )
            recipe_id: int = cursor.lastrowid  # type: ignore[assignment]

            for ingredient, food_id in zip(model.ingredients, food_ids):
                cursor.execute(
                    """
                    INSERT INTO food_recipe_ingredients
                        (recipe_id, food_item_id, quantity_g, notes)
                    VALUES (?, ?, ?, ?)
                    """,
                    (recipe_id, food_id, ingredient.quantity_g, ingredient.notes),
                )

        return recipe_id

    def get_by_id(self, record_id: int) -> Optional[FoodRecipe]:
        with self._db.get_cursor() as cursor:
            cursor.execute("SELECT * FROM food_recipes WHERE id = ?", (record_id,))
            row = cursor.fetchone()
            if not row:
                return None
            ingredients = self._fetch_ingredients(cursor, record_id)
        return self._row_to_model(row, ingredients)

    def get_all(self) -> list[FoodRecipe]:
        with self._db.get_cursor() as cursor:
            cursor.execute("SELECT * FROM food_recipes ORDER BY name")
            rows = cursor.fetchall()
            result = []
            for row in rows:
                ingredients = self._fetch_ingredients(cursor, row["id"])
                result.append(self._row_to_model(row, ingredients))
        return result

    def search_by_name(self, name: str) -> list[FoodRecipe]:
        """Search recipes by name (case-insensitive substring match)."""
        with self._db.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM food_recipes WHERE name LIKE ? ORDER BY name",
                (f"%{name}%",),
            )
            rows = cursor.fetchall()
            result = []
            for row in rows:
                ingredients = self._fetch_ingredients(cursor, row["id"])
                result.append(self._row_to_model(row, ingredients))
        return result

    def update(self, record_id: int, model: FoodRecipe) -> bool:
        food_ids = [
            self._food_item_repo.create(ingredient.food_item)
            for ingredient in model.ingredients
        ]

        with self._db.get_cursor() as cursor:
            if not self._row_exists(cursor, self._TABLE, record_id):
                return False
            cursor.execute(
                """
                UPDATE food_recipes
                SET name = ?, description = ?, servings = ?, prep_time_minutes = ?,
                    cook_time_minutes = ?, instructions = ?, tags = ?,
                    updated_at = datetime('now')
                WHERE id = ?
                """,
                (
                    model.name,
                    model.description,
                    model.servings,
                    model.prep_time_minutes,
                    model.cook_time_minutes,
                    json.dumps(model.instructions),
                    json.dumps(model.tags),
                    record_id,
                ),
            )
            cursor.execute(
                "DELETE FROM food_recipe_ingredients WHERE recipe_id = ?",
                (record_id,),
            )
            for ingredient, food_id in zip(model.ingredients, food_ids):
                cursor.execute(
                    """
                    INSERT INTO food_recipe_ingredients
                        (recipe_id, food_item_id, quantity_g, notes)
                    VALUES (?, ?, ?, ?)
                    """,
                    (record_id, food_id, ingredient.quantity_g, ingredient.notes),
                )
        return True

    def delete(self, record_id: int) -> bool:
        with self._db.get_cursor() as cursor:
            if not self._row_exists(cursor, self._TABLE, record_id):
                return False
            cursor.execute("DELETE FROM food_recipes WHERE id = ?", (record_id,))
            return True

    def _fetch_ingredients(
        self, cursor: object, recipe_id: int
    ) -> list[RecipeIngredient]:
        import sqlite3

        assert isinstance(cursor, sqlite3.Cursor)
        cursor.execute(
            """
            SELECT fri.quantity_g, fri.notes, fi.*
            FROM food_recipe_ingredients fri
            JOIN food_items fi ON fri.food_item_id = fi.id
            WHERE fri.recipe_id = ?
            """,
            (recipe_id,),
        )
        rows = cursor.fetchall()
        return [
            RecipeIngredient(
                food_item=FoodItemRepository._row_to_model(row),
                quantity_g=row["quantity_g"],
                notes=row["notes"],
            )
            for row in rows
        ]

    @staticmethod
    def _row_to_model(row: object, ingredients: list[RecipeIngredient]) -> FoodRecipe:
        return FoodRecipe(
            name=row["name"],  # type: ignore[index]
            description=row["description"],  # type: ignore[index]
            servings=row["servings"],  # type: ignore[index]
            prep_time_minutes=row["prep_time_minutes"],  # type: ignore[index]
            cook_time_minutes=row["cook_time_minutes"],  # type: ignore[index]
            instructions=json.loads(row["instructions"]),  # type: ignore[index]
            tags=json.loads(row["tags"]),  # type: ignore[index]
            ingredients=ingredients,
        )
