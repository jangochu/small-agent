"""Tests for skills system."""

import pytest
from small_agent.skills.registry import SkillRegistry, Skill, SkillResult


class TestSkillRegistry:
    """Tests for SkillRegistry."""

    def test_register_skill(self):
        """Test registering a skill."""
        registry = SkillRegistry()

        class TestSkill(Skill):
            name = "test"
            description = "Test skill"

            async def execute(self, args: str) -> SkillResult:
                return SkillResult(success=True, content="ok")

        skill = TestSkill()
        registry.register(skill)

        assert registry.get("test") == skill

    def test_unregister_skill(self):
        """Test unregistering a skill."""
        registry = SkillRegistry()

        class TestSkill(Skill):
            name = "test"
            description = "Test skill"

            async def execute(self, args: str) -> SkillResult:
                return SkillResult(success=True, content="ok")

        skill = TestSkill()
        registry.register(skill)
        registry.unregister("test")

        assert registry.get("test") is None

    def test_list_skills(self):
        """Test listing skills."""
        registry = SkillRegistry()

        class TestSkill(Skill):
            name = "test"
            description = "Test skill"

            async def execute(self, args: str) -> SkillResult:
                return SkillResult(success=True, content="ok")

        registry.register(TestSkill())
        skills = registry.list_skills()

        assert len(skills) == 1

    @pytest.mark.asyncio
    async def test_execute_skill(self):
        """Test executing a skill."""
        registry = SkillRegistry()

        class TestSkill(Skill):
            name = "test"
            description = "Test skill"

            async def execute(self, args: str) -> SkillResult:
                return SkillResult(success=True, content=f"args: {args}")

        registry.register(TestSkill())
        result = await registry.execute("test", "hello")

        assert result.success is True
        assert "hello" in result.content

    @pytest.mark.asyncio
    async def test_execute_unknown_skill(self):
        """Test executing unknown skill."""
        registry = SkillRegistry()
        result = await registry.execute("unknown", "")

        assert result.success is False
        assert "not found" in result.error

    def test_parse_command(self):
        """Test parsing slash command."""
        registry = SkillRegistry()

        # Test with slash command
        skill_name, args = registry.parse_command("/help")
        assert skill_name == "help"
        assert args == ""

        # Test with args
        skill_name, args = registry.parse_command("/tools detailed")
        assert skill_name == "tools"
        assert args == "detailed"

        # Test without slash command
        skill_name, args = registry.parse_command("hello")
        assert skill_name is None
        assert args == "hello"

    def test_get_help(self):
        """Test skill help."""
        registry = SkillRegistry()

        class TestSkill(Skill):
            name = "test"
            description = "Test skill"
            usage = "/test [args]"

            async def execute(self, args: str) -> SkillResult:
                return SkillResult(success=True, content="ok")

        skill = TestSkill()
        registry.register(skill)

        help_text = skill.get_help()
        assert "/test" in help_text
        assert "Test skill" in help_text
