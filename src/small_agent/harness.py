"""Agent harness - orchestrates events, hooks, and LLM."""

import json
from pathlib import Path
from typing import Any, Optional

from small_agent.config import Settings, HooksConfig
from small_agent.hooks.executor import HookExecutor, HarnessEvent
from small_agent.llm.base import LLMProvider, LLMResponse, LLMConfig
from small_agent.tools.registry import ToolRegistry


class AgentHarness:
    """Main agent harness that orchestrates events and hooks."""

    def __init__(
        self,
        settings: Settings,
        llm_provider: LLMProvider,
        working_dir: Path | None = None,
        tool_registry: Optional[ToolRegistry] = None,
    ):
        self.settings = settings
        self.llm_provider = llm_provider
        self.hook_executor = HookExecutor(working_dir)
        self.conversation_history: list[dict[str, str]] = []
        self.tool_registry = tool_registry
        self._max_tool_iterations = 5  # Prevent infinite loops

    def _get_hook_command(self, event_name: str) -> str | None:
        """Get hook command for an event."""
        hook_map = {
            "before_tool": self.settings.hooks.before_tool,
            "after_tool": self.settings.hooks.after_tool,
            "before_prompt": self.settings.hooks.before_prompt,
            "after_response": self.settings.hooks.after_response,
        }
        return hook_map.get(event_name)

    async def trigger_event(
        self,
        event_name: str,
        context: Optional[dict[str, Any]] = None,
    ) -> tuple[int, str, str]:
        """Trigger an event and run associated hooks.

        Args:
            event_name: Name of the event
            context: Event context data

        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        context = context or {}
        event = HarnessEvent(event_name, context)
        command = self._get_hook_command(event_name)

        if command:
            return await self.hook_executor.execute(command, event)

        return (0, "", "")

    async def _execute_tool_calls(
        self,
        tool_calls: list[dict],
    ) -> tuple[list[dict], bool]:
        """Execute tool calls and return results as messages.

        Returns:
            Tuple of (results list, has_error)
        """
        results = []
        has_error = False

        for tc in tool_calls:
            tool_id = tc.get("id", "")
            func = tc.get("function", {})
            tool_name = func.get("name", "")
            args_str = func.get("arguments", "{}")

            try:
                args = json.loads(args_str) if isinstance(args_str, str) else args_str
            except json.JSONDecodeError:
                results.append({
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "content": f"Error: Invalid arguments: {args_str}",
                })
                has_error = True
                continue

            # Trigger before_tool hook
            await self.trigger_event("before_tool", {
                "tool_name": tool_name,
                "arguments": args,
            })

            # Execute the tool
            result = await self.tool_registry.execute(tool_name, **args) if self.tool_registry else None

            # Trigger after_tool hook
            await self.trigger_event("after_tool", {
                "tool_name": tool_name,
                "arguments": args,
                "result": result.content if result else "No result",
            })

            # Add tool result to messages
            if result and result.success:
                results.append({
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "content": result.content,
                })
            else:
                error_msg = result.error if result else "Tool not found"
                results.append({
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "content": f"Error: {error_msg}",
                })
                has_error = True

        return results, has_error

    async def process_prompt(
        self,
        prompt: str,
        options: Optional[dict[str, Any]] = None,
        tools: Optional[list[dict]] = None,
    ) -> LLMResponse:
        """Process a user prompt and generate response.

        Args:
            prompt: User input
            options: Generation options
            tools: Optional list of tool definitions for function calling

        Returns:
            LLMResponse with generated content
        """
        options = options or {}

        # Trigger before_prompt hook
        await self.trigger_event("before_prompt", {"prompt": prompt})

        # Add user message to history
        self.conversation_history.append({"role": "user", "content": prompt})

        # Main loop for tool execution
        iterations = 0
        final_response = None
        last_error = None

        while iterations < self._max_tool_iterations:
            iterations += 1

            # Generate response
            response = await self.llm_provider.generate(
                messages=self.conversation_history,
                config=LLMConfig(
                    provider_type=self.llm_provider.provider_type,
                    model=self.settings.llm.bailian.get("model", "qwen-max"),
                ),
                tools=tools,
                **options,
            )

            # Add assistant response to history
            assistant_message = {
                "role": "assistant",
                "content": response.content if response.content else None,
            }

            # Handle tool calls if present
            if response.tool_calls and self.tool_registry:
                # Add assistant message with tool_calls to history
                if response.raw and isinstance(response.raw, dict) and response.raw.get('output'):
                    choices = response.raw['output'].get('choices', [])
                    if choices:
                        message = choices[0].get('message', {})
                        if message.get('tool_calls'):
                            # Must include the full tool_calls structure
                            assistant_message['tool_calls'] = message['tool_calls']
                            # Content must be None (not empty string) for tool calls
                            assistant_message['content'] = None

                self.conversation_history.append(assistant_message)

                # Execute tool calls
                tool_results, has_error = await self._execute_tool_calls(response.tool_calls)
                self.conversation_history.extend(tool_results)

                # Track last error for fallback
                if has_error:
                    last_error = "Tool execution failed. See tool results for details."

                # Continue loop to get final response
                continue
            else:
                # No tool calls, this is the final response
                self.conversation_history.append(assistant_message)
                final_response = response
                break

        # Trigger after_response hook
        if final_response:
            await self.trigger_event(
                "after_response",
                {"response": final_response.content, "prompt": prompt},
            )
            return final_response

        # Fallback: return last response if we exited loop without final response
        return response

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history = []

    def get_history(self) -> list[dict[str, str]]:
        """Get conversation history."""
        return self.conversation_history.copy()
