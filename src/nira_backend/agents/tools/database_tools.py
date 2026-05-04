"""Read-only database query tools shared across agents."""

from datetime import date

from langchain_core.tools import tool

from nira_backend.database.connection import DatabaseConnection
from nira_backend.database.repositories import (
    ExerciseRepository,
    FridgeInventoryRepository,
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


def make_fridge_db_tools(db: DatabaseConnection) -> list:
    """
    Return read-only fridge/pantry inventory query tools.

    Args:
        db: Active database connection.

    Returns:
        List of LangChain tool callables.
    """
    fridge_repo = FridgeInventoryRepository(db)

    @tool
    def list_fridge_contents(location: str = "all") -> str:
        """
        List what is currently in the household inventory.

        Args:
            location: Filter by location — 'fridge', 'freezer', 'pantry',
                      'other', or 'all' (default) to show everything.
        """
        if location == "all":
            items = fridge_repo.get_all()
        else:
            items = fridge_repo.get_by_location(location)

        if not items:
            loc_str = "inventory" if location == "all" else location
            return f"Nothing found in {loc_str}."

        by_location: dict[str, list] = {}
        for item in items:
            by_location.setdefault(item.location, []).append(item)

        lines = []
        for loc, loc_items in sorted(by_location.items()):
            lines.append(f"\n[{loc.upper()}]")
            for it in loc_items:
                expiry_str = ""
                if it.expiry_date:
                    days = it.days_until_expiry
                    if it.is_expired:
                        expiry_str = " ⚠️ EXPIRED"
                    elif days is not None and days <= 3:
                        expiry_str = f" ⚠️ expires in {days}d"
                    else:
                        expiry_str = f" (exp {it.expiry_date})"
                notes_str = f" — {it.notes}" if it.notes else ""
                lines.append(f"  • {it.quantity_display} of {it.food_name}{expiry_str}{notes_str}")

        return "Household inventory:" + "\n".join(lines)

    @tool
    def get_expiring_items(days: int = 3) -> str:
        """
        Show inventory items that will expire within the next N days.

        Args:
            days: Look-ahead window in days (default 3).
        """
        items = fridge_repo.get_expiring_soon(days=days)
        if not items:
            return f"No items expiring within the next {days} days."
        lines = []
        for it in items:
            d = it.days_until_expiry
            urgency = "TODAY" if d == 0 else (f"EXPIRED {-d}d ago" if d and d < 0 else f"in {d}d")
            lines.append(f"  • {it.quantity_display} of {it.food_name} ({it.location}) — {urgency}")
        return f"Items expiring within {days} days:\n" + "\n".join(lines)

    return [list_fridge_contents, get_expiring_items]


def make_dietary_tools(db: DatabaseConnection) -> list:
    """
    Return tools that aggregate data across domains for dietary advice.

    Args:
        db: Active database connection.

    Returns:
        List of LangChain tool callables.
    """
    meal_repo = MealLogRepository(db)
    health_repo = HealthRecordRepository(db)
    fridge_repo = FridgeInventoryRepository(db)

    @tool
    def get_dietary_context(
        human_name: str, days: int = 7, include_fridge: bool = True
    ) -> str:
        """
        Gather comprehensive diet, health, and inventory context for making
        personalised food suggestions.

        Call this tool whenever you need to analyse eating habits, health trends,
        or make dietary recommendations.  It returns a structured summary so you
        can reason over the data and provide helpful, specific suggestions.

        Args:
            human_name: Name of the family member to analyse.
            days: How many past days of data to include (default 7).
            include_fridge: Whether to include current fridge/pantry inventory
                            in the context (default True).
        """
        from datetime import timedelta

        sections: list[str] = [
            f"=== Dietary Context for {human_name} (last {days} days) ===\n"
        ]

        # --- Meal history ---
        meals = meal_repo.get_by_human(human_name, days=days)
        if meals:
            sections.append("RECENT MEALS:")
            by_date: dict = {}
            for m in meals:
                by_date.setdefault(str(m.log_date), []).append(m)
            for d, day_meals in sorted(by_date.items(), reverse=True):
                day_lines = [
                    f"    {m.meal_type}: {m.food_name} ({m.quantity_g}g)"
                    + (f" — {m.notes}" if m.notes else "")
                    for m in day_meals
                ]
                sections.append(f"  {d}:\n" + "\n".join(day_lines))
        else:
            sections.append(f"RECENT MEALS: None logged in the last {days} days.")

        # --- Health overview ---
        from datetime import date

        end = date.today()
        start = end - timedelta(days=days * 2)  # slightly wider window for health
        health_records = health_repo.get_by_date_range(start, end)
        person_records = [
            r for r in health_records if human_name.lower() in r.human_name.lower()
        ]

        sections.append("\nHEALTH OVERVIEW:")
        if not person_records:
            sections.append("  No health records found in the analysis window.")
        else:
            by_type: dict = {}
            for r in person_records:
                by_type.setdefault(r.record_type, []).append(r)
            for rtype, records in sorted(by_type.items()):
                latest = records[0]
                m = latest.measurement
                sections.append(
                    f"  {rtype} (latest {latest.record_date}): {m.model_dump_json()}"
                )

        # --- Fridge inventory ---
        if include_fridge:
            all_items = fridge_repo.get_all()
            sections.append("\nFRIDGE / PANTRY INVENTORY:")
            if not all_items:
                sections.append("  Inventory is empty or not set up.")
            else:
                for it in all_items:
                    expiry_str = ""
                    if it.expiry_date:
                        d_left = it.days_until_expiry
                        if it.is_expired:
                            expiry_str = " [EXPIRED]"
                        elif d_left is not None and d_left <= 3:
                            expiry_str = f" [expires in {d_left}d — use soon!]"
                        else:
                            expiry_str = f" [exp {it.expiry_date}]"
                    sections.append(
                        f"  • {it.quantity_display} of {it.food_name} ({it.location}){expiry_str}"
                    )

            expiring = fridge_repo.get_expiring_soon(days=3)
            if expiring:
                names = ", ".join(it.food_name for it in expiring)
                sections.append(
                    f"\n  ⚠️  Use soon (expiring within 3 days): {names}"
                )

        return "\n".join(sections)

    return [get_dietary_context]
