"""File tool for file operations."""

import os
from pathlib import Path
from typing import Optional

from small_agent.tools.registry import Tool, ToolResult


class FileTool(Tool):
    """Tool for file operations."""

    name = "file"
    description = "Read, write, or manipulate files"
    auto_use = True

    @property
    def schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["read", "write", "append", "delete", "list", "exists"],
                    "description": "The file operation to perform",
                },
                "path": {
                    "type": "string",
                    "description": "File or directory path",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write (for write/append operations)",
                },
            },
            "required": ["operation", "path"],
        }

    async def execute(
        self,
        operation: str,
        path: str,
        content: Optional[str] = None,
    ) -> ToolResult:
        """Execute a file operation."""
        try:
            file_path = Path(path).expanduser()

            if operation == "read":
                if not file_path.exists():
                    return ToolResult(
                        success=False,
                        content="",
                        error=f"File not found: {path}",
                    )
                with open(file_path, "r") as f:
                    file_content = f.read()
                return ToolResult(
                    success=True,
                    content=file_content,
                )

            elif operation == "write":
                if content is None:
                    return ToolResult(
                        success=False,
                        content="",
                        error="Content required for write operation",
                    )
                file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, "w") as f:
                    f.write(content)
                return ToolResult(
                    success=True,
                    content=f"Written to {path}",
                )

            elif operation == "append":
                if content is None:
                    return ToolResult(
                        success=False,
                        content="",
                        error="Content required for append operation",
                    )
                with open(file_path, "a") as f:
                    f.write(content)
                return ToolResult(
                    success=True,
                    content=f"Appended to {path}",
                )

            elif operation == "delete":
                if file_path.is_file():
                    file_path.unlink()
                elif file_path.is_dir():
                    import shutil
                    shutil.rmtree(file_path)
                return ToolResult(
                    success=True,
                    content=f"Deleted {path}",
                )

            elif operation == "list":
                if not file_path.exists():
                    return ToolResult(
                        success=False,
                        content="",
                        error=f"Path not found: {path}",
                    )
                if not file_path.is_dir():
                    return ToolResult(
                        success=False,
                        content="",
                        error=f"Not a directory: {path}",
                    )
                items = [str(p) for p in file_path.iterdir()]
                return ToolResult(
                    success=True,
                    content="\n".join(items),
                    data=items,
                )

            elif operation == "exists":
                return ToolResult(
                    success=True,
                    content=f"exists: {file_path.exists()}",
                    data={"exists": file_path.exists()},
                )

            else:
                return ToolResult(
                    success=False,
                    content="",
                    error=f"Unknown operation: {operation}",
                )

        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=str(e),
            )
