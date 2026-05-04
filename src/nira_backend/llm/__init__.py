"""LLM integration for the NIRA backend.

All LLM calls go through LangChain.  Use :func:`build_llm` to obtain a
provider-agnostic ``BaseChatModel`` for a given agent, configured from
``config/models.json``.
"""

from nira_backend.llm.factory import build_llm
from nira_backend.llm.model_config import get_model_for_agent, get_models_config, get_provider

__all__ = [
    "build_llm",
    "get_models_config",
    "get_provider",
    "get_model_for_agent",
]
