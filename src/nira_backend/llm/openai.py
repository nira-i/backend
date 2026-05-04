"""OpenAI LLM provider implementation."""

from typing import AsyncIterator, Optional

from nira_backend.llm.base import BaseLLMProvider, LLMMessage, LLMResponse, MessageRole
from nira_backend.llm.config import get_api_key

_DEFAULT_MODEL = "gpt-4o-mini"


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI implementation of :class:`~nira_backend.llm.base.BaseLLMProvider`.

    Requires ``openai`` to be installed and a valid API key available via the
    ``OPENAI_API_KEY`` environment variable or ``secrets/openai_api_key.txt``.

    Args:
        model_name: OpenAI model to use. Defaults to ``"gpt-4o-mini"``.
        system_prompt: Optional system instruction sent with every request.
        temperature: Sampling temperature (0.0–2.0 for OpenAI models).
        max_output_tokens: Maximum tokens in the response.
        api_key: Override the API key loaded from the environment / secrets file.

    Example::

        provider = OpenAIProvider()
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
        self._api_key = api_key or get_api_key("openai")
        self._client = self._build_client()

    @property
    def provider_name(self) -> str:
        return "OpenAI"

    def _build_client(self) -> object:
        try:
            import openai
        except ImportError as exc:
            raise ImportError(
                "openai is not installed. "
                "Run: pip install openai"
            ) from exc

        return openai.OpenAI(api_key=self._api_key)

    def _build_messages(self, messages: list[LLMMessage]) -> list[dict[str, str]]:
        """Convert LLMMessages to the OpenAI messages format."""
        result: list[dict[str, str]] = []

        if self._system_prompt:
            result.append({"role": "system", "content": self._system_prompt})

        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                result.append({"role": "system", "content": msg.content})
            elif msg.role == MessageRole.USER:
                result.append({"role": "user", "content": msg.content})
            else:
                result.append({"role": "assistant", "content": msg.content})

        return result

    def generate(self, prompt: str) -> LLMResponse:
        """
        Generate text from a single prompt.

        Args:
            prompt: User prompt to send to the model.

        Returns:
            :class:`LLMResponse` containing the generated text.
        """
        import openai

        assert isinstance(self._client, openai.OpenAI)
        messages: list[dict[str, str]] = []
        if self._system_prompt:
            messages.append({"role": "system", "content": self._system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self._client.chat.completions.create(
            model=self._model_name,
            messages=messages,  # type: ignore[arg-type]
            temperature=self._temperature,
            max_tokens=self._max_output_tokens,
        )
        return self._parse_response(response)

    def chat(self, messages: list[LLMMessage]) -> LLMResponse:
        """
        Send a multi-turn conversation to the OpenAI chat endpoint.

        Args:
            messages: Ordered list of conversation messages.

        Returns:
            :class:`LLMResponse` with the assistant reply.
        """
        import openai

        assert isinstance(self._client, openai.OpenAI)
        response = self._client.chat.completions.create(
            model=self._model_name,
            messages=self._build_messages(messages),  # type: ignore[arg-type]
            temperature=self._temperature,
            max_tokens=self._max_output_tokens,
        )
        return self._parse_response(response)

    async def stream_chat(
        self, messages: list[LLMMessage]
    ) -> AsyncIterator[str]:
        """
        Stream the assistant response from OpenAI token-by-token.

        Args:
            messages: Ordered list of conversation messages.

        Yields:
            Successive text chunks as they arrive.
        """
        import openai

        assert isinstance(self._client, openai.OpenAI)
        stream = self._client.chat.completions.create(
            model=self._model_name,
            messages=self._build_messages(messages),  # type: ignore[arg-type]
            temperature=self._temperature,
            max_tokens=self._max_output_tokens,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield delta.content

    @staticmethod
    def _parse_response(response: object) -> LLMResponse:
        """Extract LLMResponse fields from an OpenAI ChatCompletion object."""
        choice = response.choices[0]  # type: ignore[attr-defined]
        content: str = choice.message.content or ""
        finish_reason: Optional[str] = getattr(choice, "finish_reason", None)
        model_name: str = getattr(response, "model", _DEFAULT_MODEL)

        input_tokens: Optional[int] = None
        output_tokens: Optional[int] = None
        usage = getattr(response, "usage", None)
        if usage:
            input_tokens = getattr(usage, "prompt_tokens", None)
            output_tokens = getattr(usage, "completion_tokens", None)

        return LLMResponse(
            content=content,
            model=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            finish_reason=finish_reason,
        )
