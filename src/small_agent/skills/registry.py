"""Skill registry and base classes."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class SkillResult:
    """Result of a skill execution."""
    success: bool
    content: str
    error: Optional[str] = None


class Skill(ABC):
    """Base class for skills."""

    name: str = ""
    description: str = ""
    usage: str = ""  # Usage example

    @abstractmethod
    async def execute(self, args: str) -> SkillResult:
        """Execute the skill with given arguments."""
        pass

    def get_help(self) -> str:
        """Get help text for this skill."""
        return f"/{self.name} - {self.description}\n  Usage: {self.usage}"


class SkillRegistry:
    """Registry for skills."""

    def __init__(self):
        self._skills: dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        """Register a skill."""
        self._skills[skill.name] = skill

    def unregister(self, name: str) -> None:
        """Unregister a skill by name."""
        if name in self._skills:
            del self._skills[name]

    def get(self, name: str) -> Optional[Skill]:
        """Get a skill by name."""
        return self._skills.get(name)

    def list_skills(self) -> list[Skill]:
        """List all registered skills."""
        return list(self._skills.values())

    async def execute(self, name: str, args: str = "") -> SkillResult:
        """Execute a skill by name."""
        skill = self.get(name)
        if not skill:
            return SkillResult(
                success=False,
                content="",
                error=f"Skill not found: {name}",
            )
        try:
            return await skill.execute(args)
        except Exception as e:
            return SkillResult(
                success=False,
                content="",
                error=str(e),
            )

    def parse_command(self, user_input: str) -> tuple[Optional[str], str]:
        """Parse a slash command from user input.

        Returns:
            Tuple of (skill_name, args) or (None, original_input) if not a command
        """
        user_input = user_input.strip()
        if user_input.startswith("/"):
            parts = user_input[1:].split(" ", 1)
            skill_name = parts[0]
            args = parts[1] if len(parts) > 1 else ""
            return skill_name, args
        return None, user_input
