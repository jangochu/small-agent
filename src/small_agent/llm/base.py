"""Base LLM provider interface."""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional
from pydantic import BaseModel, Field, ConfigDict


class LLMConfig(BaseModel):
    """Base configuration for any LLM provider."""

    model_config = ConfigDict(extra="allow")

    provider_type: str = Field(description="Provider type identifier")
    model: str = Field(description="Model name/id")


class LLMResponse(BaseModel):
    """Standardized response from any LLM provider."""

    content: str = Field(description="Generated text content")
    model: str = Field(description="Model that generated the response")
    usage: Optional[dict] = Field(default=None, description="Token usage info")
    raw: Optional[dict] = Field(default=None, description="Raw provider response")
    tool_calls: Optional[list[dict]] = Field(default=None, description="Tool calls from the LLM")


class LLMProvider(ABC):
    """Abstract base class for LLM providers.

    Implementations should handle:
    - Provider-specific authentication
    - Request/response formatting
    - Error handling and retries
    """

    @property
    @abstractmethod
    def provider_type(self) -> str:
        """Return the provider type identifier."""
        pass

    @abstractmethod
    async def generate(
        self,
        messages: list[dict],
        config: LLMConfig,
        tools: Optional[list[dict]] = None,
        **options,
    ) -> LLMResponse:
        """Generate a completion response.

        Args:
            messages: List of message dicts with 'role' and 'content'
            config: Provider configuration
            tools: Optional list of tool definitions for function calling
            **options: Additional generation options (temperature, max_tokens, etc.)

        Returns:
            LLMResponse with generated content
        """
        pass

    @abstractmethod
    async def stream(
        self,
        messages: list[dict],
        config: LLMConfig,
        tools: Optional[list[dict]] = None,
        **options,
    ) -> AsyncGenerator[str, None]:
        """Stream a completion response.

        Args:
            messages: List of message dicts with 'role' and 'content'
            config: Provider configuration
            tools: Optional list of tool definitions for function calling
            **options: Additional generation options

        Yields:
            Chunks of generated text
        """
        pass
