"""Tests for hook executor."""

import asyncio
import tempfile
from pathlib import Path

import pytest

from small_agent.hooks.executor import HookExecutor, HarnessEvent


@pytest.fixture
def executor():
    """Create a HookExecutor for testing."""
    return HookExecutor()


def test_harness_event():
    """Test HarnessEvent creation."""
    event = HarnessEvent("test_event", {"key": "value"})
    assert event.name == "test_event"
    assert event.context["key"] == "value"


@pytest.mark.asyncio
async def test_execute_simple_hook(executor):
    """Test executing a simple hook command."""
    event = HarnessEvent("test", {"foo": "bar"})

    # Use a simple echo command
    returncode, stdout, stderr = await executor.execute(
        "echo 'Hello from hook'",
        event,
    )

    assert returncode == 0
    assert "Hello from hook" in stdout


@pytest.mark.asyncio
async def test_execute_hook_with_context(executor):
    """Test hook execution with context variables."""
    event = HarnessEvent("before_prompt", {"prompt": "test prompt"})

    # Command that uses context env var
    cmd = "echo \"Prompt: $HARNESS_PROMPT\""
    returncode, stdout, stderr = await executor.execute(cmd, event)

    assert returncode == 0
    assert "Prompt: test prompt" in stdout


@pytest.mark.asyncio
async def test_execute_hook_with_env_var(executor):
    """Test that hook receives event name."""
    event = HarnessEvent("after_response", {})

    cmd = "echo \"Event: $HARNESS_EVENT_NAME\""
    returncode, stdout, stderr = await executor.execute(cmd, event)

    assert returncode == 0
    assert "Event: after_response" in stdout


@pytest.mark.asyncio
async def test_execute_hook_timeout(executor):
    """Test hook execution timeout."""
    event = HarnessEvent("test", {})

    # Command that takes too long
    returncode, stdout, stderr = await executor.execute(
        "sleep 10",
        event,
        timeout=1,
    )

    assert returncode == -1
    assert "timed out" in stderr


@pytest.mark.asyncio
async def test_execute_failing_hook(executor):
    """Test handling of failing hook."""
    event = HarnessEvent("test", {})

    returncode, stdout, stderr = await executor.execute(
        "exit 1",
        event,
    )

    assert returncode == 1


def test_execute_sync_hook(executor):
    """Test synchronous hook execution."""
    event = HarnessEvent("test", {"data": "sync"})

    cmd = "echo 'Sync hook executed'"
    returncode, stdout, stderr = executor.execute_sync(cmd, event)

    assert returncode == 0
    assert "Sync hook executed" in stdout
