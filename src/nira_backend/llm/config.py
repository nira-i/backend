"""LLM configuration and API key loader.

API keys are stored in provider-specific files under the ``secrets/`` directory.
The entire ``secrets/`` directory is listed in ``.gitignore`` and must never
be committed to source control.

Supported secret files
----------------------
- ``secrets/gemini_api_key.txt`` — Google Gemini API key

Example ``secrets/gemini_api_key.txt``::

    AIzaSy...your-key-here...

The file should contain only the key, with optional surrounding whitespace.
"""

from pathlib import Path

_SECRETS_DIR = Path("secrets")


def get_api_key(provider: str) -> str:
    """
    Read and return the API key for the given provider.

    The key is read from ``secrets/<provider>_api_key.txt``.

    Args:
        provider: Provider identifier, e.g. ``"gemini"``.

    Returns:
        The API key as a string (whitespace stripped).

    Raises:
        FileNotFoundError: If the secrets file does not exist.
        ValueError: If the secrets file is empty.
    """
    key_file = _SECRETS_DIR / f"{provider}_api_key.txt"
    if not key_file.exists():
        raise FileNotFoundError(
            f"API key file not found: {key_file}\n"
            f"Create '{key_file}' and paste your {provider} API key inside."
        )
    key = key_file.read_text(encoding="utf-8").strip()
    if not key:
        raise ValueError(
            f"API key file is empty: {key_file}\n"
            f"Paste your {provider} API key into '{key_file}'."
        )
    return key
