"""NIRA multi-agent system.

The only class external code needs to import is :class:`MainAgent`.
All specialist agents are managed internally by it.

Quick start::

    from nira_backend.agents import MainAgent

    with MainAgent() as nira:
        response = nira.chat("Log that John had oatmeal for breakfast, about 200g")
        print(response)
"""

from nira_backend.agents.main_agent import MainAgent

__all__ = ["MainAgent"]
