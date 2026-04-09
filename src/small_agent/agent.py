"""Main agent orchestration."""

import asyncio
from pathlib import Path
from typing import Any, Optional

from small_agent.config import Settings, load_settings
from small_agent.harness import AgentHarness
from small_agent.llm.base import LLMProvider, LLMResponse
from small_agent.llm.bailian import BailianProvider, BailianConfig
from small_agent.mcp.client import MCPClient
from small_agent.tools.registry import ToolRegistry
from small_agent.tools.builtin import ShellTool, FileTool, HttpTool, WeatherTool
from small_agent.skills.registry import SkillRegistry
from small_agent.skills.builtin import HelpSkill, ClearSkill, ToolsSkill, ConfigSkill


class Agent:
    """Main agent class that manages providers, harness, tools, skills, and MCP."""

    def __init__(
        self,
        settings: Optional[Settings] = None,
        working_dir: Path | None = None,
    ):
        self.settings = settings or load_settings()
        self.working_dir = working_dir or Path.cwd()
        self._harness: Optional[AgentHarness] = None
        self._llm_provider: Optional[LLMProvider] = None

        # Initialize MCP client
        self.mcp = MCPClient()
        self._setup_mcp_servers()

        # Initialize tool registry
        self.tool_registry = ToolRegistry()
        self._setup_builtin_tools()

        # Initialize skill registry
        self.skill_registry = SkillRegistry()
        self._setup_builtin_skills()

    def _setup_mcp_servers(self):
        """Setup MCP servers from config."""
        if hasattr(self.settings, 'mcp') and self.settings.mcp:
            servers = getattr(self.settings.mcp, 'servers', {})
            for name, config in servers.items():
                self.mcp.add_server(
                    name=name,
                    command=config.get('command', ''),
                    args=config.get('args', []),
                    env=config.get('env', {}),
                )

    def _setup_builtin_tools(self):
        """Register built-in tools."""
        self.tool_registry.register(ShellTool())
        self.tool_registry.register(FileTool())
        self.tool_registry.register(HttpTool())
        self.tool_registry.register(WeatherTool())

    def _setup_builtin_skills(self):
        """Register built-in skills."""
        self.skill_registry.register(HelpSkill(
            skill_registry=self.skill_registry,
            tool_registry=self.tool_registry,
        ))
        self.skill_registry.register(ClearSkill(clear_callback=self.reset))
        self.skill_registry.register(ToolsSkill(tool_registry=self.tool_registry))
        self.skill_registry.register(ConfigSkill())

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
                    api_key=bailian_config.get("api_key"),
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
                tool_registry=self.tool_registry,
            )
        return self._harness

    def get_available_tools(self) -> list[dict]:
        """Get list of available tools for LLM."""
        tools = self.tool_registry.to_llm_tools()
        return tools

    async def execute_tool(self, name: str, **kwargs) -> Any:
        """Execute a tool by name."""
        return await self.tool_registry.execute(name, **kwargs)

    async def execute_skill(self, name: str, args: str = "") -> Any:
        """Execute a skill by name."""
        return await self.skill_registry.execute(name, args)

    def parse_skill_command(self, user_input: str) -> tuple[Optional[str], str]:
        """Parse a slash command from user input."""
        return self.skill_registry.parse_command(user_input)

    async def chat(self, prompt: str, **options) -> LLMResponse:
        """Send a prompt and get response."""
        tools = self.get_available_tools()
        return await self.harness.process_prompt(prompt, options, tools=tools)

    async def run(self, prompt: str, **options) -> LLMResponse:
        """Alias for chat()."""
        return await self.chat(prompt, **options)

    def reset(self) -> None:
        """Reset agent state (clear history, recreate harness)."""
        self._harness = None
        self._llm_provider = None

    async def connect_mcp(self, server_name: str) -> bool:
        """Connect to an MCP server."""
        return await self.mcp.connect(server_name)

    async def disconnect_mcp(self, server_name: str) -> None:
        """Disconnect from an MCP server."""
        await self.mcp.disconnect(server_name)

    async def list_mcp_tools(self, server_name: Optional[str] = None) -> list[dict]:
        """List MCP tools."""
        return await self.mcp.list_tools(server_name)

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
