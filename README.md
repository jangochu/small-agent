# small-agent

A CLI agent powered by 阿里云百炼 (Alibaba Cloud Bailian) with harness engineering patterns.

## Features

- 🚀 **Bailian Integration**: Uses Alibaba Cloud DashScope SDK for Qwen models
- 🔌 **Pluggable LLM Providers**: Strategy pattern for easy provider swapping
- ⚡ **Harness Hooks**: Event-driven shell hooks (like Claude Code)
- 📝 **Memory System**: Persistent file-based memory across sessions

## Installation

```bash
pip install -e ".[dev]"
```

## Configuration

Create a `settings.json` file:

```json
{
  "llm": {
    "provider": "bailian",
    "bailian": {
      "api_key_env": "DASHSCOPE_API_KEY",
      "model": "qwen-max"
    }
  },
  "hooks": {
    "before_tool": "~/.claude/hooks/before_tool.sh",
    "after_tool": "~/.claude/hooks/after_tool.sh"
  }
}
```

## Usage

```bash
# Start interactive chat
small-agent chat

# View config
small-agent config

# Run a single prompt
small-agent run "What is the capital of France?"
```

## Project Structure

```
small-agent/
├── src/small_agent/
│   ├── __init__.py
│   ├── cli.py           # CLI entry point
│   ├── agent.py         # Agent orchestration
│   ├── harness.py       # Event system & hooks
│   ├── config.py        # Configuration
│   └── llm/
│       ├── __init__.py
│       ├── base.py      # LLM provider interface
│       └── bailian.py   # Bailian implementation
├── tests/
├── pyproject.toml
└── README.md
```

## License

MIT
