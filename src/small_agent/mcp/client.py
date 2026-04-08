"""MCP Client implementation."""

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@dataclass
class MCPServer:
    """Configuration for an MCP server."""
    name: str
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)


class MCPClient:
    """MCP Client for connecting to external MCP servers."""

    def __init__(self):
        self.servers: dict[str, MCPServer] = {}
        self.sessions: dict[str, ClientSession] = {}
        self._contexts: dict[str, Any] = {}
        self._tasks: dict[str, asyncio.Task] = {}

    def add_server(self, name: str, command: str, args: list[str], env: dict[str, str] = None):
        """Register an MCP server configuration."""
        self.servers[name] = MCPServer(
            name=name,
            command=command,
            args=args,
            env=env or {},
        )

    async def connect(self, name: str) -> bool:
        """Connect to a registered MCP server."""
        if name not in self.servers:
            raise ValueError(f"Unknown MCP server: {name}")

        if name in self.sessions:
            return True

        server = self.servers[name]

        # Create server parameters
        server_params = StdioServerParameters(
            command=server.command,
            args=server.args,
            env=server.env if server.env else None,
        )

        # Create stdio transport
        stdio_transport = await stdio_client(server_params)
        read, write = stdio_transport

        # Create session
        session = ClientSession(read, write)
        await session.initialize()

        self.sessions[name] = session
        self._contexts[name] = stdio_transport

        return True

    async def disconnect(self, name: str) -> None:
        """Disconnect from an MCP server."""
        if name in self.sessions:
            session = self.sessions[name]
            await session.close()

            if name in self._contexts:
                await self._contexts[name].__aexit__(None, None, None)

            del self.sessions[name]
            del self._contexts[name]

    async def disconnect_all(self) -> None:
        """Disconnect from all MCP servers."""
        for name in list(self.sessions.keys()):
            await self.disconnect(name)

    async def list_tools(self, server_name: Optional[str] = None) -> list[dict]:
        """List available tools from MCP server(s)."""
        tools = []

        if server_name:
            if server_name not in self.sessions:
                await self.connect(server_name)
            session = self.sessions[server_name]
            response = await session.list_tools()
            for tool in response.tools:
                tools.append({
                    "name": f"{server_name}:{tool.name}",
                    "description": tool.description or "",
                    "inputSchema": tool.inputSchema,
                    "server": server_name,
                })
        else:
            for name, session in self.sessions.items():
                response = await session.list_tools()
                for tool in response.tools:
                    tools.append({
                        "name": f"{name}:{tool.name}",
                        "description": tool.description or "",
                        "inputSchema": tool.inputSchema,
                        "server": name,
                    })

        return tools

    async def call_tool(self, tool_name: str, arguments: dict) -> Any:
        """Call an MCP tool.

        Args:
            tool_name: Tool name in format 'server:tool' or just 'tool'
            arguments: Tool arguments

        Returns:
            Tool result
        """
        # Parse server name from tool name
        if ":" in tool_name:
            server_name, tool = tool_name.split(":", 1)
        else:
            # Try to find tool in any connected server
            server_name = None
            tool = tool_name

        if server_name:
            if server_name not in self.sessions:
                await self.connect(server_name)
            session = self.sessions[server_name]
        else:
            # Search in all sessions
            session = None
            for name, sess in self.sessions.items():
                try:
                    response = await sess.list_tools()
                    if any(t.name == tool for t in response.tools):
                        session = sess
                        server_name = name
                        break
                except:
                    continue

            if not session:
                raise ValueError(f"Tool not found: {tool_name}")

        # Call the tool
        result = await session.call_tool(tool, arguments)
        return result

    async def get_prompt(self, server_name: str, prompt_name: str, arguments: dict = None) -> str:
        """Get a prompt from an MCP server."""
        if server_name not in self.sessions:
            await self.connect(server_name)

        session = self.sessions[server_name]
        result = await session.get_prompt(prompt_name, arguments or {})
        return result

    def __aiter__(self):
        """Iterate over connected servers."""
        return iter(self.sessions.items())
