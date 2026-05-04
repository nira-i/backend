"""Load and resolve LLM provider / model configuration from config/models.json."""

import json
from pathlib import Path

_CONFIG_PATH = Path("config/models.json")

_FALLBACK: dict = {
    "active_provider": "gemini",
    "providers": {
        "gemini": {
            "models": {
                "main":      "gemini-2.0-flash",
                "nutrition": "gemini-2.0-flash",
                "health":    "gemini-2.0-flash",
                "exercise":  "gemini-2.0-flash",
                "shopping":  "gemini-2.0-flash",
            }
        }
    },
}

_SUPPORTED_PROVIDERS = {"gemini", "openai", "anthropic"}


def get_models_config() -> dict:
    """
    Return the full models config dict.

    Reads ``config/models.json`` relative to the current working directory.
    Falls back to Gemini defaults if the file is absent.

    Returns:
        Parsed configuration dictionary.

    Raises:
        ValueError: If ``active_provider`` is not one of the supported values.
    """
    if not _CONFIG_PATH.exists():
        return _FALLBACK

    config = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))

    provider = config.get("active_provider", "gemini")
    if provider not in _SUPPORTED_PROVIDERS:
        raise ValueError(
            f"Unsupported active_provider {provider!r} in {_CONFIG_PATH}. "
            f"Choose from: {', '.join(sorted(_SUPPORTED_PROVIDERS))}"
        )
    return config


def get_provider() -> str:
    """Return the currently active provider name (e.g. 'gemini')."""
    return get_models_config()["active_provider"]


def get_model_for_agent(agent_name: str) -> tuple[str, str]:
    """
    Return ``(provider, model_name)`` for the given agent.

    Falls back to the ``main`` model entry if the agent is not explicitly
    listed under the active provider's ``models`` section.

    Args:
        agent_name: One of ``'main'``, ``'nutrition'``, ``'health'``,
                    ``'exercise'``, or ``'shopping'``.

    Returns:
        A 2-tuple of ``(provider, model_name)``.
    """
    config = get_models_config()
    provider = config["active_provider"]
    models: dict[str, str] = (
        config.get("providers", {})
        .get(provider, {})
        .get("models", {})
    )
    model = models.get(agent_name) or models.get("main") or "gemini-2.0-flash"
    return provider, model
