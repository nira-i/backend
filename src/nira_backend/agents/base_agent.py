"""Abstract base class for all NIRA agents."""

from abc import ABC, abstractmethod
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from nira_backend.agents.memory.persistent_memory import PersistentMemory


class BaseAgent(ABC):
    """
    Abstract base for all NIRA agents.

    Subclasses provide a ``name``, a ``system_prompt``, and a list of
    LangChain ``@tool``-decorated callables.  The base class handles:

    - Building the full message list (system + history + current turn)
    - Running the tool-calling agent loop
    - Persisting the exchange to memory after each call

    Args:
        name: Unique agent identifier (also used as the memory filename).
        system_prompt: Instruction prepended to every conversation.
        tools: List of LangChain tool callables available to this agent.
        llm: A ``ChatGoogleGenerativeAI`` (or compatible) LangChain chat model.
        max_iterations: Safety cap on the agent loop iterations per call.
        memory_exchanges: How many past exchanges to retain in memory.
        data_dir: Override the data directory for memory storage (tests).
    """

    def __init__(
        self,
        name: str,
        system_prompt: str,
        tools: list[Any],
        llm: Any,
        max_iterations: int = 10,
        memory_exchanges: int = 20,
        data_dir: Any = None,
    ) -> None:
        self.name = name
        self._system_prompt = system_prompt
        self._tools = tools
        self._llm = llm
        self._max_iterations = max_iterations
        self._memory = PersistentMemory(
            agent_name=name,
            max_exchanges=memory_exchanges,
            data_dir=data_dir,
        )
        self._tool_map = {t.name: t for t in tools}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, user_message: str) -> str:
        """
        Process a user message and return the agent's response.

        Loads conversation history, runs the tool-calling loop, saves the
        exchange to memory, and returns the final text response.

        Args:
            user_message: The user's input text.

        Returns:
            The agent's text response.
        """
        messages: list[Any] = [SystemMessage(content=self._system_prompt)]
        messages.extend(self._memory.get_context_messages())
        messages.append(HumanMessage(content=user_message))

        response_text = self._run_agent_loop(messages)
        self._memory.add_exchange(user_message, response_text)
        return response_text

    def clear_memory(self) -> None:
        """Erase this agent's conversation history."""
        self._memory.clear()

    @property
    def memory_exchange_count(self) -> int:
        """Number of exchanges currently stored in memory."""
        return self._memory.exchange_count

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _run_agent_loop(self, messages: list[Any]) -> str:
        """
        Core agent loop: invoke LLM, execute any tool calls, repeat.

        Continues until the model returns a plain text response (no tool
        calls) or ``max_iterations`` is reached.
        """
        llm = (
            self._llm.bind_tools(self._tools)
            if self._tools
            else self._llm
        )

        for _ in range(self._max_iterations):
            response: AIMessage = llm.invoke(messages)
            messages.append(response)

            if not response.tool_calls:
                return response.content or ""

            for tc in response.tool_calls:
                result = self._call_tool(tc)
                messages.append(
                    ToolMessage(content=str(result), tool_call_id=tc["id"])
                )

        return (
            "I reached the maximum number of reasoning steps. "
            "Please try a more specific request."
        )

    def _call_tool(self, tool_call: dict[str, Any]) -> str:
        """Execute a single tool call and return its string result."""
        tool_name = tool_call["name"]
        tool_args = tool_call.get("args", {})
        tool = self._tool_map.get(tool_name)
        if tool is None:
            return f"Unknown tool: {tool_name}"
        try:
            result = tool.invoke(tool_args)
            return str(result)
        except Exception as exc:
            return f"Tool '{tool_name}' raised an error: {exc}"
