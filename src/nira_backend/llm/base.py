"""Abstract base class for LLM providers.

To add a new LLM provider (e.g. OpenAI, Anthropic):
1. Create a new file in this folder (e.g. ``openai.py``).
2. Subclass :class:`BaseLLMProvider` and implement all abstract methods.
3. Export the new class from ``__init__.py``.

The interface is intentionally minimal so that providers can be swapped
without changing calling code.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import AsyncIterator, Optional

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Role of a message in a conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class LLMMessage(BaseModel):
    """A single message in a conversation."""

    role: MessageRole = Field(description="Who sent the message")
    content: str = Field(min_length=1, description="Text content of the message")


class LLMResponse(BaseModel):
    """The response returned from an LLM provider."""

    content: str = Field(description="Text content of the response")
    model: str = Field(description="Name of the model that generated the response")
    input_tokens: Optional[int] = Field(
        default=None, description="Number of input tokens consumed (if reported)"
    )
    output_tokens: Optional[int] = Field(
        default=None, description="Number of output tokens generated (if reported)"
    )
    finish_reason: Optional[str] = Field(
        default=None, description="Reason the generation stopped (if reported)"
    )


class BaseLLMProvider(ABC):
    """
    Abstract base class for all LLM provider implementations.

    Subclasses must implement:
    - :meth:`generate` — single-turn text generation from a prompt.
    - :meth:`chat` — multi-turn conversation.
    - :meth:`stream_chat` — streaming version of :meth:`chat`.
    - :attr:`model_name` — the model identifier used by this provider.
    - :attr:`provider_name` — human-readable provider name.

    Args:
        model_name: The model to use for generation.
        system_prompt: Optional system-level instruction to prepend to every request.
        temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative).
        max_output_tokens: Maximum number of tokens in the response.
    """

    def __init__(
        self,
        model_name: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_output_tokens: int = 2048,
    ) -> None:
        self._model_name = model_name
        self._system_prompt = system_prompt
        self._temperature = temperature
        self._max_output_tokens = max_output_tokens

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable name of the LLM provider, e.g. 'Google Gemini'."""

    @property
    def model_name(self) -> str:
        """Model identifier used by this provider."""
        return self._model_name

    @property
    def system_prompt(self) -> Optional[str]:
        """System-level instruction prepended to every request."""
        return self._system_prompt

    @abstractmethod
    def generate(self, prompt: str) -> LLMResponse:
        """
        Generate text from a single prompt (no conversation history).

        Args:
            prompt: The user prompt to send to the model.

        Returns:
            :class:`LLMResponse` with the generated text.
        """

    @abstractmethod
    def chat(self, messages: list[LLMMessage]) -> LLMResponse:
        """
        Send a multi-turn conversation and return the assistant response.

        Args:
            messages: Ordered list of conversation messages.

        Returns:
            :class:`LLMResponse` with the generated text.
        """

    @abstractmethod
    async def stream_chat(
        self, messages: list[LLMMessage]
    ) -> AsyncIterator[str]:
        """
        Stream the assistant response token-by-token.

        Args:
            messages: Ordered list of conversation messages.

        Yields:
            Successive text chunks as they arrive from the provider.
        """
