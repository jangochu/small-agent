"""Config skill - view and edit configuration."""

from small_agent.skills.registry import Skill, SkillResult
from small_agent.config import load_settings


class ConfigSkill(Skill):
    """View current configuration."""

    name = "config"
    description = "Show current configuration"
    usage = "/config"

    async def execute(self, args: str) -> SkillResult:
        """Show current configuration."""
        try:
            settings = load_settings()

            lines = ["[bold]Current Configuration:[/bold]", ""]
            lines.append(f"  LLM Provider: [cyan]{settings.llm.provider}[/cyan]")
            lines.append(f"  Model: [cyan]{settings.llm.bailian.get('model', 'qwen-max')}[/cyan]")

            if settings.llm.bailian.get("api_key"):
                key = settings.llm.bailian.get("api_key")
                masked = key[:6] + "..." + key[-4:] if len(key) > 10 else "***"
                lines.append(f"  API Key: [cyan]{masked}[/cyan]")
            else:
                lines.append(f"  API Key Env: [cyan]{settings.llm.bailian.get('api_key_env')}[/cyan]")

            lines.append("")
            lines.append("  [bold]Hooks:[/bold]")
            if settings.hooks.before_tool:
                lines.append(f"    before_tool: {settings.hooks.before_tool}")
            if settings.hooks.after_tool:
                lines.append(f"    after_tool: {settings.hooks.after_tool}")
            if settings.hooks.before_prompt:
                lines.append(f"    before_prompt: {settings.hooks.before_prompt}")
            if settings.hooks.after_response:
                lines.append(f"    after_response: {settings.hooks.after_response}")

            if not any([
                settings.hooks.before_tool,
                settings.hooks.after_tool,
                settings.hooks.before_prompt,
                settings.hooks.after_response,
            ]):
                lines.append("    (none configured)")

            lines.append("")
            lines.append(f"  [bold]Memory:[/bold] {settings.memory.directory}")

            return SkillResult(
                success=True,
                content="\n".join(lines),
            )

        except Exception as e:
            return SkillResult(
                success=False,
                content="",
                error=str(e),
            )
