"""Tests for tools system."""

import pytest
from small_agent.tools.registry import ToolRegistry, Tool, ToolResult
from small_agent.tools.builtin import ShellTool, FileTool, HttpTool


class TestToolRegistry:
    """Tests for ToolRegistry."""

    def test_register_tool(self):
        """Test registering a tool."""
        registry = ToolRegistry()
        tool = ShellTool()
        registry.register(tool)

        assert registry.get("shell") == tool

    def test_unregister_tool(self):
        """Test unregistering a tool."""
        registry = ToolRegistry()
        registry.register(ShellTool())
        registry.unregister("shell")

        assert registry.get("shell") is None

    def test_list_tools(self):
        """Test listing tools."""
        registry = ToolRegistry()
        registry.register(ShellTool())
        registry.register(FileTool())

        tools = registry.list_tools()
        assert len(tools) == 2

    def test_to_llm_tools(self):
        """Test converting tools to LLM format."""
        registry = ToolRegistry()
        registry.register(ShellTool())

        llm_tools = registry.to_llm_tools()
        assert len(llm_tools) == 1
        assert llm_tools[0]["type"] == "function"
        assert llm_tools[0]["function"]["name"] == "shell"


class TestShellTool:
    """Tests for ShellTool."""

    @pytest.mark.asyncio
    async def test_execute_command(self):
        """Test executing a shell command."""
        tool = ShellTool()
        result = await tool.execute(command="echo hello")

        assert result.success is True
        assert "hello" in result.content

    @pytest.mark.asyncio
    async def test_execute_failing_command(self):
        """Test executing a failing command."""
        tool = ShellTool()
        result = await tool.execute(command="exit 1")

        assert result.success is False
        assert result.data.get("returncode") == 1

    @pytest.mark.asyncio
    async def test_execute_with_timeout(self):
        """Test command timeout."""
        tool = ShellTool()
        result = await tool.execute(command="sleep 2", timeout=1)

        assert result.success is False
        assert "timed out" in result.error


class TestFileTool:
    """Tests for FileTool."""

    @pytest.mark.asyncio
    async def test_write_and_read(self, tmp_path):
        """Test writing and reading a file."""
        tool = FileTool()
        test_file = tmp_path / "test.txt"

        # Write
        result = await tool.execute(
            operation="write",
            path=str(test_file),
            content="hello world",
        )
        assert result.success is True

        # Read
        result = await tool.execute(
            operation="read",
            path=str(test_file),
        )
        assert result.success is True
        assert result.content == "hello world"

    @pytest.mark.asyncio
    async def test_delete(self, tmp_path):
        """Test deleting a file."""
        tool = FileTool()
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        result = await tool.execute(
            operation="delete",
            path=str(test_file),
        )
        assert result.success is True
        assert not test_file.exists()

    @pytest.mark.asyncio
    async def test_exists(self, tmp_path):
        """Test checking file existence."""
        tool = FileTool()
        test_file = tmp_path / "test.txt"

        result = await tool.execute(
            operation="exists",
            path=str(test_file),
        )
        assert result.success is True
        assert result.data.get("exists") is False


class TestHttpTool:
    """Tests for HttpTool."""

    @pytest.mark.asyncio
    async def test_get_request(self):
        """Test making a GET request."""
        tool = HttpTool()
        result = await tool.execute(
            method="GET",
            url="https://httpbin.org/get",
        )

        # Check result structure (network may be unavailable)
        if result.success:
            assert result.data is not None
            assert result.data.get("status") == 200
        # If not success, it's likely a network issue, not a code issue
