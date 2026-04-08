# small-agent

A CLI agent powered by 阿里云百炼 (Alibaba Cloud Bailian) with harness engineering patterns, MCP support, and extensible tools/skills system.

## Features

- 🚀 **Bailian Integration**: Uses Alibaba Cloud DashScope SDK for Qwen models
- 🔌 **Pluggable LLM Providers**: Strategy pattern for easy provider swapping
- ⚡ **Harness Hooks**: Event-driven shell hooks (like Claude Code)
- 🛠️ **Tools System**: Built-in shell, file, and HTTP tools with auto/manual execution
- 🎯 **Skills System**: Slash command skills like `/help`, `/config`, `/tools`
- 🔗 **MCP Client**: Connect to external MCP servers (filesystem, database, etc.)
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
      "api_key": "sk-your-key-here",
      "model": "qwen-max"
    }
  },
  "hooks": {
    "before_tool": null,
    "after_tool": null
  },
  "mcp": {
    "servers": {
      "filesystem": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "."]
      }
    }
  },
  "tools": {
    "enabled": ["shell", "file", "http"]
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
small-agent run "杭州有什么好玩的"
```

## Skills (Slash Commands)

In chat mode, use slash commands:

| Command | Description |
|---------|-------------|
| `/help` | Show available commands and tools |
| `/clear` | Clear conversation history |
| `/tools` | List available tools |
| `/config` | Show current configuration |

## Tools

Built-in tools available for LLM auto-calling:

| Tool | Description | Auto |
|------|-------------|------|
| `shell` | Execute shell commands | ✅ |
| `file` | Read/write/delete files | ✅ |
| `http` | Make HTTP requests | ✅ |

## MCP Integration

Configure MCP servers in `settings.json`:

```json
{
  "mcp": {
    "servers": {
      "filesystem": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/watch"]
      }
    }
  }
}
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
│   ├── mcp/             # MCP Client
│   │   ├── __init__.py
│   │   └── client.py
│   ├── tools/           # Tools system
│   │   ├── __init__.py
│   │   ├── registry.py
│   │   └── builtin/
│   └── skills/          # Skills system
│       ├── __init__.py
│       ├── registry.py
│       └── builtin/
├── tests/
├── pyproject.toml
├── settings.json
└── README.md
```

## License

MIT
