"""Shopping list analysis tools.

Aggregates meal history, health conditions, nutritional gaps, seasonal
produce, and fridge inventory into a single rich context that the
ShoppingAgent reasons over to generate personalised shopping lists.
"""

from __future__ import annotations

from datetime import date, timedelta

from langchain_core.tools import tool

from nira_backend.database.connection import DatabaseConnection
from nira_backend.database.repositories import (
    FridgeInventoryRepository,
    HealthRecordRepository,
    MealLogRepository,
)

# ---------------------------------------------------------------------------
# Seasonal produce guide (Northern Hemisphere, monthly)
# ---------------------------------------------------------------------------

_SEASONAL: dict[int, dict] = {
    1: {
        "season": "Winter",
        "vegetables": ["kale", "parsnips", "celeriac", "leeks", "savoy cabbage", "swede"],
        "fruits": ["clementines", "blood oranges", "pomelos", "kiwi", "pears"],
        "note": "Warming soups and casseroles. Citrus for vitamin C and immune support.",
    },
    2: {
        "season": "Winter",
        "vegetables": ["purple sprouting broccoli", "Brussels sprouts", "leeks", "kale", "spinach"],
        "fruits": ["blood oranges", "clementines", "kiwi", "pink grapefruit"],
        "note": "Late winter — first spring greens begin to appear. Focus on iron and folate.",
    },
    3: {
        "season": "Spring",
        "vegetables": ["spring greens", "spinach", "radishes", "spring onions", "watercress"],
        "fruits": ["rhubarb", "citrus", "avocado"],
        "note": "Fresh spring greens excellent for iron and folate. Lighter meals begin.",
    },
    4: {
        "season": "Spring",
        "vegetables": ["asparagus", "peas", "artichokes", "rocket", "lettuce", "spring onions"],
        "fruits": ["rhubarb", "strawberries", "avocado"],
        "note": "Asparagus season. High fibre, high-protein spring produce.",
    },
    5: {
        "season": "Spring",
        "vegetables": ["asparagus", "peas", "broad beans", "fennel", "rocket", "cucumber"],
        "fruits": ["strawberries", "gooseberries", "avocado"],
        "note": "Peak asparagus and early berry season. Great for light, colourful meals.",
    },
    6: {
        "season": "Summer",
        "vegetables": ["courgette", "lettuce", "radishes", "peas", "cucumber", "tomatoes"],
        "fruits": ["strawberries", "cherries", "raspberries", "gooseberries"],
        "note": "Hydrating summer produce. High antioxidant content.",
    },
    7: {
        "season": "Summer",
        "vegetables": ["tomatoes", "courgette", "green beans", "sweetcorn", "peppers", "aubergine"],
        "fruits": ["blueberries", "raspberries", "peaches", "nectarines", "watermelon"],
        "note": "Peak vitamin and antioxidant season. Lycopene from tomatoes for heart health.",
    },
    8: {
        "season": "Summer",
        "vegetables": ["tomatoes", "sweetcorn", "courgette", "peppers", "aubergine", "runner beans"],
        "fruits": ["blackberries", "plums", "peaches", "figs", "melon"],
        "note": "Harvest in full swing. Excellent for grilling and salads.",
    },
    9: {
        "season": "Autumn",
        "vegetables": ["butternut squash", "broccoli", "cauliflower", "beetroot", "mushrooms", "spinach"],
        "fruits": ["apples", "pears", "grapes", "plums", "blackberries"],
        "note": "Root vegetables and squash rich in beta-carotene. Warming roasted dishes.",
    },
    10: {
        "season": "Autumn",
        "vegetables": ["pumpkin", "butternut squash", "kale", "Brussels sprouts", "celeriac", "leeks"],
        "fruits": ["apples", "pears", "figs", "quinces", "grapes"],
        "note": "Hearty harvest season. Rich in fibre and slow-release energy.",
    },
    11: {
        "season": "Autumn/Winter",
        "vegetables": ["kale", "Brussels sprouts", "parsnips", "sweet potato", "swede", "leeks"],
        "fruits": ["clementines", "apples", "pears", "pomegranates"],
        "note": "Pomegranates for antioxidants. Immune-boosting citrus returns.",
    },
    12: {
        "season": "Winter",
        "vegetables": ["kale", "Brussels sprouts", "red cabbage", "parsnips", "celeriac", "leeks"],
        "fruits": ["clementines", "pomelo", "pears", "kiwi", "blood oranges"],
        "note": "Cruciferous vegetables and citrus for immunity during cold season.",
    },
}

# ---------------------------------------------------------------------------
# Food group keyword mapping (for qualitative gap analysis)
# ---------------------------------------------------------------------------

_FOOD_GROUPS: dict[str, list[str]] = {
    "proteins": [
        "chicken", "beef", "pork", "lamb", "fish", "salmon", "tuna", "sardine",
        "egg", "tofu", "tempeh", "lentil", "bean", "turkey", "shrimp", "prawn",
        "chickpea", "mince", "steak", "cod", "haddock",
    ],
    "vegetables": [
        "broccoli", "spinach", "kale", "carrot", "tomato", "pepper", "onion",
        "garlic", "pea", "corn", "lettuce", "cucumber", "courgette", "zucchini",
        "mushroom", "celery", "beetroot", "asparagus", "cabbage", "cauliflower",
        "sweet potato", "squash", "leek", "aubergine",
    ],
    "fruits": [
        "apple", "banana", "orange", "berry", "grape", "mango", "strawberry",
        "blueberry", "raspberry", "peach", "pear", "melon", "kiwi", "avocado",
        "plum", "cherry", "watermelon", "lemon", "lime", "grapefruit",
    ],
    "dairy": [
        "milk", "yogurt", "yoghurt", "cheese", "butter", "cream", "cottage",
        "kefir", "fromage",
    ],
    "carbs": [
        "rice", "bread", "pasta", "oat", "potato", "noodle", "cereal",
        "quinoa", "couscous", "wheat", "rye", "barley", "tortilla", "wrap",
    ],
}


def _classify_food(food_name: str) -> list[str]:
    """Return the food groups a food name belongs to (keyword match)."""
    name_lower = food_name.lower()
    groups = []
    for group, keywords in _FOOD_GROUPS.items():
        if any(kw in name_lower for kw in keywords):
            groups.append(group)
    return groups or ["other"]


def _analyse_meal_variety(meals: list) -> str:
    """Produce a qualitative nutritional gap and variety analysis from meal logs."""
    if not meals:
        return "  No meal data available for analysis."

    food_names = [m.food_name for m in meals]
    unique_foods = set(food_names)

    # Food group coverage
    group_hits: dict[str, set] = {g: set() for g in _FOOD_GROUPS}
    for m in meals:
        for group in _classify_food(m.food_name):
            if group in group_hits:
                group_hits[group].add(m.food_name)

    # Repetition — foods eaten on 5+ of the last 7 days
    from collections import Counter
    date_foods: dict = {}
    for m in meals:
        date_foods.setdefault(str(m.log_date), set()).add(m.food_name)
    food_day_counts: Counter = Counter()
    for day_set in date_foods.values():
        for f in day_set:
            food_day_counts[f] += 1
    repeated = [f for f, count in food_day_counts.most_common() if count >= 5]

    # Meal type coverage
    meal_types = {m.meal_type for m in meals}

    lines = []
    lines.append(f"  Unique foods logged: {len(unique_foods)}")
    lines.append(f"  Meal types covered: {', '.join(sorted(meal_types))}")

    for group, items in group_hits.items():
        if items:
            sample = ", ".join(sorted(items)[:5])
            lines.append(f"  {group.capitalize()} sources: {sample}")
        else:
            lines.append(f"  {group.capitalize()} sources: ⚠️  NONE detected — consider adding these")

    if repeated:
        lines.append(f"  Eaten almost daily (watch for monotony): {', '.join(repeated)}")

    if len(unique_foods) < 8:
        lines.append("  ⚠️  Low food variety overall — aim for more diverse ingredients")

    missing_types = {"breakfast", "lunch", "dinner"} - meal_types
    if missing_types:
        lines.append(f"  ⚠️  Missing meal types: {', '.join(sorted(missing_types))}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool factories
# ---------------------------------------------------------------------------


def make_shopping_tools(db: DatabaseConnection) -> list:
    """
    Return tools that provide comprehensive shopping list context.

    Args:
        db: Active database connection.

    Returns:
        List of LangChain tool callables.
    """
    meal_repo = MealLogRepository(db)
    health_repo = HealthRecordRepository(db)
    fridge_repo = FridgeInventoryRepository(db)

    @tool
    def get_seasonal_foods() -> str:
        """
        Return a guide to what produce is in season this month.

        Use this when you want to recommend fresh, seasonal ingredients in a
        shopping list.  Seasonal foods are typically cheaper, more nutritious,
        and better for the environment.
        """
        month = date.today().month
        info = _SEASONAL[month]
        lines = [
            f"=== Seasonal Produce for {date.today().strftime('%B')} ({info['season']}) ===",
            "",
            f"VEGETABLES IN SEASON: {', '.join(info['vegetables'])}",
            f"FRUITS IN SEASON:     {', '.join(info['fruits'])}",
            "",
            f"SEASONAL NOTE: {info['note']}",
        ]
        return "\n".join(lines)

    @tool
    def get_shopping_context(
        human_names: str,
        days: int = 7,
        include_fridge: bool = True,
    ) -> str:
        """
        Gather comprehensive context for building a personalised shopping list.

        This aggregates recent eating patterns, health conditions, nutritional
        gap analysis, seasonal produce, and current fridge/pantry inventory for
        one or more family members.  Always call this before generating a
        shopping list.

        Args:
            human_names: Comma-separated names of family members to analyse,
                         e.g. 'Alice' or 'Alice, John'.
            days: Number of past days of eating data to include (default 7).
            include_fridge: Whether to include inventory in the context so
                            you can avoid recommending items already in stock.
        """
        today = date.today()
        names = [n.strip() for n in human_names.split(",") if n.strip()]
        month_info = _SEASONAL[today.month]

        sections: list[str] = []
        sections.append(
            f"=== Shopping Context ===\n"
            f"DATE: {today.isoformat()}  |  "
            f"SEASON: {month_info['season']}  |  "
            f"ANALYSIS WINDOW: last {days} days\n"
        )

        # --- Seasonal produce ---
        sections.append("SEASONAL PRODUCE THIS MONTH:")
        sections.append(f"  Vegetables: {', '.join(month_info['vegetables'])}")
        sections.append(f"  Fruits:     {', '.join(month_info['fruits'])}")
        sections.append(f"  Note:       {month_info['note']}\n")

        # --- Per-person meal and health analysis ---
        for name in names:
            sections.append(f"--- {name.upper()} ---")

            # Meals
            meals = meal_repo.get_by_human(name, days=days)
            sections.append(f"\nMEAL PATTERNS (last {days} days):")
            if meals:
                by_date: dict = {}
                for m in meals:
                    by_date.setdefault(str(m.log_date), []).append(m)
                for d in sorted(by_date.keys(), reverse=True)[:5]:  # show last 5 days
                    day_summary = ", ".join(
                        f"{m.meal_type}: {m.food_name} ({m.quantity_g}g)"
                        for m in by_date[d]
                    )
                    sections.append(f"  {d}: {day_summary}")
                if len(by_date) > 5:
                    sections.append(f"  ... and {len(by_date) - 5} more days")
            else:
                sections.append(f"  No meals logged for '{name}' in the last {days} days.")

            # Nutritional gap analysis
            sections.append(f"\nNUTRITIONAL GAP ANALYSIS (last {days} days):")
            sections.append(_analyse_meal_variety(meals))

            # Health records
            end = today
            start = end - timedelta(days=max(days, 14))
            all_records = health_repo.get_by_date_range(start, end)
            person_records = [
                r for r in all_records if name.lower() in r.human_name.lower()
            ]
            sections.append(f"\nHEALTH CONDITIONS (affects dietary needs):")
            if not person_records:
                sections.append("  No recent health records found.")
            else:
                by_type: dict = {}
                for r in person_records:
                    by_type.setdefault(r.record_type, []).append(r)
                for rtype, records in sorted(by_type.items()):
                    latest = records[0]
                    m = latest.measurement
                    sections.append(
                        f"  {rtype} — latest ({latest.record_date}): "
                        f"{m.model_dump_json()}"
                    )
            sections.append("")

        # --- Fridge / pantry inventory ---
        if include_fridge:
            sections.append("CURRENT INVENTORY (already have — avoid duplicating):")
            all_items = fridge_repo.get_all()
            if not all_items:
                sections.append("  Inventory is empty or not tracked.")
            else:
                by_loc: dict = {}
                for it in all_items:
                    by_loc.setdefault(it.location, []).append(it)
                for loc in sorted(by_loc):
                    contents = ", ".join(
                        f"{it.food_name} ({it.quantity_display})"
                        for it in by_loc[loc]
                    )
                    sections.append(f"  {loc.capitalize()}: {contents}")

            expiring = fridge_repo.get_expiring_soon(days=5)
            if expiring:
                names_exp = ", ".join(
                    f"{it.food_name} (exp {it.expiry_date})" for it in expiring
                )
                sections.append(
                    f"\n  ⚠️  Use-first items (expiring ≤5 days): {names_exp}"
                )
            sections.append("")

        return "\n".join(sections)

    return [get_seasonal_foods, get_shopping_context]
