"""Tests for LLM base classes and data models."""

import pytest
from pydantic import ValidationError

from nira_backend.llm.base import LLMMessage, LLMResponse, MessageRole


class TestLLMMessage:
    def test_create_user_message(self) -> None:
        msg = LLMMessage(role=MessageRole.USER, content="Hello")
        assert msg.role == MessageRole.USER
        assert msg.content == "Hello"

    def test_create_system_message(self) -> None:
        msg = LLMMessage(role=MessageRole.SYSTEM, content="You are a health assistant.")
        assert msg.role == MessageRole.SYSTEM

    def test_create_assistant_message(self) -> None:
        msg = LLMMessage(role=MessageRole.ASSISTANT, content="Here is the answer.")
        assert msg.role == MessageRole.ASSISTANT

    def test_empty_content_raises(self) -> None:
        with pytest.raises(ValidationError):
            LLMMessage(role=MessageRole.USER, content="")

    def test_invalid_role_raises(self) -> None:
        with pytest.raises(ValidationError):
            LLMMessage(role="admin", content="Hello")  # type: ignore[arg-type]


class TestLLMResponse:
    def test_create_minimal(self) -> None:
        resp = LLMResponse(content="Answer", model="gemini-2.5-flash")
        assert resp.content == "Answer"
        assert resp.model == "gemini-2.5-flash"
        assert resp.input_tokens is None
        assert resp.output_tokens is None
        assert resp.finish_reason is None

    def test_create_full(self) -> None:
        resp = LLMResponse(
            content="Answer",
            model="gemini-2.5-flash",
            input_tokens=50,
            output_tokens=100,
            finish_reason="STOP",
        )
        assert resp.input_tokens == 50
        assert resp.output_tokens == 100
        assert resp.finish_reason == "STOP"


class TestMessageRole:
    def test_all_roles_exist(self) -> None:
        assert MessageRole.USER == "user"
        assert MessageRole.SYSTEM == "system"
        assert MessageRole.ASSISTANT == "assistant"
