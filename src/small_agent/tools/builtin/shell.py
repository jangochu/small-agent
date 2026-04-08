"""Shell tool for executing commands."""

import asyncio
from typing import Optional

from small_agent.tools.registry import Tool, ToolResult


class ShellTool(Tool):
    """Tool for executing shell commands."""

    name = "shell"
    description = "Execute a shell command"
    auto_use = True

    @property
    def schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute",
                },
                "cwd": {
                    "type": "string",
                    "description": "Working directory (optional)",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (default: 30)",
                },
            },
            "required": ["command"],
        }

    async def execute(
        self,
        command: str,
        cwd: Optional[str] = None,
        timeout: int = 30,
    ) -> ToolResult:
        """Execute a shell command."""
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout,
            )

            return ToolResult(
                success=proc.returncode == 0,
                content=stdout.decode() if stdout else "",
                error=stderr.decode() if stderr else None,
                data={"returncode": proc.returncode},
            )

        except asyncio.TimeoutError:
            return ToolResult(
                success=False,
                content="",
                error=f"Command timed out after {timeout}s",
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=str(e),
            )
