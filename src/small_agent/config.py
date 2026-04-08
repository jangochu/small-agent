"""Configuration loading and validation."""

import json
import os
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field, ConfigDict


class LLMConfig(BaseModel):
    """LLM configuration section."""

    model_config = ConfigDict(extra="allow")

    provider: str = Field(default="bailian", description="Active LLM provider")
    bailian: dict[str, Any] = Field(
        default_factory=lambda: {
            "api_key_env": "DASHSCOPE_API_KEY",
            "model": "qwen-max",
        },
        description="Bailian provider config",
    )


class HooksConfig(BaseModel):
    """Hook configuration - event to command mapping."""

    before_tool: str | None = Field(default=None, description="Run before tool execution")
    after_tool: str | None = Field(default=None, description="Run after tool execution")
    before_prompt: str | None = Field(default=None, description="Run before processing prompt")
    after_response: str | None = Field(default=None, description="Run after generating response")


class MemoryConfig(BaseModel):
    """Memory configuration."""

    directory: str = Field(
        default="~/.claude/projects/{project_name}/memory",
        description="Memory directory path",
    )


class Settings(BaseModel):
    """Main settings schema."""

    model_config = ConfigDict(extra="allow")

    llm: LLMConfig = Field(default_factory=LLMConfig)
    hooks: HooksConfig = Field(default_factory=HooksConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)


def expand_path(path: str) -> str:
    """Expand ~ and environment variables in paths."""
    path = os.path.expanduser(path)
    path = os.path.expandvars(path)
    return path


def load_settings(settings_path: Path | str | None = None) -> Settings:
    """Load settings from JSON file.

    Args:
        settings_path: Path to settings file. If None, looks for
            ./settings.json, then ~/.small-agent/settings.json

    Returns:
        Validated Settings object
    """
    if settings_path is None:
        # Try local directory first
        local_path = Path("settings.json")
        if local_path.exists():
            settings_path = local_path
        else:
            # Fall back to home directory
            home_path = Path.home() / ".small-agent" / "settings.json"
            if home_path.exists():
                settings_path = home_path
            else:
                # Return defaults
                return Settings()

    with open(settings_path, "r") as f:
        data = json.load(f)

    return Settings(**data)


def save_settings(settings: Settings, settings_path: Path | str) -> None:
    """Save settings to JSON file."""
    settings_path = Path(settings_path)
    settings_path.parent.mkdir(parents=True, exist_ok=True)

    with open(settings_path, "w") as f:
        json.dump(settings.model_dump(), f, indent=2)


def get_default_settings_json() -> str:
    """Return default settings as JSON string."""
    return json.dumps(
        {
            "llm": {
                "provider": "bailian",
                "bailian": {
                    "api_key_env": "DASHSCOPE_API_KEY",
                    "api_key": None,  # Set your key here or use env var
                    "model": "qwen-max",
                },
            },
            "hooks": {
                "before_tool": None,
                "after_tool": None,
                "before_prompt": None,
                "after_response": None,
            },
            "memory": {
                "directory": "~/.claude/projects/{project_name}/memory",
            },
        },
        indent=2,
    )
