# Testing NIRA with Dummy Data

This guide walks through seeding a realistic family dataset and verifying every major feature. Steps 1–3 require no API key. Step 4 (live agent) requires `secrets/gemini_api_key.txt`.

---

## Prerequisites

```bash
uv sync                          # install all dependencies
cp config/local.example.json config/local.json   # optional — defaults work fine
```

---

## Step 1 — Run the test suite

Verify the codebase is healthy before touching any live data.

```bash
python -m pytest tests/ --no-cov -q
```

Expected output: **400 passed**.

---

## Step 2 — Seed dummy data

Create `scripts/seed_dummy_data.py` with the content below, then run it.

```python
"""Seed realistic dummy data for a two-person family (Alice + John)."""

from datetime import date, timedelta

from nira_backend.database.connection import DatabaseConnection
from nira_backend.database.repositories import (
    ExerciseRepository,
    FridgeInventoryRepository,
    HealthIncidentRepository,
    HealthRecordRepository,
    HumanRepository,
    MealLogRepository,
)
from nira_backend.data_models.exercise import ExerciseEntry, MealLog
from nira_backend.data_models.food_inventory import FridgeItem
from nira_backend.data_models.health_incident import HealthIncident
from nira_backend.data_models.health_record import (
    BloodGlucoseRecord,
    BloodPressureRecord,
    HeartRateRecord,
    SleepRecord,
)
from nira_backend.data_models.human import Human

db = DatabaseConnection()
today = date.today()

# ── 1. Family members ──────────────────────────────────────────────────────
human_repo = HumanRepository(db)
human_repo.create(Human(
    name="Alice",
    date_of_birth=date(1988, 4, 12),
    gender="female",
    weight=65.0,
    height=168.0,
))
human_repo.create(Human(
    name="John",
    date_of_birth=date(1985, 9, 3),
    gender="male",
    weight=82.0,
    height=178.0,
))
print("✓ Family members added")

# ── 2. Health records ──────────────────────────────────────────────────────
health_repo = HealthRecordRepository(db)

# John — slightly elevated blood pressure over the past week
for days_ago, systolic, diastolic in [(0, 132, 84), (2, 135, 86), (5, 128, 82)]:
    health_repo.create(BloodPressureRecord(
        human_name="John",
        record_date=today - timedelta(days=days_ago),
        systolic_mmhg=systolic,
        diastolic_mmhg=diastolic,
    ))

# Alice — blood glucose and poor sleep
health_repo.create(BloodGlucoseRecord(
    human_name="Alice",
    record_date=today,
    glucose_mmol_per_l=5.2,
))
for days_ago, hours, quality in [(0, 5.5, "poor"), (1, 6.0, "fair"), (2, 7.5, "good")]:
    health_repo.create(SleepRecord(
        human_name="Alice",
        record_date=today - timedelta(days=days_ago),
        hours=hours,
        quality=quality,
    ))

# Alice — heart rate
health_repo.create(HeartRateRecord(
    human_name="Alice",
    record_date=today,
    bpm=72,
))
print("✓ Health records added")

# ── 3. Health incidents ────────────────────────────────────────────────────
incident_repo = HealthIncidentRepository(db)

incident_repo.create(HealthIncident(
    human_name="Alice",
    incident_date=today,
    description="Shoulder pain after long hours working at desk",
    symptoms=["shoulder pain", "stiffness", "tension"],
    severity="mild",
    body_part="shoulder",
    incident_type="pain",
    notes="Started after 10-hour work session — worsens with mouse use",
))
incident_repo.create(HealthIncident(
    human_name="Alice",
    incident_date=today - timedelta(days=3),
    description="Felt very fatigued and run-down mid-week",
    symptoms=["fatigue", "low energy"],
    severity="mild",
    incident_type="fatigue",
))
incident_repo.create(HealthIncident(
    human_name="John",
    incident_date=today - timedelta(days=2),
    description="Fever and sore throat — likely seasonal cold",
    symptoms=["fever", "sore throat", "runny nose", "fatigue"],
    severity="moderate",
    incident_type="illness",
    notes="Took paracetamol, resting at home",
))
incident_repo.create(HealthIncident(
    human_name="John",
    incident_date=today - timedelta(days=7),
    description="Work stress causing headaches and tension",
    symptoms=["headache", "neck tension"],
    severity="mild",
    body_part="head",
    incident_type="stress",
))
print("✓ Health incidents added")

# ── 4. Exercise sessions (Alice — last 4 weeks) ───────────────────────────
exercise_repo = ExerciseRepository(db)

sessions = [
    # days_ago, activity,          duration, intensity,   distance_km
    (0,  "Running",                30,       "vigorous",  5.0),
    (2,  "Yoga",                   45,       "light",     None),
    (4,  "Weight training",        40,       "moderate",  None),
    (6,  "Running",                25,       "moderate",  4.0),
    (7,  "Cycling",                60,       "vigorous",  20.0),
    (9,  "Yoga",                   30,       "light",     None),
    (11, "Running",                35,       "vigorous",  5.5),
    (14, "Swimming",               45,       "moderate",  None),
    (16, "Weight training",        50,       "moderate",  None),
    (18, "Running",                28,       "vigorous",  4.8),
    (21, "Yoga",                   40,       "light",     None),
    (23, "Cycling",                45,       "moderate",  15.0),
    (25, "Running",                32,       "vigorous",  5.2),
    (27, "Weight training",        35,       "moderate",  None),
]
for days_ago, activity, duration, intensity, distance in sessions:
    exercise_repo.create(ExerciseEntry(
        human_name="Alice",
        exercise_date=today - timedelta(days=days_ago),
        activity=activity,
        duration_minutes=duration,
        intensity=intensity,
        distance_km=distance,
    ))
print("✓ Exercise sessions added")

# ── 5. Meal logs (Alice — last 7 days) ────────────────────────────────────
meal_repo = MealLogRepository(db)

meals = [
    # days_ago, food_name,          grams, meal_type
    (0, "Oatmeal with banana",      300,   "breakfast"),
    (0, "Grilled chicken salad",    350,   "lunch"),
    (0, "Apple",                    150,   "snack"),
    (1, "Scrambled eggs on toast",  250,   "breakfast"),
    (1, "Tuna pasta",               400,   "lunch"),
    (1, "Grilled salmon",           200,   "dinner"),
    (2, "Greek yoghurt",            200,   "breakfast"),
    (2, "Vegetable stir fry",       380,   "lunch"),
    (2, "Chicken curry with rice",  450,   "dinner"),
    (3, "Oatmeal",                  280,   "breakfast"),
    (3, "Caesar salad",             300,   "lunch"),
    (4, "Banana smoothie",          350,   "breakfast"),
    (4, "Lentil soup",              400,   "lunch"),
    (5, "Eggs and avocado toast",   300,   "breakfast"),
    (5, "Pasta bolognese",          450,   "dinner"),
    (6, "Oatmeal with berries",     300,   "breakfast"),
    (6, "Chicken sandwich",         350,   "lunch"),
]
for days_ago, food_name, grams, meal_type in meals:
    meal_repo.create(MealLog(
        human_name="Alice",
        log_date=today - timedelta(days=days_ago),
        food_name=food_name,
        quantity_grams=grams,
        meal_type=meal_type,
    ))
print("✓ Meal logs added")

# ── 6. Fridge / pantry inventory ──────────────────────────────────────────
fridge_repo = FridgeInventoryRepository(db)

inventory = [
    # food_name,          qty,   unit,      location,  expiry_days, notes
    ("Eggs",             6,     "pieces",  "fridge",   7,   None),
    ("Broccoli",         300,   "g",       "fridge",   3,   "Use soon"),
    ("Spinach",          150,   "g",       "fridge",   2,   "Getting old"),
    ("Oat milk",         1,     "l",       "fridge",   14,  None),
    ("Greek yoghurt",    500,   "g",       "fridge",   5,   None),
    ("Chicken breast",   2000,  "g",       "freezer",  30,  None),
    ("Salmon fillets",   400,   "g",       "freezer",  45,  None),
    ("Rolled oats",      500,   "g",       "pantry",   90,  None),
    ("Lentils",          400,   "g",       "pantry",   180, None),
    ("Tinned tomatoes",  800,   "g",       "pantry",   365, None),
    ("Olive oil",        750,   "ml",      "pantry",   365, None),
    ("Brown rice",       1000,  "g",       "pantry",   180, None),
]
for food_name, qty, unit, location, expiry_days, notes in inventory:
    fridge_repo.create(FridgeItem(
        food_name=food_name,
        quantity=qty,
        unit=unit,
        location=location,
        added_date=today,
        expiry_date=today + timedelta(days=expiry_days),
        notes=notes,
    ))
print("✓ Fridge / pantry inventory added")
print("\nAll dummy data seeded successfully.")
```

Run it:

```bash
python scripts/seed_dummy_data.py
```

---

## Step 3 — Verify data directly (no API key)

Create `scripts/check_data.py` and run it to confirm every repository is returning data correctly.

```python
"""Query all repositories and tool outputs without an LLM."""

from nira_backend.database.connection import DatabaseConnection
from nira_backend.database.repositories import (
    ExerciseRepository,
    FridgeInventoryRepository,
    HealthIncidentRepository,
    HealthRecordRepository,
    HumanRepository,
    MealLogRepository,
)
from nira_backend.agents.tools.database_tools import (
    make_exercise_analysis_tools,
    make_fridge_db_tools,
    make_incident_db_tools,
    make_shared_db_tools,
)

db = DatabaseConnection()
DIVIDER = "\n" + "─" * 60 + "\n"

# ── Family members ─────────────────────────────────────────────
tool = next(t for t in make_shared_db_tools(db) if t.name == "list_family_members")
print(DIVIDER + "FAMILY MEMBERS")
print(tool.invoke({}))

# ── Health history ─────────────────────────────────────────────
tool = next(t for t in make_shared_db_tools(db) if t.name == "get_health_history")
print(DIVIDER + "HEALTH HISTORY — Alice (last 14 days)")
print(tool.invoke({"human_name": "Alice", "days": 14}))
print(DIVIDER + "HEALTH HISTORY — John (last 14 days)")
print(tool.invoke({"human_name": "John", "days": 14}))

# ── Health incidents ───────────────────────────────────────────
tool = next(t for t in make_incident_db_tools(db) if t.name == "get_incident_history")
print(DIVIDER + "HEALTH INCIDENTS — Alice")
print(tool.invoke({"human_name": "Alice", "days": 30}))
print(DIVIDER + "HEALTH INCIDENTS — John")
print(tool.invoke({"human_name": "John", "days": 30}))

# ── Exercise history ───────────────────────────────────────────
tool = next(t for t in make_shared_db_tools(db) if t.name == "get_exercise_history")
print(DIVIDER + "EXERCISE HISTORY — Alice (last 7 days)")
print(tool.invoke({"human_name": "Alice", "days": 7}))

# ── Exercise analysis ──────────────────────────────────────────
tool = next(t for t in make_exercise_analysis_tools(db) if t.name == "get_exercise_analysis_context")
print(DIVIDER + "EXERCISE ANALYSIS — Alice (last 28 days)")
print(tool.invoke({"human_name": "Alice", "days": 28}))

# ── Fridge inventory ───────────────────────────────────────────
tool = next(t for t in make_fridge_db_tools(db) if t.name == "list_fridge_contents")
print(DIVIDER + "FRIDGE / PANTRY CONTENTS")
print(tool.invoke({}))

tool = next(t for t in make_fridge_db_tools(db) if t.name == "get_expiring_items")
print(DIVIDER + "EXPIRING SOON (next 5 days)")
print(tool.invoke({"days": 5}))
```

Run it:

```bash
python scripts/check_data.py
```

**What to look for:**

| Section | Expected output |
|---------|----------------|
| Family members | Alice and John listed with age and BMI |
| Health history (John) | Three BP readings around 130/84 — slightly elevated |
| Health incidents (Alice) | Shoulder pain + fatigue entries |
| Health incidents (John) | Fever/cold + stress/headache entries |
| Exercise analysis (Alice) | 14 sessions, cardio/strength/flexibility all present, intensity mix |
| Fridge contents | 12 items across fridge/freezer/pantry |
| Expiring soon | Broccoli (3 days) and Spinach (2 days) flagged |

---

## Step 4 — Live agent test (requires API key)

Add your Gemini API key:

```bash
echo "YOUR_API_KEY" > secrets/gemini_api_key.txt
```

Create `scripts/smoke_test.py`:

```python
"""End-to-end smoke test through MainAgent (requires Gemini API key)."""

from nira_backend.agents import MainAgent

DIVIDER = "\n" + "=" * 60 + "\n"

with MainAgent() as nira:

    # ── Health incidents ───────────────────────────────────────
    print(DIVIDER + "INCIDENT — natural language")
    print(nira.chat(
        "Alice has been getting shoulder pain this week from sitting at her "
        "desk too long. It's mild but annoying."
    ))

    print(DIVIDER + "INCIDENT — query")
    print(nira.chat("What health issues has Alice had recently?"))

    # ── Exercise recommendation ────────────────────────────────
    print(DIVIDER + "EXERCISE RECOMMENDATION")
    print(nira.chat(
        "Can you analyse Alice's exercise over the past month and give her "
        "specific recommendations for next week?"
    ))

    # ── Meal logging ───────────────────────────────────────────
    print(DIVIDER + "MEAL LOG — natural language")
    print(nira.chat(
        "Alice had overnight oats with blueberries for breakfast, "
        "about 300g, and a large chicken salad for lunch."
    ))

    # ── Dietary suggestions ────────────────────────────────────
    print(DIVIDER + "DIETARY SUGGESTIONS")
    print(nira.chat(
        "What should Alice eat for dinner tonight? Check what's in the "
        "fridge and her recent health data."
    ))

    # ── Fridge check ───────────────────────────────────────────
    print(DIVIDER + "FRIDGE EXPIRY CHECK")
    print(nira.chat("What's expiring soon in the fridge?"))

    # ── Shopping list ──────────────────────────────────────────
    print(DIVIDER + "SHOPPING LIST")
    print(nira.chat(
        "Generate a weekly shopping list for Alice. Consider her health "
        "records, what she has been eating, and what is already in the fridge."
    ))

    # ── John's health ──────────────────────────────────────────
    print(DIVIDER + "JOHN'S HEALTH SUMMARY")
    print(nira.chat(
        "John's blood pressure has been a bit high lately and he had a cold "
        "this week. What does his health picture look like and what should "
        "he be eating?"
    ))
```

Run it:

```bash
python scripts/smoke_test.py
```

**What to expect from the agent:**

| Prompt | Expected agent behaviour |
|--------|--------------------------|
| Alice's shoulder pain | HealthAgent logs it as `pain` / `shoulder`, confirms with severity |
| Alice's incidents query | Returns shoulder pain and fatigue entries from the database |
| Exercise recommendation | Reads 4-week analysis (14 sessions) and gives 3–5 specific suggestions |
| Meal log | NutritionAgent parses free text and logs two meals |
| Dietary suggestions | Combines recent meals + fridge inventory + sleep data (poor sleep → magnesium-rich foods) |
| Expiring soon | Lists broccoli and spinach |
| Shopping list | Categorised list driven by nutritional gaps, John's BP, and what's already in stock |
| John's health | Notes elevated BP and recent cold; suggests low-sodium, immunity-supporting foods |

---

## Resetting between runs

The database file is `nira_data.db` in the project root (or whatever path is in `config/local.json`). To start fresh:

```bash
rm nira_data.db          # delete the database
python scripts/seed_dummy_data.py   # re-seed
```
