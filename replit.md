# NIRA Backend

Backend component of the NIRA family health and food management system.

## Project Overview

A pure Python library (no web server) providing data models, SQLite database management,
a Gemini LLM integration, and a LangChain-based multi-agent system for tracking food,
meals, health metrics, exercise, and household food inventory for a family.
Designed to run locally on a Raspberry Pi. A future separate repo will add an API layer and frontend.

## Architecture

- **Language**: Python 3.11
- **Build System**: setuptools (pyproject.toml), managed via uv
- **Key Dependencies**: `pydantic`, `langchain`, `langchain-google-genai`, `google-generativeai`
- **Dev Dependencies**: `pytest`, `pytest-cov`, `black`, `ruff`, `mypy`
- **Database**: SQLite (via built-in `sqlite3`) — lightweight, no server required
- **Agent Memory**: JSON files per agent in `data/memory/` (gitignored, stays on device)

## Project Structure

```
src/nira_backend/
  __init__.py
  config.py                 # Central config: get_database_path(), get_data_dir()
  data_models/
    __init__.py
    human.py                # Human model with BMI, age
    measurements.py         # Weight, Length, BodyShapeMeasurements
    food_item.py            # FoodItem, NutritionalInfo, FoodCategory
    food_recipe.py          # FoodRecipe, RecipeIngredient
    food_inventory.py       # FridgeItem — fridge/freezer/pantry inventory
    health_record.py        # HealthRecord, BloodPressure, Glucose, HeartRate, Sleep
    health_incident.py      # HealthIncident — illness/injury/pain/fatigue/stress events
    exercise.py             # ExerciseEntry, MealLog
  database/
    __init__.py
    config.py               # Reads DB path from config/local.json
    connection.py           # DatabaseConnection context manager
    schema.py               # CREATE TABLE statements (idempotent)
    repositories/
      __init__.py
      base_repository.py    # Abstract CRUD base class
      human_repository.py
      food_repository.py    # FoodItemRepository, FoodRecipeRepository
      health_repository.py  # HealthRecordRepository
      meal_repository.py    # MealLogRepository
      exercise_repository.py # ExerciseRepository
      fridge_repository.py  # FridgeInventoryRepository
      incident_repository.py # HealthIncidentRepository
  llm/
    __init__.py
    base.py                 # BaseLLMProvider abstract class
    config.py               # Reads API key from secrets/<provider>_api_key.txt
    gemini.py               # GeminiProvider (direct Gemini SDK, pre-agent)
  agents/
    __init__.py             # Exports MainAgent (the only public interface)
    base_agent.py           # BaseAgent: LLM loop, tool calling, memory management
    main_agent.py           # MainAgent — user's only interface; orchestrates subagents
    nutrition_agent.py      # NutritionAgent — food, meals, inventory, dietary advice
    health_agent.py         # HealthAgent — metrics + health incidents (NL + structured)
    exercise_agent.py       # ExerciseAgent — exercise logging, history, recommendations
    shopping_agent.py       # ShoppingAgent — personalised weekly shopping lists
    memory/
      persistent_memory.py  # JSON-backed per-agent conversation history
    tools/
      __init__.py
      database_tools.py     # Read-only DB query tools + fridge + incident + exercise analysis
      entry_tools.py        # Structured data-entry tools (health, meal, exercise, fridge, incident)
      parsing_tools.py      # NL text → Pydantic model → DB; fridge + incident NL parsing
      shopping_tools.py     # Shopping context aggregator + seasonal produce guide

tests/
  data_models/              # Pydantic model validation tests
  database/
    test_fridge_repository.py     # FridgeInventoryRepository + FridgeItem property tests
    test_incident_repository.py   # HealthIncidentRepository full CRUD + model tests
    ...                           # Other repository and connection tests (use tmp_path)
  llm/                      # LLM base class tests
  agents/
    test_memory.py                      # PersistentMemory unit tests (no LLM)
    test_tools.py                       # Tool factory integration tests (real DB, no LLM)
    test_fridge_tools.py                # Fridge entry, DB query, and dietary context tool tests
    test_shopping_tools.py              # Shopping context, seasonal data, and gap analysis tests
    test_incident_and_exercise_tools.py # Incident entry/query + exercise analysis tool tests
    test_agents.py                      # Agent smoke tests (mocked LLM)
```

## Multi-Agent System

### Design

- **MainAgent** is the sole interface for callers. It orchestrates four specialist subagents
  as LangChain tools.
- Each subagent has its own **persistent memory** (JSON file in `data/memory/`) and its own
  set of domain-specific tools.
- **Two data-entry paths** exist for every domain:
  1. **Structured** — caller provides explicit field values (tool functions in `entry_tools.py`)
  2. **Natural language** — caller writes free text; Gemini parses it into a Pydantic model
     (tools in `parsing_tools.py` using `llm.with_structured_output()`)
- The **agent loop** is manual (no AgentExecutor): invoke LLM → execute tool calls → loop
  until plain-text response. Max 10 iterations per call.

### Usage

```python
from nira_backend.agents import MainAgent

with MainAgent() as nira:
    # Family + health
    nira.chat("Add John Doe to the family, male, born 1985-03-20, 80kg, 178cm")
    nira.chat("John's blood pressure was 125/82 this morning")

    # Health incidents (non-metric events)
    nira.chat("Alice has been getting shoulder pain after working long hours at her desk")
    nira.chat("John had a fever and sore throat since yesterday")

    # Meal logging
    nira.chat("Jane had a banana and oatmeal for breakfast, about 300g total")

    # Exercise + recommendations
    nira.chat("I went for a 5km run, took 28 minutes, felt vigorous")
    nira.chat("Can you give me an exercise recommendation for this week?")

    # Fridge / inventory
    nira.chat("I bought 6 eggs, 500g broccoli, and 1 litre oat milk")
    nira.chat("Put 2kg chicken breast in the freezer, expires 2026-06-01")
    nira.chat("What's in the fridge?")
    nira.chat("Any items expiring soon?")
    nira.chat("I used all the broccoli")

    # Dietary suggestions
    nira.chat("What should John eat today based on his recent habits?")
    nira.chat("Suggest meals for Jane — check what we have in the fridge")

    # Shopping list
    nira.chat("Generate a shopping list for the family this week")
```

### Available Tools per Agent

| Agent | Structured Tools | NL Parsing Tools | Query / Advisory Tools |
|-------|-----------------|-----------------|------------------------|
| NutritionAgent | log_meal, add_food_item, search_food_catalog, add_to_fridge, update_fridge_quantity, remove_from_fridge | parse_and_log_meal, parse_and_add_to_fridge | list_family_members, get_meal_history, list_fridge_contents, get_expiring_items, **get_dietary_context** |
| HealthAgent | log_blood_pressure, log_blood_glucose, log_heart_rate, log_sleep, **log_health_incident** | parse_and_log_health, **parse_and_log_incident** | list_family_members, get_health_history, **get_incident_history** |
| ExerciseAgent | log_exercise | parse_and_log_exercise | list_family_members, get_exercise_history, **get_exercise_analysis_context** |
| ShoppingAgent | — | — | list_family_members, **get_shopping_context**, **get_seasonal_foods** |
| MainAgent | add_family_member, list_family_members | — | get_todays_summary |

### Health Incident Flow

When a family member reports a non-metric health event (illness, injury, pain, fatigue, stress), `HealthAgent`:
1. Routes free-text descriptions through `parse_and_log_incident` — Gemini extracts:
   - `incident_type` (illness / injury / pain / fatigue / stress / other)
   - `body_part` (shoulder, head, knee, etc.)
   - `symptoms` (list of specific complaints)
   - `severity` (mild / moderate / severe)
   - `incident_date` (absolute date, resolved from relative references like "yesterday")
   - `notes` (cause, context, follow-up)
2. Persists to `health_incidents` table via `HealthIncidentRepository`
3. Past incidents are retrievable via `get_incident_history` for trend analysis

### Exercise Recommendation Flow

When asked for exercise recommendations, `ExerciseAgent`:
1. Calls `get_exercise_analysis_context(human_name, days=28)` — analyses 4-week window:
   - Total sessions, minutes, estimated calories
   - Activity type breakdown: cardio / strength / flexibility / sports (with % and missing gaps)
   - Intensity distribution: light / moderate / vigorous (with gap warnings)
   - Days since last session by type
   - Rest-day ratio and longest consecutive active streak
   - Last 7 days detail
2. Generates 3–5 specific, data-driven recommendations based on actual patterns
3. Flags missing exercise types, overtraining risks, and recovery gaps

### Shopping List Flow

When asked for a shopping list, `ShoppingAgent`:
1. Calls `get_shopping_context(human_names, days, include_fridge)` — aggregates:
   - Recent meal patterns (last 7 days by default) with qualitative nutritional gap analysis
   - Health conditions (elevated BP → low-sodium; high glucose → low-GI; poor sleep → magnesium-rich)
   - Seasonal produce guide for the current month (Northern Hemisphere)
   - Fridge/pantry inventory so it doesn't recommend items already in stock
2. Optionally calls `get_seasonal_foods` for a deeper seasonal guide
3. Generates a categorised list (Proteins / Vegetables / Fruits / Dairy / Pantry / Optional)
4. Each item includes a brief reason: nutritional gap, seasonal, health condition, or low stock
5. Ends with a short nutritional rationale explaining the key choices

### Dietary Suggestions Flow

When asked for food suggestions, `NutritionAgent`:
1. Calls `get_dietary_context(human_name, days, include_fridge)` — one tool call that bundles:
   - Recent meal history (default: 7 days)
   - Recent health metrics (BP, glucose, sleep)
   - Full fridge/pantry inventory with expiry warnings
2. Reasons over the combined context to produce personalised, specific meal suggestions
3. Prioritises ingredients expiring soon and considers health data (e.g. low-sodium if BP is elevated)

## Database Schema

Nine tables:

| Table | Purpose |
|-------|---------|
| `humans` | Family member profiles |
| `food_items` | Food catalog with nutritional info (per 100g) |
| `food_recipes` | Recipes with ingredients |
| `food_recipe_ingredients` | Recipe–food join table |
| `health_records` | BP, glucose, HR, sleep readings |
| `health_incidents` | Non-metric health events (illness, injury, pain, fatigue, stress) |
| `meal_logs` | What each person ate and when |
| `exercise_entries` | Exercise sessions per person |
| `fridge_inventory` | Household food inventory (fridge/freezer/pantry) |

### `health_incidents` columns

| Column | Type | Notes |
|--------|------|-------|
| `human_name` | TEXT | Affected family member |
| `incident_date` | TEXT | ISO date |
| `description` | TEXT | Summary of the event |
| `incident_type` | TEXT | `illness`, `injury`, `pain`, `fatigue`, `stress`, `other` |
| `severity` | TEXT | `mild`, `moderate`, `severe` — optional |
| `body_part` | TEXT | Affected body part — optional |
| `symptoms` | TEXT | JSON array of symptom strings |
| `notes` | TEXT | Extra context or cause — optional |

### `fridge_inventory` columns

| Column | Type | Notes |
|--------|------|-------|
| `food_name` | TEXT | Item name |
| `quantity` | REAL | Amount in `unit` |
| `unit` | TEXT | `g`, `kg`, `pieces`, `ml`, `l` |
| `location` | TEXT | `fridge`, `freezer`, `pantry`, `other` |
| `added_date` | TEXT | ISO date |
| `expiry_date` | TEXT | ISO date, optional |
| `notes` | TEXT | Free text, optional |

## Configuration (Gitignored Files)

### `config/local.json`
```json
{
    "database_path": "/home/pi/nira/nira_data.db",
    "data_dir": "/home/pi/nira/data"
}
```
Copy `config/local.example.json` as a starting point.
- `database_path` defaults to `nira_data.db` in CWD.
- `data_dir` defaults to `./data` in CWD (holds `memory/` and `entries/` subdirs).

### `secrets/gemini_api_key.txt`
Paste your Google Gemini API key (from https://aistudio.google.com/app/apikey).
Blank lines and `#` comment lines are ignored.

## Extending the System

### Adding a new subagent (e.g. MindfulnessAgent)
1. Create `src/nira_backend/agents/mindfulness_agent.py` extending `BaseAgent`.
2. Add domain tools to `tools/entry_tools.py` and `tools/parsing_tools.py`.
3. Add the agent as a tool in `MainAgent._make_tools()`.
4. Write tests in `tests/agents/`.

### Adding a new LLM provider
1. Create `src/nira_backend/llm/<provider>.py` subclassing `BaseLLMProvider`.
2. Export from `src/nira_backend/llm/__init__.py`.

## Running Tests

```bash
python -m pytest tests/ --no-cov -q   # quick summary
python -m pytest tests/ -v             # verbose with coverage
```

Current test count: **400 passing**.
