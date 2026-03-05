# NIRA Backend

Backend component of the NIRA family food and health management application.

## Project Overview

A pure Python library (no web server) providing data models, SQLite database management,
and LLM (Google Gemini) integration for tracking food, nutrition, and health metrics
for a family. Designed to run locally on a Raspberry Pi.

## Architecture

- **Language**: Python 3.11
- **Build System**: setuptools (pyproject.toml), managed via uv
- **Key Dependencies**: `pydantic`, `numpy`, `google-generativeai`
- **Dev Dependencies**: `pytest`, `pytest-cov`, `black`, `ruff`, `mypy`
- **Database**: SQLite (via built-in `sqlite3`) — lightweight, no server required

## Project Structure

```
src/nira_backend/
  __init__.py
  data_models/
    __init__.py
    human.py              # Human model with BMI, age
    measurements.py       # Weight, Length, BodyShapeMeasurements
    food_item.py          # FoodItem, NutritionalInfo, FoodCategory
    food_recipe.py        # FoodRecipe, RecipeIngredient
    health_record.py      # HealthRecord, BloodPressure, Glucose, HeartRate, Sleep
  database/
    __init__.py
    config.py             # Reads DB path from config/local.json
    connection.py         # DatabaseConnection context manager
    schema.py             # CREATE TABLE statements (idempotent)
    repositories/
      __init__.py
      base_repository.py  # Abstract CRUD base class
      human_repository.py
      food_repository.py  # FoodItemRepository, FoodRecipeRepository
      health_repository.py
  llm/
    __init__.py
    base.py               # BaseLLMProvider abstract class, LLMMessage, LLMResponse
    config.py             # Reads API key from secrets/<provider>_api_key.txt
    gemini.py             # GeminiProvider (extends BaseLLMProvider)

tests/
  data_models/            # 69 original + new food/health tests
  database/               # Repository and connection tests (uses tmp_path)
  llm/                    # LLM base class tests
```

## Configuration (Gitignored Files)

### Database path — `config/local.json`
```json
{ "database_path": "/home/pi/nira/nira_data.db" }
```
Copy `config/local.example.json` as a starting point. Falls back to `nira_data.db` in CWD.

### Gemini API key — `secrets/gemini_api_key.txt`
Paste your Google Gemini API key (from https://aistudio.google.com/app/apikey) into this file.

## Extending the LLM Module

To add a new LLM provider (e.g. OpenAI):
1. Create `src/nira_backend/llm/openai.py`
2. Subclass `BaseLLMProvider` and implement `generate`, `chat`, `stream_chat`, `provider_name`
3. Export from `src/nira_backend/llm/__init__.py`

## Running Tests

The "Run Tests" workflow runs `python -m pytest tests/ -v --no-cov`.

```bash
python -m pytest tests/ --no-cov -q   # quick
python -m pytest tests/ -v             # verbose with coverage
```
