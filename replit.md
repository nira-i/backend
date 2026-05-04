# NIRA Backend

Backend component of the NIRA family health and food management system.

## Project Overview

A pure Python library (no web server) providing data models, SQLite database management,
a Gemini LLM integration, and a LangChain-based multi-agent system for tracking food,
meals, health metrics, and exercise for a family. Designed to run locally on a Raspberry Pi.
A future separate repo will add an API layer and frontend.

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
    health_record.py        # HealthRecord, BloodPressure, Glucose, HeartRate, Sleep
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
  llm/
    __init__.py
    base.py                 # BaseLLMProvider abstract class
    config.py               # Reads API key from secrets/<provider>_api_key.txt
    gemini.py               # GeminiProvider (direct Gemini SDK, pre-agent)
  agents/
    __init__.py             # Exports MainAgent (the only public interface)
    base_agent.py           # BaseAgent: LLM loop, tool calling, memory management
    main_agent.py           # MainAgent — user's only interface; orchestrates subagents
    nutrition_agent.py      # NutritionAgent — food, meals, nutritional analysis
    health_agent.py         # HealthAgent — blood pressure, glucose, HR, sleep
    exercise_agent.py       # ExerciseAgent — exercise sessions and history
    memory/
      persistent_memory.py  # JSON-backed per-agent conversation history
    tools/
      database_tools.py     # Read-only DB query tools (shared across agents)
      entry_tools.py        # Structured data-entry tools (health, meal, exercise)
      parsing_tools.py      # NL text → Pydantic model → DB (via Gemini)

tests/
  data_models/              # Pydantic model validation tests
  database/                 # Repository and connection tests (uses tmp_path)
  llm/                      # LLM base class tests
  agents/
    test_memory.py          # PersistentMemory unit tests (no LLM)
    test_tools.py           # Tool factory integration tests (real DB, no LLM)
    test_agents.py          # Agent smoke tests (mocked LLM)
```

## Multi-Agent System

### Design

- **MainAgent** is the sole interface for callers. It orchestrates three specialist subagents
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
    # Structured intent — MainAgent routes to the right subagent automatically
    print(nira.chat("Add John Doe to the family, male, born 1985-03-20, 80kg, 178cm"))
    print(nira.chat("John's blood pressure was 125/82 this morning"))
    print(nira.chat("Log that Jane had a banana and oatmeal for breakfast, about 300g total"))
    print(nira.chat("I went for a 5km run, took 28 minutes, felt vigorous"))
    print(nira.chat("How is John's blood pressure trending this month?"))
```

### Available Tools per Agent

| Agent | Structured Tools | NL Parsing Tools | Query Tools |
|-------|-----------------|-----------------|-------------|
| NutritionAgent | log_meal, add_food_item, search_food_catalog | parse_and_log_meal | list_family_members, get_meal_history |
| HealthAgent | log_blood_pressure, log_blood_glucose, log_heart_rate, log_sleep | parse_and_log_health | list_family_members, get_health_history |
| ExerciseAgent | log_exercise | parse_and_log_exercise | list_family_members, get_exercise_history |
| MainAgent | add_family_member, list_family_members | — | get_todays_summary |

## Database Schema

Five core tables + two new tables:

| Table | Purpose |
|-------|---------|
| `humans` | Family member profiles |
| `food_items` | Food catalog with nutritional info (per 100g) |
| `food_recipes` | Recipes with ingredients |
| `food_recipe_ingredients` | Recipe–food join table |
| `health_records` | BP, glucose, HR, sleep readings |
| `meal_logs` | What each person ate and when |
| `exercise_entries` | Exercise sessions per person |

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
