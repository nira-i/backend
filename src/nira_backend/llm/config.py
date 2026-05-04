"""LLM configuration and API key loader.

API keys are resolved in this order for each provider:

1. The ``<PROVIDER>_API_KEY`` environment variable
   (e.g. ``GEMINI_API_KEY``, ``OPENAI_API_KEY``, ``ANTHROPIC_API_KEY``).
2. A provider-specific file under the ``secrets/`` directory
   (e.g. ``secrets/gemini_api_key.txt``).

The entire ``secrets/`` directory is listed in ``.gitignore`` and must never
be committed to source control.

Supported providers
-------------------
- ``gemini``    → ``GEMINI_API_KEY``    / ``secrets/gemini_api_key.txt``
- ``openai``    → ``OPENAI_API_KEY``    / ``secrets/openai_api_key.txt``
- ``anthropic`` → ``ANTHROPIC_API_KEY`` / ``secrets/anthropic_api_key.txt``

Example ``secrets/gemini_api_key.txt``::

    AIzaSy...your-key-here...

The file should contain only the key. Blank lines and lines starting with ``#``
are ignored, so you can add comments if needed.
"""

from pathlib import Path

_SECRETS_DIR = Path("secrets")

_PLACEHOLDER_PREFIXES = (
    "paste_your",
    "your_api_key",
    "your-api-key",
    "replace_this",
    "<",
)


def _looks_like_placeholder(line: str) -> bool:
    return any(line.lower().startswith(p) for p in _PLACEHOLDER_PREFIXES)


def get_api_key(provider: str) -> str:
    """
    Read and return the API key for the given provider.

    The key is resolved first from the ``<PROVIDER>_API_KEY`` environment
    variable, then from ``secrets/<provider>_api_key.txt``.  Blank lines and
    lines starting with ``#`` are skipped; the first remaining non-empty line
    is used as the key.

    Args:
        provider: Provider identifier — one of ``"gemini"``, ``"openai"``,
                  or ``"anthropic"``.

    Returns:
        The API key as a single-line string (no surrounding whitespace).

    Raises:
        FileNotFoundError: If neither the environment variable nor the secrets
                           file exists.
        ValueError: If no valid key line is found, or the key contains spaces.
    """
    env_var = f"{provider.upper()}_API_KEY"
    if env_key := __import__("os").environ.get(env_var):
        return env_key

    key_file = _SECRETS_DIR / f"{provider}_api_key.txt"
    if not key_file.exists():
        raise FileNotFoundError(
            f"API key not found for provider '{provider}'.\n"
            f"Set the {env_var} environment variable, or create '{key_file}' "
            "and paste your key inside."
        )

    for raw_line in key_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or _looks_like_placeholder(line):
            continue
        if " " in line or "\t" in line:
            raise ValueError(
                f"API key in '{key_file}' contains whitespace — "
                "make sure you pasted only the key with no extra text."
            )
        return line

    raise ValueError(
        f"No valid API key found in '{key_file}'.\n"
        f"Paste your {provider} API key into the file (one key per line)."
    )
