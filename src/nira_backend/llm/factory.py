"""LLM factory — instantiate the right LangChain chat model from config."""

from typing import Any

from nira_backend.llm.config import get_api_key
from nira_backend.llm.model_config import get_model_for_agent


def build_llm(
    agent_name: str,
    api_key: str | None = None,
    temperature: float = 0.3,
) -> Any:
    """
    Build and return a LangChain chat model for the given agent.

    The provider and model are read from ``config/models.json``.  The API key
    is resolved in this order:
      1. The ``api_key`` argument (explicit override — useful in tests).
      2. The ``<PROVIDER>_API_KEY`` environment variable.
      3. The ``secrets/<provider>_api_key.txt`` file.

    Supported providers
    -------------------
    - **gemini**    → ``ChatGoogleGenerativeAI`` (``langchain-google-genai``)
    - **openai**    → ``ChatOpenAI``             (``langchain-openai``)
    - **anthropic** → ``ChatAnthropic``          (``langchain-anthropic``)

    Args:
        agent_name:  Agent identifier matching a key in ``models.json``
                     (``'main'``, ``'nutrition'``, ``'health'``, ``'exercise'``,
                     ``'shopping'``).
        api_key:     Optional API key override for the active provider.
        temperature: Sampling temperature passed to the model.

    Returns:
        A LangChain ``BaseChatModel`` instance ready for use.

    Raises:
        ValueError: If the configured provider is not supported.
        FileNotFoundError: If no API key can be resolved for the provider.
    """
    provider, model = get_model_for_agent(agent_name)
    resolved_key = api_key or get_api_key(provider)

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=model,
            google_api_key=resolved_key,
            temperature=temperature,
        )

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model,
            api_key=resolved_key,
            temperature=temperature,
        )

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=model,
            api_key=resolved_key,
            temperature=temperature,
        )

    raise ValueError(
        f"Unsupported provider {provider!r}. "
        "Choose from: gemini, openai, anthropic"
    )
