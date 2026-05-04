"""Tests for PersistentMemory — no LLM required."""

from pathlib import Path

import pytest

from nira_backend.agents.memory.persistent_memory import PersistentMemory


@pytest.fixture
def memory(tmp_path: Path) -> PersistentMemory:
    return PersistentMemory(agent_name="test_agent", max_exchanges=3, data_dir=tmp_path)


class TestPersistentMemoryBasics:
    def test_initial_state_is_empty(self, memory: PersistentMemory) -> None:
        assert memory.message_count == 0
        assert memory.exchange_count == 0
        assert memory.get_context_messages() == []

    def test_add_exchange_increments_counts(self, memory: PersistentMemory) -> None:
        memory.add_exchange("Hello", "Hi there!")
        assert memory.message_count == 2
        assert memory.exchange_count == 1

    def test_add_multiple_exchanges(self, memory: PersistentMemory) -> None:
        memory.add_exchange("msg 1", "reply 1")
        memory.add_exchange("msg 2", "reply 2")
        assert memory.message_count == 4
        assert memory.exchange_count == 2

    def test_get_context_messages_returns_langchain_messages(
        self, memory: PersistentMemory
    ) -> None:
        from langchain_core.messages import AIMessage, HumanMessage

        memory.add_exchange("Hello", "Hi!")
        messages = memory.get_context_messages()
        assert len(messages) == 2
        assert isinstance(messages[0], HumanMessage)
        assert isinstance(messages[1], AIMessage)
        assert messages[0].content == "Hello"
        assert messages[1].content == "Hi!"

    def test_get_context_messages_order_is_preserved(
        self, memory: PersistentMemory
    ) -> None:
        memory.add_exchange("first", "first reply")
        memory.add_exchange("second", "second reply")
        messages = memory.get_context_messages()
        assert messages[0].content == "first"
        assert messages[1].content == "first reply"
        assert messages[2].content == "second"
        assert messages[3].content == "second reply"


class TestPersistentMemoryCapLimit:
    def test_max_exchanges_is_respected(self, tmp_path: Path) -> None:
        mem = PersistentMemory(agent_name="capped", max_exchanges=2, data_dir=tmp_path)
        mem.add_exchange("a", "A")
        mem.add_exchange("b", "B")
        mem.add_exchange("c", "C")
        assert mem.exchange_count == 2
        assert mem.message_count == 4

    def test_oldest_exchange_is_dropped_when_cap_exceeded(
        self, tmp_path: Path
    ) -> None:
        mem = PersistentMemory(agent_name="cap2", max_exchanges=2, data_dir=tmp_path)
        mem.add_exchange("old", "old reply")
        mem.add_exchange("newer", "newer reply")
        mem.add_exchange("newest", "newest reply")
        messages = mem.get_context_messages()
        contents = [m.content for m in messages]
        assert "old" not in contents
        assert "newer" in contents
        assert "newest" in contents


class TestPersistentMemoryPersistence:
    def test_memory_survives_reload(self, tmp_path: Path) -> None:
        mem1 = PersistentMemory(agent_name="persist", max_exchanges=5, data_dir=tmp_path)
        mem1.add_exchange("question", "answer")

        mem2 = PersistentMemory(agent_name="persist", max_exchanges=5, data_dir=tmp_path)
        assert mem2.message_count == 2
        messages = mem2.get_context_messages()
        assert messages[0].content == "question"
        assert messages[1].content == "answer"

    def test_json_file_is_created(self, tmp_path: Path) -> None:
        mem = PersistentMemory(agent_name="myagent", max_exchanges=5, data_dir=tmp_path)
        mem.add_exchange("test", "response")
        expected_path = tmp_path / "memory" / "myagent.json"
        assert expected_path.exists()

    def test_clear_removes_history_and_file(self, tmp_path: Path) -> None:
        mem = PersistentMemory(agent_name="clr", max_exchanges=5, data_dir=tmp_path)
        mem.add_exchange("x", "y")
        file_path = tmp_path / "memory" / "clr.json"
        assert file_path.exists()

        mem.clear()
        assert mem.message_count == 0
        assert not file_path.exists()

    def test_clear_then_add_works_correctly(self, tmp_path: Path) -> None:
        mem = PersistentMemory(agent_name="clr2", max_exchanges=5, data_dir=tmp_path)
        mem.add_exchange("before", "before reply")
        mem.clear()
        mem.add_exchange("after", "after reply")
        assert mem.exchange_count == 1
        assert mem.get_context_messages()[0].content == "after"

    def test_separate_agents_have_separate_files(self, tmp_path: Path) -> None:
        mem_a = PersistentMemory(agent_name="alpha", max_exchanges=5, data_dir=tmp_path)
        mem_b = PersistentMemory(agent_name="beta", max_exchanges=5, data_dir=tmp_path)
        mem_a.add_exchange("from alpha", "reply alpha")
        mem_b.add_exchange("from beta", "reply beta")

        assert (tmp_path / "memory" / "alpha.json").exists()
        assert (tmp_path / "memory" / "beta.json").exists()

        loaded_a = PersistentMemory(agent_name="alpha", max_exchanges=5, data_dir=tmp_path)
        loaded_b = PersistentMemory(agent_name="beta", max_exchanges=5, data_dir=tmp_path)
        assert loaded_a.get_context_messages()[0].content == "from alpha"
        assert loaded_b.get_context_messages()[0].content == "from beta"


class TestPersistentMemoryEdgeCases:
    def test_corrupt_json_file_resets_gracefully(self, tmp_path: Path) -> None:
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir(parents=True)
        bad_file = mem_dir / "broken.json"
        bad_file.write_text("{{not valid json", encoding="utf-8")

        mem = PersistentMemory(agent_name="broken", max_exchanges=5, data_dir=tmp_path)
        assert mem.message_count == 0

    def test_unicode_content_is_preserved(self, tmp_path: Path) -> None:
        mem = PersistentMemory(agent_name="uni", max_exchanges=5, data_dir=tmp_path)
        mem.add_exchange("こんにちは", "Héllo wörld 🌍")
        loaded = PersistentMemory(agent_name="uni", max_exchanges=5, data_dir=tmp_path)
        msgs = loaded.get_context_messages()
        assert msgs[0].content == "こんにちは"
        assert msgs[1].content == "Héllo wörld 🌍"
