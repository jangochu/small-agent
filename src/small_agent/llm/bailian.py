"""Alibaba Cloud Bailian (DashScope) LLM provider."""

import os
from typing import AsyncGenerator

from dashscope import Generation
from dashscope.api_entities.dashscope_response import Role

from small_agent.llm.base import LLMProvider, LLMResponse, LLMConfig


class BailianConfig(LLMConfig):
    """Bailian-specific configuration."""

    provider_type: str = "bailian"
    model: str = "qwen-max"
    api_key_env: str = "DASHSCOPE_API_KEY"
    api_key: str | None = None  # Direct key takes precedence
    base_url: str | None = None


class BailianProvider(LLMProvider):
    """Alibaba Cloud Bailian provider using DashScope SDK."""

    @property
    def provider_type(self) -> str:
        return "bailian"

    def __init__(self, config: BailianConfig):
        self.config = config
        self._api_key = self._get_api_key(config)
        if not self._api_key:
            raise ValueError(
                f"API key not set. Provide 'api_key' in settings or set "
                f"env var '{config.api_key_env}'"
            )

    def _get_api_key(self, config: BailianConfig) -> str | None:
        """Get API key, preferring direct key over env var."""
        # Direct key takes precedence
        if config.api_key:
            return config.api_key
        # Fall back to environment variable
        return os.getenv(config.api_key_env)

    async def generate(
        self,
        messages: list[dict],
        config: LLMConfig,
        **options,
    ) -> LLMResponse:
        """Generate completion using Bailian."""
        bailian_config = BailianConfig(**config.model_dump())

        # Convert messages to DashScope format
        dashscope_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            # Map common roles to DashScope roles
            if role == "assistant":
                role = Role.ASSISTANT
            elif role == "system":
                role = Role.SYSTEM
            else:
                role = Role.USER

            dashscope_messages.append({
                "role": role,
                "content": msg.get("content", "")
            })

        # Call DashScope API
        response = Generation.call(
            model=bailian_config.model,
            messages=dashscope_messages,
            api_key=self._api_key,
            **options,
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"Bailian API error: {response.code} - {response.message}"
            )

        return LLMResponse(
            content=response.output.get("text", ""),
            model=bailian_config.model,
            usage={
                "prompt_tokens": response.usage.get("input_tokens", 0),
                "completion_tokens": response.usage.get("output_tokens", 0),
                "total_tokens": response.usage.get("total_tokens", 0),
            },
            raw=response,
        )

    async def stream(
        self,
        messages: list[dict],
        config: LLMConfig,
        **options,
    ) -> AsyncGenerator[str, None]:
        """Stream completion using Bailian."""
        bailian_config = BailianConfig(**config.model_dump())

        dashscope_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            if role == "assistant":
                role = Role.ASSISTANT
            elif role == "system":
                role = Role.SYSTEM
            else:
                role = Role.USER

            dashscope_messages.append({
                "role": role,
                "content": msg.get("content", "")
            })

        # Stream call
        responses = Generation.call(
            model=bailian_config.model,
            messages=dashscope_messages,
            api_key=self._api_key,
            stream=True,
            **options,
        )

        async for response in responses:
            if response.status_code == 200:
                yield response.output.get("text", "")
            else:
                raise RuntimeError(
                    f"Bailian stream error: {response.code} - {response.message}"
                )
