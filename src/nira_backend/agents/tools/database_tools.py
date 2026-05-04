"""Read-only database query tools shared across agents."""

from datetime import date

from langchain_core.tools import tool

from nira_backend.database.connection import DatabaseConnection
from nira_backend.database.repositories import (
    ExerciseRepository,
    HealthRecordRepository,
    HumanRepository,
    MealLogRepository,
)


def make_shared_db_tools(db: DatabaseConnection) -> list:
    """
    Return read-only query tools for the central database.

    These tools let any agent look up family members and their history
    without modifying data.

    Args:
        db: Active database connection.

    Returns:
        List of LangChain tool callables.
    """
    human_repo = HumanRepository(db)
    health_repo = HealthRecordRepository(db)
    meal_repo = MealLogRepository(db)
    exercise_repo = ExerciseRepository(db)

    @tool
    def list_family_members() -> str:
        """List all family members registered in the system with their basic details."""
        humans = human_repo.get_all()
        if not humans:
            return "No family members registered yet."
        lines = [
            f"- {h.name} ({h.gender}, age {h.get_age()}, "
            f"BMI {h.bmi} – {h.bmi_category})"
            for h in humans
        ]
        return "Family members:\n" + "\n".join(lines)

    @tool
    def get_health_history(human_name: str, record_type: str = "all", days: int = 30) -> str:
        """
        Retrieve recent health records for a family member.

        Args:
            human_name: Name of the person (partial match supported).
            record_type: One of 'blood_pressure', 'blood_glucose', 'heart_rate',
                         'sleep', or 'all'.
            days: How many days back to look (default 30).
        """
        end_date = date.today()
        from datetime import timedelta
        start_date = end_date - timedelta(days=days)

        if record_type == "all":
            records = health_repo.get_by_date_range(start_date, end_date)
            records = [r for r in records if human_name.lower() in r.human_name.lower()]
        else:
            records = health_repo.get_by_human_name(human_name)
            records = [r for r in records if r.record_type == record_type]

        if not records:
            return f"No {record_type} records found for '{human_name}' in the last {days} days."

        lines = [
            f"[{r.record_date}] {r.record_type}: {r.measurement.model_dump_json()} "
            f"{'| ' + r.notes if r.notes else ''}"
            for r in records[:20]
        ]
        return f"Health records for {human_name} (last {days} days):\n" + "\n".join(lines)

    @tool
    def get_meal_history(human_name: str, days: int = 7) -> str:
        """
        Retrieve recent meal logs for a family member.

        Args:
            human_name: Name of the person (partial match supported).
            days: How many days back to look (default 7).
        """
        logs = meal_repo.get_by_human(human_name, days=days)
        if not logs:
            return f"No meal logs found for '{human_name}' in the last {days} days."
        lines = [
            f"[{m.log_date}] {m.meal_type}: {m.food_name} ({m.quantity_g}g)"
            f"{'  – ' + m.notes if m.notes else ''}"
            for m in logs
        ]
        return f"Meal history for {human_name} (last {days} days):\n" + "\n".join(lines)

    @tool
    def get_exercise_history(human_name: str, days: int = 7) -> str:
        """
        Retrieve recent exercise entries for a family member.

        Args:
            human_name: Name of the person (partial match supported).
            days: How many days back to look (default 7).
        """
        entries = exercise_repo.get_by_human(human_name, days=days)
        if not entries:
            return f"No exercise records found for '{human_name}' in the last {days} days."
        lines = [
            f"[{e.exercise_date}] {e.activity} – {e.duration_minutes} min "
            f"({e.intensity})"
            f"{f', {e.distance_km} km' if e.distance_km else ''}"
            f"{f', ~{e.calories_burned} kcal' if e.calories_burned else ''}"
            for e in entries
        ]
        return f"Exercise history for {human_name} (last {days} days):\n" + "\n".join(lines)

    return [list_family_members, get_health_history, get_meal_history, get_exercise_history]
