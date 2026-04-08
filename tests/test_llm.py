"""Tests for LLM providers."""

import os

import pytest

from small_agent.llm.base import LLMConfig, LLMResponse
from small_agent.llm.bailian import BailianConfig, BailianProvider


def test_bailian_config():
    """Test BailianConfig creation."""
    config = BailianConfig()
    assert config.provider_type == "bailian"
    assert config.api_key_env == "DASHSCOPE_API_KEY"
    assert config.model == "qwen-max"


def test_bailian_config_custom():
    """Test custom BailianConfig."""
    config = BailianConfig(
        api_key_env="CUSTOM_KEY",
        model="qwen-plus",
    )
    assert config.api_key_env == "CUSTOM_KEY"
    assert config.model == "qwen-plus"


def test_bailian_provider_requires_api_key():
    """Test that BailianProvider requires API key."""
    config = BailianConfig(api_key_env="NONEXISTENT_KEY_12345")

    with pytest.raises(ValueError, match="API key not set"):
        BailianProvider(config)


def test_bailian_provider_with_direct_key():
    """Test BailianProvider with direct API key."""
    config = BailianConfig(api_key="sk-test123", model="qwen-max")
    provider = BailianProvider(config)
    assert provider._api_key == "sk-test123"


def test_bailian_provider_direct_key_takes_precedence():
    """Test that direct API key takes precedence over env var."""
    # Set a fake env var
    os.environ["TEST_KEY"] = "env-key"
    config = BailianConfig(api_key_env="TEST_KEY", api_key="direct-key")
    provider = BailianProvider(config)
    assert provider._api_key == "direct-key"
    del os.environ["TEST_KEY"]


def test_llm_response():
    """Test LLMResponse creation."""
    response = LLMResponse(
        content="Test response",
        model="qwen-max",
        usage={"total_tokens": 100},
    )
    assert response.content == "Test response"
    assert response.model == "qwen-max"
    assert response.usage["total_tokens"] == 100
