"""Main agent orchestration."""

import asyncio
from pathlib import Path
from typing import Any, Optional

from small_agent.config import Settings, load_settings, LLMConfig as SettingsLLMConfig
from small_agent.harness import AgentHarness
from small_agent.llm.base import LLMProvider, LLMResponse
from small_agent.llm.bailian import BailianProvider, BailianConfig


class Agent:
    """Main agent class that manages providers and harness."""

    def __init__(
        self,
        settings: Optional[Settings] = None,
        working_dir: Path | None = None,
    ):
        self.settings = settings or load_settings()
        self.working_dir = working_dir or Path.cwd()
        self._harness: Optional[AgentHarness] = None
        self._llm_provider: Optional[LLMProvider] = None

    @property
    def llm_provider(self) -> LLMProvider:
        """Get or create LLM provider based on settings."""
        if self._llm_provider is None:
            self._llm_provider = self._create_provider()
        return self._llm_provider

    def _create_provider(self) -> LLMProvider:
        """Create LLM provider based on settings."""
        provider_type = self.settings.llm.provider

        if provider_type == "bailian":
            bailian_config = self.settings.llm.bailian
            return BailianProvider(
                BailianConfig(
                    api_key_env=bailian_config.get("api_key_env", "DASHSCOPE_API_KEY"),
                    api_key=bailian_config.get("api_key"),  # Can be None, falls back to env var
                    model=bailian_config.get("model", "qwen-max"),
                )
            )
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")

    @property
    def harness(self) -> AgentHarness:
        """Get or create agent harness."""
        if self._harness is None:
            self._harness = AgentHarness(
                settings=self.settings,
                llm_provider=self.llm_provider,
                working_dir=self.working_dir,
            )
        return self._harness

    async def chat(self, prompt: str, **options) -> LLMResponse:
        """Send a prompt and get response."""
        return await self.harness.process_prompt(prompt, options)

    async def run(self, prompt: str, **options) -> LLMResponse:
        """Alias for chat()."""
        return await self.chat(prompt, **options)

    def reset(self) -> None:
        """Reset agent state (clear history, recreate harness)."""
        self._harness = None
        self._llm_provider = None

    @classmethod
    async def create(
        cls,
        settings_path: Path | str | None = None,
        working_dir: Path | None = None,
    ) -> "Agent":
        """Factory method to create agent with loaded settings."""
        settings = load_settings(settings_path)
        agent = cls(settings=settings, working_dir=working_dir)
        # Pre-initialize provider to catch API key errors early
        _ = agent.llm_provider
        return agent
