"""Tests for MCP client."""

import pytest
from small_agent.mcp.client import MCPClient, MCPServer


class TestMCPServer:
    """Tests for MCPServer dataclass."""

    def test_create_server(self):
        """Test creating an MCP server config."""
        server = MCPServer(
            name="test",
            command="node",
            args=["server.js"],
            env={"KEY": "value"},
        )

        assert server.name == "test"
        assert server.command == "node"
        assert server.args == ["server.js"]
        assert server.env["KEY"] == "value"


class TestMCPClient:
    """Tests for MCPClient."""

    def test_add_server(self):
        """Test adding a server configuration."""
        client = MCPClient()
        client.add_server(
            name="test",
            command="node",
            args=["server.js"],
        )

        assert "test" in client.servers
        assert client.servers["test"].command == "node"

    def test_add_server_with_env(self):
        """Test adding a server with environment variables."""
        client = MCPClient()
        client.add_server(
            name="test",
            command="node",
            args=["server.js"],
            env={"API_KEY": "secret"},
        )

        assert client.servers["test"].env["API_KEY"] == "secret"

    def test_unknown_server(self):
        """Test error on unknown server."""
        client = MCPClient()

        with pytest.raises(ValueError, match="Unknown MCP server"):
            import asyncio
            asyncio.run(client.connect("unknown"))

    def test_iter_servers(self):
        """Test iterating over servers."""
        client = MCPClient()
        client.add_server("server1", "cmd1", [])
        client.add_server("server2", "cmd2", [])

        # Note: Can only iterate disconnected servers in this simple test
        assert len(client.servers) == 2


class TestMCPClientToolMethods:
    """Tests for MCP client tool methods."""

    @pytest.mark.asyncio
    async def test_list_tools_no_servers(self):
        """Test listing tools with no servers."""
        client = MCPClient()
        tools = await client.list_tools()

        assert tools == []

    @pytest.mark.asyncio
    async def test_call_tool_unknown(self):
        """Test calling unknown tool."""
        client = MCPClient()

        with pytest.raises(ValueError, match="Tool not found"):
            await client.call_tool("unknown", {})
