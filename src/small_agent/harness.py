"""Agent harness - orchestrates events, hooks, and LLM."""

import asyncio
from pathlib import Path
from typing import Any, Optional

from small_agent.config import Settings, HooksConfig
from small_agent.hooks.executor import HookExecutor, HarnessEvent
from small_agent.llm.base import LLMProvider, LLMResponse, LLMConfig


class AgentHarness:
    """Main agent harness that orchestrates events and hooks."""

    def __init__(
        self,
        settings: Settings,
        llm_provider: LLMProvider,
        working_dir: Path | None = None,
    ):
        self.settings = settings
        self.llm_provider = llm_provider
        self.hook_executor = HookExecutor(working_dir)
        self.conversation_history: list[dict[str, str]] = []

    def _get_hook_command(self, event_name: str) -> str | None:
        """Get hook command for an event."""
        hook_map = {
            "before_tool": self.settings.hooks.before_tool,
            "after_tool": self.settings.hooks.after_tool,
            "before_prompt": self.settings.hooks.before_prompt,
            "after_response": self.settings.hooks.after_response,
        }
        return hook_map.get(event_name)

    async def trigger_event(
        self,
        event_name: str,
        context: Optional[dict[str, Any]] = None,
    ) -> tuple[int, str, str]:
        """Trigger an event and run associated hooks.

        Args:
            event_name: Name of the event
            context: Event context data

        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        context = context or {}
        event = HarnessEvent(event_name, context)
        command = self._get_hook_command(event_name)

        if command:
            return await self.hook_executor.execute(command, event)

        return (0, "", "")

    async def process_prompt(
        self,
        prompt: str,
        options: Optional[dict[str, Any]] = None,
    ) -> LLMResponse:
        """Process a user prompt and generate response.

        Args:
            prompt: User input
            options: Generation options

        Returns:
            LLMResponse with generated content
        """
        options = options or {}

        # Trigger before_prompt hook
        await self.trigger_event("before_prompt", {"prompt": prompt})

        # Add user message to history
        self.conversation_history.append({"role": "user", "content": prompt})

        # Generate response
        response = await self.llm_provider.generate(
            messages=self.conversation_history,
            config=LLMConfig(
                provider_type=self.llm_provider.provider_type,
                model=self.settings.llm.bailian.get("model", "qwen-max"),
            ),
            **options,
        )

        # Add assistant response to history
        self.conversation_history.append(
            {"role": "assistant", "content": response.content}
        )

        # Trigger after_response hook
        await self.trigger_event(
            "after_response",
            {"response": response.content, "prompt": prompt},
        )

        return response

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history = []

    def get_history(self) -> list[dict[str, str]]:
        """Get conversation history."""
        return self.conversation_history.copy()
