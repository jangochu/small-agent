"""Tests for configuration loading."""

import json
import tempfile
from pathlib import Path

import pytest

from small_agent.config import (
    Settings,
    load_settings,
    save_settings,
    get_default_settings_json,
)


def test_default_settings():
    """Test default settings creation."""
    settings = Settings()
    assert settings.llm.provider == "bailian"
    assert settings.llm.bailian["api_key_env"] == "DASHSCOPE_API_KEY"
    assert settings.llm.bailian["model"] == "qwen-max"


def test_load_settings_from_file():
    """Test loading settings from a JSON file."""
    config = {
        "llm": {
            "provider": "bailian",
            "bailian": {
                "api_key_env": "CUSTOM_API_KEY",
                "model": "qwen-plus",
            },
        },
        "hooks": {
            "before_tool": "~/.hooks/before.sh",
        },
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config, f)
        temp_path = Path(f.name)

    try:
        settings = load_settings(temp_path)
        assert settings.llm.provider == "bailian"
        assert settings.llm.bailian["api_key_env"] == "CUSTOM_API_KEY"
        assert settings.llm.bailian["model"] == "qwen-plus"
        assert settings.hooks.before_tool == "~/.hooks/before.sh"
    finally:
        temp_path.unlink()


def test_save_settings():
    """Test saving settings to a file."""
    settings = Settings()
    settings.llm.bailian["model"] = "qwen-max-2024"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = Path(f.name)

    try:
        save_settings(settings, temp_path)

        with open(temp_path) as f:
            loaded = json.load(f)

        assert loaded["llm"]["bailian"]["model"] == "qwen-max-2024"
    finally:
        temp_path.unlink()


def test_get_default_settings_json():
    """Test default settings JSON output."""
    json_str = get_default_settings_json()
    data = json.loads(json_str)
    assert data["llm"]["provider"] == "bailian"
    assert "bailian" in data["llm"]
    assert "hooks" in data
