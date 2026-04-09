"""Alibaba Cloud Bailian (DashScope) LLM provider."""

import json
import os
from dataclasses import dataclass
from typing import AsyncGenerator, Optional

from dashscope import Generation
from dashscope.api_entities.dashscope_response import Role

from small_agent.llm.base import LLMProvider, LLMResponse, LLMConfig


@dataclass
class ToolCall:
    """Represents a tool call from the LLM."""
    id: str
    name: str
    arguments: dict


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
        tools: Optional[list[dict]] = None,
        **options,
    ) -> LLMResponse:
        """Generate completion using Bailian."""
        bailian_config = BailianConfig(**config.model_dump())

        # Convert messages to DashScope format
        dashscope_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content")

            # Map common roles to DashScope roles
            if role == "assistant":
                role = Role.ASSISTANT
            elif role == "system":
                role = Role.SYSTEM
            elif role == "tool":
                role = "tool"  # Keep tool role as-is
            else:
                role = Role.USER

            dashscope_msg = {
                "role": role,
                "content": content if content is not None else "",
            }

            # Preserve tool_calls for assistant messages
            if role == Role.ASSISTANT and msg.get("tool_calls"):
                dashscope_msg["tool_calls"] = msg["tool_calls"]

            # Preserve tool_call_id for tool messages
            if role == "tool" and msg.get("tool_call_id"):
                dashscope_msg["tool_call_id"] = msg["tool_call_id"]

            dashscope_messages.append(dashscope_msg)

        # Build API parameters
        api_params = {
            "model": bailian_config.model,
            "messages": dashscope_messages,
            "api_key": self._api_key,
            **options,
        }

        # Add tools if provided
        if tools:
            api_params["tools"] = tools

        # Call DashScope API
        response = Generation.call(**api_params)

        if response.status_code != 200:
            raise RuntimeError(
                f"Bailian API error: {response.code} - {response.message}"
            )

        # Check for tool calls in response
        output = response.output
        tool_calls = None
        content = ""

        # Qwen returns tool_calls in the output
        if output.get("choices") and len(output["choices"]) > 0:
            choice = output["choices"][0]
            message = choice.get("message", {})

            # Get content from message (not from output.text)
            content = message.get("content", "") or ""

            # Handle tool calls
            if message.get("tool_calls"):
                tool_calls = []
                for tc in message["tool_calls"]:
                    tool_calls.append({
                        "id": tc.get("id", ""),
                        "type": "function",
                        "function": {
                            "name": tc.get("function", {}).get("name", ""),
                            "arguments": tc.get("function", {}).get("arguments", "{}"),
                        },
                    })

        return LLMResponse(
            content=content,
            model=bailian_config.model,
            usage={
                "prompt_tokens": response.usage.get("input_tokens", 0),
                "completion_tokens": response.usage.get("output_tokens", 0),
                "total_tokens": response.usage.get("total_tokens", 0),
            },
            raw={"output": output},  # Store as dict for easier access
            tool_calls=tool_calls,
        )

    async def stream(
        self,
        messages: list[dict],
        config: LLMConfig,
        tools: Optional[list[dict]] = None,
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
        api_params = {
            "model": bailian_config.model,
            "messages": dashscope_messages,
            "api_key": self._api_key,
            "stream": True,
            **options,
        }

        if tools:
            api_params["tools"] = tools

        responses = Generation.call(**api_params)

        async for response in responses:
            if response.status_code == 200:
                yield response.output.get("text", "")
            else:
                raise RuntimeError(
                    f"Bailian stream error: {response.code} - {response.message}"
                )
