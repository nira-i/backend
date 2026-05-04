"""Read-only database query tools shared across agents."""

from datetime import date

from langchain_core.tools import tool

from nira_backend.database.connection import DatabaseConnection
from nira_backend.database.repositories import (
    ExerciseRepository,
    FridgeInventoryRepository,
    HealthIncidentRepository,
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


def make_incident_db_tools(db: DatabaseConnection) -> list:
    """
    Return read-only query tools for health incidents.

    Args:
        db: Active database connection.

    Returns:
        List of LangChain tool callables.
    """
    incident_repo = HealthIncidentRepository(db)

    @tool
    def get_incident_history(human_name: str, days: int = 30) -> str:
        """
        Retrieve recent health incidents for a family member.

        Covers non-metric events such as illnesses, injuries, pain episodes,
        fatigue, and stress.

        Args:
            human_name: Name of the person (partial match supported).
            days: How many days back to look (default 30).
        """
        incidents = incident_repo.get_by_human(human_name, days=days)
        if not incidents:
            return (
                f"No health incidents recorded for '{human_name}' "
                f"in the last {days} days."
            )
        lines = []
        for inc in incidents:
            severity_str = f" [{inc.severity}]" if inc.severity else ""
            body_str = f" — {inc.body_part}" if inc.body_part else ""
            symptom_str = (
                f" | symptoms: {', '.join(inc.symptoms)}" if inc.symptoms else ""
            )
            lines.append(
                f"[{inc.incident_date}] {inc.incident_type.upper()}{severity_str}"
                f"{body_str}: {inc.description}{symptom_str}"
            )
        return (
            f"Health incidents for {human_name} (last {days} days):\n"
            + "\n".join(lines)
        )

    return [get_incident_history]


# ---------------------------------------------------------------------------
# Exercise analysis tools (for recommendations)
# ---------------------------------------------------------------------------

_EXERCISE_CATEGORIES: dict[str, list[str]] = {
    "cardio": [
        "run", "jog", "walk", "swim", "cycle", "cycling", "bike", "rowing",
        "cardio", "hiit", "sprint", "dance", "aerobic", "elliptical", "treadmill",
        "stair", "jump rope", "skipping",
    ],
    "strength": [
        "weight", "lift", "dumbbell", "barbell", "squat", "deadlift", "bench",
        "press", "curl", "row", "plank", "resistance", "gym", "pull-up",
        "push-up", "pushup", "pullup", "lunge", "kettle",
    ],
    "flexibility": [
        "yoga", "stretch", "pilates", "mobility", "foam roll", "meditation",
        "tai chi", "barre",
    ],
    "sports": [
        "football", "soccer", "tennis", "basketball", "badminton", "cricket",
        "rugby", "volleyball", "hockey", "martial art", "boxing", "hiking",
        "climbing", "surfing",
    ],
}


def _classify_exercise(activity: str) -> str:
    """Return the exercise category for a given activity name."""
    name_lower = activity.lower()
    for category, keywords in _EXERCISE_CATEGORIES.items():
        if any(kw in name_lower for kw in keywords):
            return category
    return "other"


def make_exercise_analysis_tools(db: DatabaseConnection) -> list:
    """
    Return tools that analyse exercise history for personalised recommendations.

    Args:
        db: Active database connection.

    Returns:
        List of LangChain tool callables.
    """
    exercise_repo = ExerciseRepository(db)

    @tool
    def get_exercise_analysis_context(human_name: str, days: int = 28) -> str:
        """
        Analyse recent exercise history and surface patterns, gaps, and
        recommendations context for a family member.

        Call this before making exercise recommendations.  It returns a
        structured analysis covering frequency, activity variety, intensity
        distribution, rest-day patterns, and identified gaps — so you can
        suggest a well-rounded, progressive training plan.

        Args:
            human_name: Name of the family member to analyse.
            days: Analysis window in days (default 28 — four weeks).
        """
        from collections import Counter
        from datetime import timedelta

        entries = exercise_repo.get_by_human(human_name, days=days)

        if not entries:
            return (
                f"No exercise logged for '{human_name}' in the last {days} days.\n"
                f"Recommendation context: fresh start — suggest a gentle beginner "
                f"routine covering cardio, strength, and flexibility."
            )

        today = date.today()
        sections: list[str] = [
            f"=== Exercise Analysis for {human_name} (last {days} days) ===\n"
        ]

        # --- Volume ---
        total_sessions = len(entries)
        total_minutes = sum(e.duration_minutes for e in entries)
        total_calories = sum(e.calories_burned or 0 for e in entries)
        avg_duration = total_minutes / total_sessions
        weeks = days / 7
        sessions_per_week = total_sessions / weeks

        sections.append("OVERALL VOLUME:")
        sections.append(f"  Sessions: {total_sessions} ({sessions_per_week:.1f}/week avg)")
        sections.append(f"  Total time: {total_minutes} min ({avg_duration:.0f} min/session avg)")
        if total_calories:
            sections.append(f"  Est. calories burned: {total_calories:.0f} kcal")

        # --- Activity type breakdown ---
        type_counter: Counter = Counter()
        type_minutes: Counter = Counter()
        for e in entries:
            cat = _classify_exercise(e.activity)
            type_counter[cat] += 1
            type_minutes[cat] += e.duration_minutes

        sections.append("\nACTIVITY TYPE BREAKDOWN:")
        for cat, count in type_counter.most_common():
            pct = 100 * count / total_sessions
            sections.append(
                f"  {cat.capitalize()}: {count} sessions "
                f"({pct:.0f}%) — {type_minutes[cat]} min total"
            )

        missing_types = [
            cat for cat in ["cardio", "strength", "flexibility"]
            if type_counter[cat] == 0
        ]
        if missing_types:
            sections.append(
                f"\n  ⚠️  Missing exercise types: {', '.join(missing_types)}"
            )

        # --- Intensity distribution ---
        intensity_counter: Counter = Counter(e.intensity for e in entries)
        sections.append("\nINTENSITY DISTRIBUTION:")
        for intensity in ["light", "moderate", "vigorous"]:
            count = intensity_counter[intensity]
            pct = 100 * count / total_sessions
            sections.append(f"  {intensity.capitalize()}: {count} sessions ({pct:.0f}%)")

        if intensity_counter["vigorous"] == 0:
            sections.append("  ⚠️  No vigorous sessions — consider adding some higher-intensity work")
        if intensity_counter["light"] == 0:
            sections.append("  ⚠️  No active recovery / light sessions logged")

        # --- Days since last session by type ---
        sections.append("\nDAYS SINCE LAST SESSION BY TYPE:")
        type_last_date: dict[str, date] = {}
        for e in entries:
            cat = _classify_exercise(e.activity)
            d = e.exercise_date if isinstance(e.exercise_date, date) else date.fromisoformat(str(e.exercise_date))
            if cat not in type_last_date or d > type_last_date[cat]:
                type_last_date[cat] = d
        for cat in ["cardio", "strength", "flexibility", "sports"]:
            if cat in type_last_date:
                days_ago = (today - type_last_date[cat]).days
                sections.append(f"  {cat.capitalize()}: {days_ago} day(s) ago")
            else:
                sections.append(f"  {cat.capitalize()}: never logged in window")

        # --- Rest day pattern ---
        active_dates = {
            (e.exercise_date if isinstance(e.exercise_date, date)
             else date.fromisoformat(str(e.exercise_date)))
            for e in entries
        }
        rest_days = days - len(active_dates)
        consecutive_max = 0
        streak = 0
        for i in range(days):
            d = today - timedelta(days=i)
            if d in active_dates:
                streak += 1
                consecutive_max = max(consecutive_max, streak)
            else:
                streak = 0

        sections.append(f"\nREST & RECOVERY:")
        sections.append(f"  Rest days: {rest_days} / {days}")
        sections.append(f"  Longest active streak: {consecutive_max} consecutive days")
        if consecutive_max >= 6:
            sections.append("  ⚠️  Long consecutive streak — ensure adequate recovery days")
        if rest_days > days * 0.7:
            sections.append("  ⚠️  Low activity frequency — encourage more consistent sessions")

        # --- Recent sessions (last 7 days) ---
        recent = [
            e for e in entries
            if (today - (e.exercise_date if isinstance(e.exercise_date, date)
                         else date.fromisoformat(str(e.exercise_date)))).days <= 7
        ]
        sections.append(f"\nLAST 7 DAYS ({len(recent)} sessions):")
        if recent:
            for e in sorted(recent, key=lambda x: x.exercise_date, reverse=True):
                sections.append(
                    f"  [{e.exercise_date}] {e.activity} — {e.duration_minutes} min "
                    f"({e.intensity})"
                    f"{f', {e.distance_km} km' if e.distance_km else ''}"
                )
        else:
            sections.append("  No sessions in the last 7 days.")

        return "\n".join(sections)

    return [get_exercise_analysis_context]


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
