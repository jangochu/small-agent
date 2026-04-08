"""HTTP tool for making HTTP requests."""

from typing import Optional

import aiohttp
from small_agent.tools.registry import Tool, ToolResult


class HttpTool(Tool):
    """Tool for making HTTP requests."""

    name = "http"
    description = "Make HTTP requests"
    auto_use = True

    @property
    def schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "method": {
                    "type": "string",
                    "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"],
                    "description": "HTTP method",
                },
                "url": {
                    "type": "string",
                    "description": "URL to request",
                },
                "headers": {
                    "type": "object",
                    "description": "Request headers",
                },
                "body": {
                    "type": "string",
                    "description": "Request body (for POST/PUT/PATCH)",
                },
            },
            "required": ["method", "url"],
        }

    async def execute(
        self,
        method: str,
        url: str,
        headers: Optional[dict] = None,
        body: Optional[str] = None,
    ) -> ToolResult:
        """Make an HTTP request."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method,
                    url,
                    headers=headers,
                    data=body,
                ) as response:
                    content = await response.text()
                    return ToolResult(
                        success=200 <= response.status < 300,
                        content=content,
                        data={
                            "status": response.status,
                            "headers": dict(response.headers),
                        },
                    )

        except aiohttp.ClientError as e:
            return ToolResult(
                success=False,
                content="",
                error=str(e),
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=str(e),
            )
