"""Structured data-entry tools for each domain.

Each factory returns a list of LangChain tools that write directly to the
central SQLite database.  These tools represent the *classical entry* path
(explicit field-by-field input), as opposed to the NL parsing path in
``parsing_tools.py``.
"""

from datetime import date

from langchain_core.tools import tool

from nira_backend.data_models.exercise import ExerciseEntry, MealLog
from nira_backend.data_models.food_item import FoodCategory, FoodItem, NutritionalInfo
from nira_backend.data_models.health_record import (
    BloodGlucoseRecord,
    BloodPressureRecord,
    HeartRateRecord,
    HealthRecord,
    SleepRecord,
)
from nira_backend.database.connection import DatabaseConnection
from nira_backend.database.repositories import (
    ExerciseRepository,
    FoodItemRepository,
    HealthRecordRepository,
    MealLogRepository,
)


# ---------------------------------------------------------------------------
# Health entry tools
# ---------------------------------------------------------------------------


def make_health_entry_tools(db: DatabaseConnection) -> list:
    """
    Return structured health-record entry tools.

    Args:
        db: Active database connection.

    Returns:
        List of LangChain tool callables.
    """
    health_repo = HealthRecordRepository(db)

    @tool
    def log_blood_pressure(
        human_name: str,
        systolic_mmhg: int,
        diastolic_mmhg: int,
        pulse_bpm: int = None,
        notes: str = None,
    ) -> str:
        """
        Log a blood pressure reading for a family member.

        Args:
            human_name: Full name of the person.
            systolic_mmhg: Systolic pressure (upper value) in mmHg.
            diastolic_mmhg: Diastolic pressure (lower value) in mmHg.
            pulse_bpm: Optional pulse rate in beats per minute.
            notes: Optional free-text notes.
        """
        record = HealthRecord(
            human_name=human_name,
            record_date=date.today(),
            record_type="blood_pressure",
            measurement=BloodPressureRecord(
                systolic_mmhg=systolic_mmhg,
                diastolic_mmhg=diastolic_mmhg,
                pulse_bpm=pulse_bpm,
            ),
            notes=notes,
        )
        rid = health_repo.create(record)
        bp = record.measurement
        assert isinstance(bp, BloodPressureRecord)
        return (
            f"Logged blood pressure for {human_name}: "
            f"{systolic_mmhg}/{diastolic_mmhg} mmHg "
            f"({bp.category}) [ID {rid}]"
        )

    @tool
    def log_blood_glucose(
        human_name: str,
        glucose_mmol_l: float,
        measurement_context: str = "random",
        notes: str = None,
    ) -> str:
        """
        Log a blood glucose reading for a family member.

        Args:
            human_name: Full name of the person.
            glucose_mmol_l: Blood glucose in mmol/L.
            measurement_context: One of 'fasting', 'post_meal_1h',
                                  'post_meal_2h', 'random'.
            notes: Optional free-text notes.
        """
        record = HealthRecord(
            human_name=human_name,
            record_date=date.today(),
            record_type="blood_glucose",
            measurement=BloodGlucoseRecord(
                glucose_mmol_l=glucose_mmol_l,
                measurement_context=measurement_context,  # type: ignore[arg-type]
            ),
            notes=notes,
        )
        rid = health_repo.create(record)
        g = record.measurement
        assert isinstance(g, BloodGlucoseRecord)
        return (
            f"Logged blood glucose for {human_name}: "
            f"{glucose_mmol_l} mmol/L ({g.glucose_mg_dl} mg/dL) "
            f"context={measurement_context} [ID {rid}]"
        )

    @tool
    def log_heart_rate(
        human_name: str,
        bpm: int,
        measurement_context: str = "resting",
        notes: str = None,
    ) -> str:
        """
        Log a heart rate reading for a family member.

        Args:
            human_name: Full name of the person.
            bpm: Heart rate in beats per minute.
            measurement_context: One of 'resting', 'active',
                                  'post_exercise', 'sleeping'.
            notes: Optional free-text notes.
        """
        record = HealthRecord(
            human_name=human_name,
            record_date=date.today(),
            record_type="heart_rate",
            measurement=HeartRateRecord(
                bpm=bpm,
                measurement_context=measurement_context,  # type: ignore[arg-type]
            ),
            notes=notes,
        )
        rid = health_repo.create(record)
        return (
            f"Logged heart rate for {human_name}: {bpm} bpm "
            f"(context={measurement_context}) [ID {rid}]"
        )

    @tool
    def log_sleep(
        human_name: str,
        duration_hours: float,
        quality: int,
        notes: str = None,
    ) -> str:
        """
        Log a sleep record for a family member.

        Args:
            human_name: Full name of the person.
            duration_hours: Total sleep duration in hours.
            quality: Quality rating from 1 (very poor) to 5 (excellent).
            notes: Optional free-text notes.
        """
        record = HealthRecord(
            human_name=human_name,
            record_date=date.today(),
            record_type="sleep",
            measurement=SleepRecord(
                duration_hours=duration_hours,
                quality=quality,
            ),
            notes=notes,
        )
        rid = health_repo.create(record)
        s = record.measurement
        assert isinstance(s, SleepRecord)
        return (
            f"Logged sleep for {human_name}: {duration_hours}h, "
            f"quality={quality}/5 ({s.quality_label}) [ID {rid}]"
        )

    return [log_blood_pressure, log_blood_glucose, log_heart_rate, log_sleep]


# ---------------------------------------------------------------------------
# Meal / food entry tools
# ---------------------------------------------------------------------------


def make_meal_entry_tools(db: DatabaseConnection) -> list:
    """
    Return structured meal and food-item entry tools.

    Args:
        db: Active database connection.

    Returns:
        List of LangChain tool callables.
    """
    meal_repo = MealLogRepository(db)
    food_repo = FoodItemRepository(db)

    @tool
    def log_meal(
        human_name: str,
        food_name: str,
        quantity_g: float,
        meal_type: str = "other",
        notes: str = None,
    ) -> str:
        """
        Log what a family member ate at a meal.

        Args:
            human_name: Full name of the person.
            food_name: Name of the food consumed.
            quantity_g: Amount eaten in grams.
            meal_type: One of 'breakfast', 'lunch', 'dinner', 'snack', 'other'.
            notes: Optional free-text notes.
        """
        entry = MealLog(
            human_name=human_name,
            food_name=food_name,
            quantity_g=quantity_g,
            meal_type=meal_type,  # type: ignore[arg-type]
            log_date=date.today(),
            notes=notes,
        )
        mid = meal_repo.create(entry)
        return (
            f"Logged meal for {human_name}: {quantity_g}g of {food_name} "
            f"({meal_type}) [ID {mid}]"
        )

    @tool
    def add_food_item(
        name: str,
        category: str,
        calories: float,
        protein_g: float,
        carbohydrates_g: float,
        fat_g: float,
        fiber_g: float = 0.0,
        sugar_g: float = 0.0,
        sodium_mg: float = 0.0,
        serving_size_g: float = None,
        description: str = None,
    ) -> str:
        """
        Add a new food item to the food catalog (nutritional values are per 100g).

        Args:
            name: Name of the food item.
            category: One of fruit, vegetable, grain, protein, dairy, fat,
                      beverage, snack, condiment, other.
            calories: Calories per 100g.
            protein_g: Protein in grams per 100g.
            carbohydrates_g: Carbohydrates in grams per 100g.
            fat_g: Fat in grams per 100g.
            fiber_g: Dietary fiber in grams per 100g.
            sugar_g: Sugar in grams per 100g.
            sodium_mg: Sodium in milligrams per 100g.
            serving_size_g: Typical serving size in grams (optional).
            description: Optional description.
        """
        food = FoodItem(
            name=name,
            category=FoodCategory(category),
            nutritional_info=NutritionalInfo(
                calories=calories,
                protein_g=protein_g,
                carbohydrates_g=carbohydrates_g,
                fat_g=fat_g,
                fiber_g=fiber_g,
                sugar_g=sugar_g,
                sodium_mg=sodium_mg,
            ),
            serving_size_g=serving_size_g,
            description=description,
        )
        fid = food_repo.create(food)
        return f"Added food item '{name}' to catalog [ID {fid}]"

    @tool
    def search_food_catalog(query: str) -> str:
        """
        Search the food catalog by name.

        Args:
            query: Partial name to search for.
        """
        items = food_repo.search_by_name(query)
        if not items:
            return f"No food items found matching '{query}'."
        lines = [
            f"- {item.name} ({item.category.value}): "
            f"{item.nutritional_info.calories} kcal, "
            f"{item.nutritional_info.protein_g}g protein per 100g"
            for item in items[:10]
        ]
        return f"Food catalog results for '{query}':\n" + "\n".join(lines)

    return [log_meal, add_food_item, search_food_catalog]


# ---------------------------------------------------------------------------
# Exercise entry tools
# ---------------------------------------------------------------------------


def make_exercise_entry_tools(db: DatabaseConnection) -> list:
    """
    Return structured exercise entry tools.

    Args:
        db: Active database connection.

    Returns:
        List of LangChain tool callables.
    """
    exercise_repo = ExerciseRepository(db)

    @tool
    def log_exercise(
        human_name: str,
        activity: str,
        duration_minutes: int,
        intensity: str = "moderate",
        calories_burned: float = None,
        distance_km: float = None,
        notes: str = None,
    ) -> str:
        """
        Log an exercise session for a family member.

        Args:
            human_name: Full name of the person.
            activity: Activity name, e.g. 'running', 'yoga', 'cycling'.
            duration_minutes: Duration of the session in minutes.
            intensity: One of 'light', 'moderate', 'vigorous'.
            calories_burned: Estimated calories burned (optional).
            distance_km: Distance covered in kilometres (optional).
            notes: Optional free-text notes.
        """
        entry = ExerciseEntry(
            human_name=human_name,
            exercise_date=date.today(),
            activity=activity,
            duration_minutes=duration_minutes,
            intensity=intensity,  # type: ignore[arg-type]
            calories_burned=calories_burned,
            distance_km=distance_km,
            notes=notes,
        )
        eid = exercise_repo.create(entry)
        return (
            f"Logged {activity} for {human_name}: {duration_minutes} min "
            f"({intensity})"
            f"{f', {distance_km} km' if distance_km else ''}"
            f"{f', ~{calories_burned} kcal' if calories_burned else ''}"
            f" [ID {eid}]"
        )

    return [log_exercise]
