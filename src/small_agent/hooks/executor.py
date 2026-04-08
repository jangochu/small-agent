"""Harness event system and hook execution."""

import asyncio
import os
import shlex
import subprocess
from pathlib import Path
from typing import Any


class HarnessEvent:
    """Represents a harness event."""

    def __init__(self, name: str, context: dict[str, Any]):
        self.name = name
        self.context = context


class HookExecutor:
    """Executes shell hooks with context."""

    def __init__(self, working_dir: Path | None = None):
        self.working_dir = working_dir or Path.cwd()

    async def execute(
        self,
        command: str,
        event: HarnessEvent,
        timeout: int = 30,
    ) -> tuple[int, str, str]:
        """Execute a shell command with event context.

        Args:
            command: Shell command to execute
            event: Event containing context
            timeout: Maximum execution time in seconds

        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        # Expand ~ in command
        if command.startswith("~/"):
            command = os.path.expanduser(command)

        # Prepare environment with event context
        env = os.environ.copy()
        env["HARNESS_EVENT_NAME"] = event.name

        # Add context variables as env vars
        for key, value in event.context.items():
            env[f"HARNESS_{key.upper()}"] = str(value)

        # Run command
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=self.working_dir,
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout,
            )

            return (
                proc.returncode or 0,
                stdout.decode() if stdout else "",
                stderr.decode() if stderr else "",
            )

        except asyncio.TimeoutError:
            return (-1, "", f"Hook timed out after {timeout}s")

    def execute_sync(
        self,
        command: str,
        event: HarnessEvent,
        timeout: int = 30,
    ) -> tuple[int, str, str]:
        """Synchronous hook execution."""
        if command.startswith("~/"):
            command = os.path.expanduser(command)

        env = os.environ.copy()
        env["HARNESS_EVENT_NAME"] = event.name

        for key, value in event.context.items():
            env[f"HARNESS_{key.upper()}"] = str(value)

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                env=env,
                cwd=self.working_dir,
                timeout=timeout,
            )

            return (
                result.returncode,
                result.stdout.decode() if result.stdout else "",
                result.stderr.decode() if result.stderr else "",
            )

        except subprocess.TimeoutExpired:
            return (-1, "", f"Hook timed out after {timeout}s")
