"""LLM configuration and API key loader.

API keys are stored in provider-specific files under the ``secrets/`` directory.
The entire ``secrets/`` directory is listed in ``.gitignore`` and must never
be committed to source control.

Supported secret files
----------------------
- ``secrets/gemini_api_key.txt`` — Google Gemini API key

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

    The key is read from ``secrets/<provider>_api_key.txt``.  Blank lines and
    lines starting with ``#`` are skipped.  The first remaining non-empty line
    is used as the key.

    Args:
        provider: Provider identifier, e.g. ``"gemini"``.

    Returns:
        The API key as a single-line string (no surrounding whitespace).

    Raises:
        FileNotFoundError: If the secrets file does not exist.
        ValueError: If no valid key line is found or the key contains spaces.
    """
    key_file = _SECRETS_DIR / f"{provider}_api_key.txt"
    if not key_file.exists():
        raise FileNotFoundError(
            f"API key file not found: {key_file}\n"
            f"Create '{key_file}' and paste your {provider} API key inside."
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
