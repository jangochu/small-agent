"""Help skill - display available commands."""

from small_agent.skills.registry import Skill, SkillResult
from small_agent.tools.registry import ToolRegistry
from small_agent.skills.registry import SkillRegistry


class HelpSkill(Skill):
    """Display help for available skills and tools."""

    name = "help"
    description = "Show available commands and tools"
    usage = "/help [skill_name]"

    def __init__(self, skill_registry: SkillRegistry = None, tool_registry: ToolRegistry = None):
        self.skill_registry = skill_registry
        self.tool_registry = tool_registry

    async def execute(self, args: str) -> SkillResult:
        """Show help information."""
        lines = ["[bold]Available Skills:[/bold]"]

        if self.skill_registry:
            for skill in self.skill_registry.list_skills():
                lines.append(f"  /{skill.name} - {skill.description}")

        lines.append("")
        lines.append("[bold]Available Tools:[/bold]")

        if self.tool_registry:
            for tool in self.tool_registry.list_tools():
                auto = " (auto)" if tool.auto_use else ""
                lines.append(f"  {tool.name} - {tool.description}{auto}")

        lines.append("")
        lines.append("[dim]Type a command and press Enter to chat.[/dim]")
        lines.append("[dim]Use /skill to execute skills.[/dim]")

        return SkillResult(
            success=True,
            content="\n".join(lines),
        )
