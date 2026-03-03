# NIRA Backend

A Python library providing data models for the NIRA backend application.

## Project Overview

This is a pure Python package (no web frontend or API server). It provides Pydantic-based data models for human physical attributes and body measurements.

## Architecture

- **Language**: Python 3.11
- **Build System**: setuptools (pyproject.toml)
- **Key Dependencies**: `pydantic`, `numpy`
- **Dev Dependencies**: `pytest`, `pytest-cov`, `black`, `ruff`, `mypy`

## Project Structure

```
src/nira_backend/
  __init__.py
  data_models/
    human.py          # Human model with BMI calculation
    measurements.py   # Weight, Length, BodyShapeMeasurements models
tests/
  data_models/
    test_human.py
    test_measurements.py
```

## Running Tests

The "Run Tests" workflow runs `python -m pytest tests/ -v --no-cov`.

You can also run manually:
```
python -m pytest tests/ -v --no-cov
```

## Package Installation

Installed via `pip install -e .` (editable mode) — the package is available as `nira_backend`.
