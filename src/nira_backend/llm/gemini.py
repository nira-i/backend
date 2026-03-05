"""Google Gemini LLM provider implementation."""

from typing import AsyncIterator, Optional

from nira_backend.llm.base import BaseLLMProvider, LLMMessage, LLMResponse, MessageRole
from nira_backend.llm.config import get_api_key

_DEFAULT_MODEL = "gemini-2.5-flash"


class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini implementation of :class:`~nira_backend.llm.base.BaseLLMProvider`.

    Requires ``google-generativeai`` to be installed and a valid API key at
    ``secrets/gemini_api_key.txt``.

    Args:
        model_name: Gemini model to use. Defaults to ``"gemini-2.5-flash"``.
        system_prompt: Optional system instruction sent with every request.
        temperature: Sampling temperature (0.0–1.0).
        max_output_tokens: Maximum tokens in the response.
        api_key: Override the API key loaded from the secrets file.

    Example::

        provider = GeminiProvider()
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
        self._api_key = api_key or get_api_key("gemini")
        self._client = self._build_client()

    @property
    def provider_name(self) -> str:
        return "Google Gemini"

    def _build_client(self) -> object:
        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise ImportError(
                "google-generativeai is not installed. "
                "Run: pip install google-generativeai"
            ) from exc

        genai.configure(api_key=self._api_key)

        generation_config = genai.types.GenerationConfig(
            temperature=self._temperature,
            max_output_tokens=self._max_output_tokens,
        )

        kwargs: dict[str, object] = {
            "model_name": self._model_name,
            "generation_config": generation_config,
        }
        if self._system_prompt:
            kwargs["system_instruction"] = self._system_prompt

        return genai.GenerativeModel(**kwargs)  # type: ignore[arg-type]

    def generate(self, prompt: str) -> LLMResponse:
        """
        Generate text from a single prompt.

        Args:
            prompt: User prompt to send to Gemini.

        Returns:
            :class:`LLMResponse` containing the generated text.
        """
        import google.generativeai as genai

        assert isinstance(self._client, genai.GenerativeModel)
        response = self._client.generate_content(prompt)
        return self._parse_response(response)

    def chat(self, messages: list[LLMMessage]) -> LLMResponse:
        """
        Send a multi-turn conversation to Gemini.

        System messages are incorporated into the model's system instruction
        when supported; otherwise prepended as user turns.

        Args:
            messages: Ordered list of conversation messages.

        Returns:
            :class:`LLMResponse` with the assistant reply.
        """
        import google.generativeai as genai

        assert isinstance(self._client, genai.GenerativeModel)
        history, last_message = self._build_history(messages)
        chat_session = self._client.start_chat(history=history)
        response = chat_session.send_message(last_message)
        return self._parse_response(response)

    async def stream_chat(
        self, messages: list[LLMMessage]
    ) -> AsyncIterator[str]:
        """
        Stream the assistant response from Gemini token-by-token.

        Args:
            messages: Ordered list of conversation messages.

        Yields:
            Successive text chunks as they arrive.
        """
        import google.generativeai as genai

        assert isinstance(self._client, genai.GenerativeModel)
        history, last_message = self._build_history(messages)
        chat_session = self._client.start_chat(history=history)
        response = chat_session.send_message(last_message, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text

    @staticmethod
    def _build_history(
        messages: list[LLMMessage],
    ) -> tuple[list[dict[str, str]], str]:
        """Convert LLMMessages to Gemini chat history format.

        Returns the history list (all messages except the last) and the
        content of the last user message to send.
        """
        if not messages:
            raise ValueError("messages list must not be empty")

        gemini_history: list[dict[str, str]] = []

        for msg in messages[:-1]:
            if msg.role == MessageRole.SYSTEM:
                continue
            role = "user" if msg.role == MessageRole.USER else "model"
            gemini_history.append({"role": role, "parts": msg.content})

        last = messages[-1]
        if last.role != MessageRole.USER:
            raise ValueError("The last message in a chat request must be a user message")

        return gemini_history, last.content

    @staticmethod
    def _parse_response(response: object) -> LLMResponse:
        """Extract LLMResponse fields from a Gemini GenerateContentResponse."""
        text: str = response.text  # type: ignore[attr-defined]
        model_name: str = getattr(response, "model", _DEFAULT_MODEL)

        input_tokens: Optional[int] = None
        output_tokens: Optional[int] = None
        finish_reason: Optional[str] = None

        usage = getattr(response, "usage_metadata", None)
        if usage:
            input_tokens = getattr(usage, "prompt_token_count", None)
            output_tokens = getattr(usage, "candidates_token_count", None)

        candidates = getattr(response, "candidates", None)
        if candidates:
            first = candidates[0]
            finish_reason = str(getattr(first, "finish_reason", None))

        return LLMResponse(
            content=text,
            model=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            finish_reason=finish_reason,
        )
