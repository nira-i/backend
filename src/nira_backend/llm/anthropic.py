"""Anthropic Claude LLM provider implementation."""

from typing import AsyncIterator, Optional

from nira_backend.llm.base import BaseLLMProvider, LLMMessage, LLMResponse, MessageRole
from nira_backend.llm.config import get_api_key

_DEFAULT_MODEL = "claude-3-5-haiku-20241022"


class AnthropicProvider(BaseLLMProvider):
    """
    Anthropic Claude implementation of :class:`~nira_backend.llm.base.BaseLLMProvider`.

    Requires ``anthropic`` to be installed and a valid API key available via the
    ``ANTHROPIC_API_KEY`` environment variable or ``secrets/anthropic_api_key.txt``.

    Anthropic separates system messages from the conversation turns; any
    ``MessageRole.SYSTEM`` messages in the ``messages`` list are merged into the
    top-level ``system`` parameter automatically.

    Args:
        model_name: Claude model to use. Defaults to ``"claude-3-5-haiku-20241022"``.
        system_prompt: Optional system instruction sent with every request.
        temperature: Sampling temperature (0.0–1.0).
        max_output_tokens: Maximum tokens in the response.
        api_key: Override the API key loaded from the environment / secrets file.

    Example::

        provider = AnthropicProvider()
        response = provider.generate("What foods are high in protein?")
        print(response.content)
    """

    def __init__(
        self,
        model_name: str = _DEFAULT_MODEL,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_output_tokens: int = 2048,
        api_key: Optional[str] = None,
    ) -> None:
        super().__init__(
            model_name=model_name,
            system_prompt=system_prompt,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )
        self._api_key = api_key or get_api_key("anthropic")
        self._client = self._build_client()

    @property
    def provider_name(self) -> str:
        return "Anthropic"

    def _build_client(self) -> object:
        try:
            import anthropic
        except ImportError as exc:
            raise ImportError(
                "anthropic is not installed. "
                "Run: pip install anthropic"
            ) from exc

        return anthropic.Anthropic(api_key=self._api_key)

    def _build_turns(
        self, messages: list[LLMMessage]
    ) -> tuple[str, list[dict[str, str]]]:
        """
        Split LLMMessages into a system string and a list of user/assistant turns.

        Anthropic's API keeps system content separate from the ``messages`` list.
        Any ``SYSTEM`` role messages are concatenated and returned as the first
        element; the remaining turns form the second element.

        Returns:
            ``(system_text, turns)`` where ``turns`` is a list of
            ``{"role": ..., "content": ...}`` dicts.
        """
        system_parts: list[str] = []
        if self._system_prompt:
            system_parts.append(self._system_prompt)

        turns: list[dict[str, str]] = []
        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system_parts.append(msg.content)
            elif msg.role == MessageRole.USER:
                turns.append({"role": "user", "content": msg.content})
            else:
                turns.append({"role": "assistant", "content": msg.content})

        return "\n\n".join(system_parts), turns

    def generate(self, prompt: str) -> LLMResponse:
        """
        Generate text from a single prompt.

        Args:
            prompt: User prompt to send to Claude.

        Returns:
            :class:`LLMResponse` containing the generated text.
        """
        import anthropic

        assert isinstance(self._client, anthropic.Anthropic)
        kwargs: dict = {
            "model": self._model_name,
            "max_tokens": self._max_output_tokens,
            "temperature": self._temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if self._system_prompt:
            kwargs["system"] = self._system_prompt

        response = self._client.messages.create(**kwargs)
        return self._parse_response(response)

    def chat(self, messages: list[LLMMessage]) -> LLMResponse:
        """
        Send a multi-turn conversation to Claude.

        System messages are extracted and passed as the ``system`` parameter;
        user and assistant turns form the ``messages`` list.

        Args:
            messages: Ordered list of conversation messages.

        Returns:
            :class:`LLMResponse` with the assistant reply.
        """
        import anthropic

        assert isinstance(self._client, anthropic.Anthropic)
        system_text, turns = self._build_turns(messages)

        kwargs: dict = {
            "model": self._model_name,
            "max_tokens": self._max_output_tokens,
            "temperature": self._temperature,
            "messages": turns,
        }
        if system_text:
            kwargs["system"] = system_text

        response = self._client.messages.create(**kwargs)
        return self._parse_response(response)

    async def stream_chat(
        self, messages: list[LLMMessage]
    ) -> AsyncIterator[str]:
        """
        Stream the assistant response from Claude token-by-token.

        Args:
            messages: Ordered list of conversation messages.

        Yields:
            Successive text chunks as they arrive.
        """
        import anthropic

        assert isinstance(self._client, anthropic.Anthropic)
        system_text, turns = self._build_turns(messages)

        kwargs: dict = {
            "model": self._model_name,
            "max_tokens": self._max_output_tokens,
            "temperature": self._temperature,
            "messages": turns,
        }
        if system_text:
            kwargs["system"] = system_text

        with self._client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                yield text

    @staticmethod
    def _parse_response(response: object) -> LLMResponse:
        """Extract LLMResponse fields from an Anthropic Message object."""
        content_blocks = getattr(response, "content", [])
        text = "".join(
            getattr(block, "text", "") for block in content_blocks
        )

        model_name: str = getattr(response, "model", _DEFAULT_MODEL)
        finish_reason: Optional[str] = getattr(response, "stop_reason", None)

        input_tokens: Optional[int] = None
        output_tokens: Optional[int] = None
        usage = getattr(response, "usage", None)
        if usage:
            input_tokens = getattr(usage, "input_tokens", None)
            output_tokens = getattr(usage, "output_tokens", None)

        return LLMResponse(
            content=text,
            model=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            finish_reason=finish_reason,
        )
