"""Tools skill - list available tools."""

from small_agent.skills.registry import Skill, SkillResult
from small_agent.tools.registry import ToolRegistry


class ToolsSkill(Skill):
    """List available tools."""

    name = "tools"
    description = "List available tools"
    usage = "/tools"

    def __init__(self, tool_registry: ToolRegistry = None):
        self.tool_registry = tool_registry

    async def execute(self, args: str) -> SkillResult:
        """List all available tools."""
        if not self.tool_registry:
            return SkillResult(
                success=False,
                content="",
                error="Tool registry not available",
            )

        lines = ["[bold]Available Tools:[/bold]", ""]

        for tool in self.tool_registry.list_tools():
            auto_tag = " [green](auto)[/green]" if tool.auto_use else " [dim](manual)[/dim]"
            lines.append(f"  [bold]{tool.name}[/bold]{auto_tag}")
            lines.append(f"    {tool.description}")
            lines.append("")

        return SkillResult(
            success=True,
            content="\n".join(lines),
        )
