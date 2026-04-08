"""Clear skill - clear conversation history."""

from small_agent.skills.registry import Skill, SkillResult


class ClearSkill(Skill):
    """Clear conversation history."""

    name = "clear"
    description = "Clear conversation history"
    usage = "/clear"

    def __init__(self, clear_callback=None):
        self.clear_callback = clear_callback

    async def execute(self, args: str) -> SkillResult:
        """Clear conversation history."""
        if self.clear_callback:
            self.clear_callback()
            return SkillResult(
                success=True,
                content="Conversation history cleared.",
            )
        return SkillResult(
            success=False,
            content="",
            error="Clear callback not set",
        )
