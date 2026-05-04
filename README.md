# NIRA Backend

Backend for the NIRA family health and food management system.

NIRA is a local-first Python library — no web server, no cloud dependency — designed to run on a Raspberry Pi. It provides a conversational multi-agent system that lets a family track health metrics, meals, exercise, food inventory, and non-metric health events through natural language.

---

## Features

- **Multi-agent architecture** — one `MainAgent` entry point that orchestrates four specialist subagents (Nutrition, Health, Exercise, Shopping)
- **Natural language input** — any piece of data can be entered in plain text; Gemini parses it into structured records automatically
- **Health metric tracking** — blood pressure, blood glucose, heart rate, sleep
- **Health incident logging** — illnesses, injuries, pain episodes, fatigue, stress (with body part, symptoms, severity)
- **Exercise tracking & recommendations** — session logging plus 4-week analysis covering frequency, activity-type balance, intensity distribution, and rest patterns
- **Meal logging** — food entries with portion sizes and meal types
- **Fridge / pantry inventory** — stock levels, locations, expiry tracking
- **Dietary suggestions** — personalised meal ideas based on recent meals, health data, and current fridge contents
- **Shopping list generation** — categorised list with reasoning per item, driven by nutritional gaps, health conditions, and seasonal produce
- **Persistent agent memory** — each agent remembers the last 20 exchanges (JSON, stays on device)
- **SQLite database** — lightweight, no server required

---

## Architecture

```
src/nira_backend/
├── config.py                    # Central config loader
├── data_models/                 # Pydantic v2 models
│   ├── human.py                 # Family member profile
│   ├── health_record.py         # BP, glucose, HR, sleep
│   ├── health_incident.py       # Illness / injury / pain / fatigue / stress events
│   ├── exercise.py              # Exercise sessions + meal logs
│   ├── food_item.py             # Food catalog with nutritional info
│   ├── food_recipe.py           # Recipes and ingredients
│   └── food_inventory.py        # Fridge / freezer / pantry items
├── database/
│   ├── connection.py            # SQLite connection context manager
│   ├── schema.py                # CREATE TABLE statements (idempotent)
│   └── repositories/            # One repository class per model
├── llm/
│   └── config.py                # Reads API key from secrets/gemini_api_key.txt
└── agents/
    ├── main_agent.py            # Sole public interface — orchestrates subagents
    ├── nutrition_agent.py       # Food, meals, inventory, dietary suggestions
    ├── health_agent.py          # Health metrics + incident logging
    ├── exercise_agent.py        # Exercise logging, history, recommendations
    ├── shopping_agent.py        # Weekly shopping list generation
    ├── base_agent.py            # Shared LLM loop, tool execution, memory
    ├── memory/
    │   └── persistent_memory.py # JSON-backed per-agent conversation history
    └── tools/
        ├── database_tools.py    # Read-only query tools + exercise analysis
        ├── entry_tools.py       # Structured data-entry tools
        ├── parsing_tools.py     # Natural language → Pydantic → DB tools
        └── shopping_tools.py    # Shopping context + seasonal produce guide
```

---

## Stack

| Concern | Choice |
|---------|--------|
| Language | Python 3.11 |
| Data models | Pydantic v2 |
| Database | SQLite (built-in `sqlite3`) |
| Agent framework | LangChain |
| LLM | Google Gemini 2.0 Flash (`langchain-google-genai`) |
| Package manager | `uv` |
| Testing | `pytest` |

---

## Quick Start

### 1 — Clone and install

```bash
git clone https://github.com/nira-i/backend.git
cd backend
uv sync
```

### 2 — Add your Gemini API key

Get a key at [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey), then:

```bash
mkdir -p secrets
echo "YOUR_API_KEY_HERE" > secrets/gemini_api_key.txt
```

### 3 — Configure paths (optional)

Copy the example config and edit it:

```bash
cp config/local.example.json config/local.json
```

```json
{
    "database_path": "/home/pi/nira/nira_data.db",
    "data_dir": "/home/pi/nira/data"
}
```

Both values default to the current working directory if the file is absent.

### 4 — Run the tests

```bash
python -m pytest tests/ --no-cov -q
```

Expected: **400 passed**.

### 5 — Start a conversation

```python
from nira_backend.agents import MainAgent

with MainAgent() as nira:
    nira.chat("Add Alice to the family, female, born 1988-04-12, 65kg, 168cm")
    nira.chat("Alice had shoulder pain today after working at her desk all day")
    nira.chat("She went for a 5km run this morning, took 28 minutes")
    nira.chat("Give Alice an exercise recommendation based on her recent activity")
    nira.chat("What should Alice eat for dinner given what we have in the fridge?")
    nira.chat("Generate a shopping list for the family this week")
```

---

## Agents & Tools

| Agent | Structured entry | Natural language entry | Query / advisory |
|-------|-----------------|----------------------|-----------------|
| **NutritionAgent** | `log_meal`, `add_food_item`, `add_to_fridge`, `update_fridge_quantity`, `remove_from_fridge` | `parse_and_log_meal`, `parse_and_add_to_fridge` | `get_meal_history`, `list_fridge_contents`, `get_expiring_items`, `get_dietary_context` |
| **HealthAgent** | `log_blood_pressure`, `log_blood_glucose`, `log_heart_rate`, `log_sleep`, `log_health_incident` | `parse_and_log_health`, `parse_and_log_incident` | `get_health_history`, `get_incident_history` |
| **ExerciseAgent** | `log_exercise` | `parse_and_log_exercise` | `get_exercise_history`, `get_exercise_analysis_context` |
| **ShoppingAgent** | — | — | `get_shopping_context`, `get_seasonal_foods` |
| **MainAgent** | `add_family_member` | — | `list_family_members`, `get_todays_summary` |

---

## Database Schema

| Table | Purpose |
|-------|---------|
| `humans` | Family member profiles |
| `food_items` | Food catalog (nutritional info per 100 g) |
| `food_recipes` | Recipes with ingredients |
| `food_recipe_ingredients` | Recipe–ingredient join table |
| `health_records` | BP, glucose, HR, sleep readings |
| `health_incidents` | Non-metric health events |
| `meal_logs` | What each person ate and when |
| `exercise_entries` | Exercise sessions per person |
| `fridge_inventory` | Household food stock |

---

## Testing with Dummy Data

See [`docs/testing_with_dummy_data.md`](docs/testing_with_dummy_data.md) for a step-by-step guide that seeds realistic family data and exercises every major feature without requiring any manual input.
