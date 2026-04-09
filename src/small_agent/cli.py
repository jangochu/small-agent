"""CLI entry point."""

import asyncio
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.markdown import Markdown

from small_agent.agent import Agent
from small_agent.config import load_settings, get_default_settings_json, save_settings

app = typer.Typer(
    name="small-agent",
    help="A CLI agent powered by 阿里云百炼 with harness engineering patterns",
)
console = Console()


@app.command()
def init(
    output: Path = typer.Option(
        "settings.json",
        "--output",
        "-o",
        help="Output path for settings file",
    ),
):
    """Initialize a new settings.json file."""
    settings_json = get_default_settings_json()
    output.write_text(settings_json)
    console.print(f"[green]✓ Created[/green] {output}")
    console.print("\nTo get started:")
    console.print("  1. Set your DASHSCOPE_API_KEY environment variable")
    console.print("  2. Edit settings.json to customize configuration")
    console.print("  3. Run [bold]small-agent chat[/bold] to start")


@app.command()
def config(
    show_path: bool = typer.Option(False, "--path", help="Show settings file path"),
    edit: bool = typer.Option(False, "--edit", "-e", help="Open settings in editor"),
):
    """View or edit configuration."""
    settings = load_settings()

    if show_path:
        local = Path("settings.json")
        if local.exists():
            console.print(str(local.resolve()))
        else:
            home = Path.home() / ".small-agent" / "settings.json"
            if home.exists():
                console.print(str(home.resolve()))
            else:
                console.print("No settings file found. Run 'small-agent init' first.")
                raise typer.Exit(1)
        return

    if edit:
        editor = typer.edit(editor=True)
        console.print("Editing settings...")
        raise typer.Exit()

    console.print("[bold]Current Configuration:[/bold]\n")
    console.print(f"LLM Provider: [cyan]{settings.llm.provider}[/cyan]")
    console.print(f"Model: [cyan]{settings.llm.bailian.get('model', 'qwen-max')}[/cyan]")
    console.print(f"\nHooks:")
    if settings.hooks.before_tool:
        console.print(f"  before_tool: {settings.hooks.before_tool}")
    if settings.hooks.after_tool:
        console.print(f"  after_tool: {settings.hooks.after_tool}")
    if settings.hooks.before_prompt:
        console.print(f"  before_prompt: {settings.hooks.before_prompt}")
    if settings.hooks.after_response:
        console.print(f"  after_response: {settings.hooks.after_response}")
    console.print(f"\nMemory: {settings.memory.directory}")


@app.command()
def chat(
    prompt: str = typer.Argument(None, help="Prompt to send (optional for REPL mode)"),
):
    """Start interactive chat or send a single prompt."""
    if prompt is None:
        _chat_repl()
    else:
        asyncio.run(_chat_single(prompt))


def _chat_repl():
    """Run interactive REPL mode synchronously."""
    from prompt_toolkit import PromptSession
    from prompt_toolkit.key_binding import KeyBindings

    # Create agent synchronously
    try:
        agent = asyncio.run(Agent.create())
    except ValueError:
        console.print()
        console.print("[bold red]⚠️  API Key Not Configured[/bold red]")
        console.print()
        console.print("You need to configure your Alibaba Cloud Bailian API key.")
        console.print()
        console.print("[bold]Option 1: Set in settings.json[/bold]")
        console.print('  Add "api_key" to your settings.json:')
        console.print()
        console.print("  [dim]{[/dim]")
        console.print("    [cyan]\"llm\"[/cyan]: [dim]{[/dim]")
        console.print("      [cyan]\"bailian\"[/cyan]: [dim]{[/dim]")
        console.print("        [cyan]\"api_key\"[/cyan]: [green]\"sk-your-key-here\"[/green],")
        console.print("        [cyan]\"model\"[/cyan]: [cyan]\"qwen-max\"[/cyan]")
        console.print("      [dim]}[/dim]")
        console.print("    [dim]}[/dim]")
        console.print("  [dim]}[/dim]")
        console.print()
        console.print("[bold]Option 2: Set environment variable[/bold]")
        console.print("  [dim]# bash/zsh[/dim]")
        console.print("  [green]export DASHSCOPE_API_KEY=sk-your-key-here[/green]")
        console.print()
        console.print("  [dim]# fish[/dim]")
        console.print("  [green]set -gx DASHSCOPE_API_KEY sk-your-key-here[/green]")
        console.print()
        raise typer.Exit(1)

    console.print("[bold green]Small Agent CLI[/bold green]")
    console.print("Type 'exit' or 'quit' to exit, 'clear' to reset conversation\n")

    # Store conversation history for display
    history: list[tuple[str, str]] = []  # (user_input, assistant_response)

    # Set up key bindings for multi-line input
    bindings = KeyBindings()

    @bindings.add("escape", "enter")
    def _(event):
        """Insert newline on Escape+Enter."""
        event.current_buffer.insert_text("\n")

    session = PromptSession(
        key_bindings=bindings,
    )

    while True:
        # Clear screen and redraw history
        print("\033[2J\033[H", end="")  # ANSI clear screen
        console.print("[bold green]Small Agent CLI[/bold green]")
        console.print("Type 'exit' or 'quit' to exit, 'clear' to reset conversation\n")

        # Draw history with user input and assistant response
        for user_input, assistant_response in history:
            console.print(f"[bold blue]• 你：[/bold blue] {user_input}")
            console.print(f"[bold green]• 助手：[/bold green] {assistant_response}")
            console.print()

        # Draw input box with separators
        console.print("━" * 60, style="dim")
        try:
            user_input = session.prompt("")
        except (EOFError, KeyboardInterrupt):
            console.print("\nGoodbye!")
            break
        console.print("━" * 60, style="dim")
        console.print()

        user_input = user_input.strip()

        if user_input.lower() in ("exit", "quit"):
            print("\033[2J\033[H", end="")
            console.print("[bold green]Small Agent CLI[/bold green]")
            console.print("Type 'exit' or 'quit' to exit\n")
            for user_input, assistant_response in history:
                console.print(f"[bold blue]• 你：[/bold blue] {user_input}")
                console.print(f"[bold green]• 助手：[/bold green] {assistant_response}")
                console.print()
            console.print("Goodbye!")
            break

        # Check for slash commands
        skill_name, args = agent.parse_skill_command(user_input)
        if skill_name:
            result = asyncio.run(agent.execute_skill(skill_name, args))
            if result.success:
                console.print(Markdown(result.content))
            else:
                console.print(f"[red]Error:[/red] {result.error}")
            input("[Press Enter to continue...]")
            continue

        if not user_input:
            continue

        # Get response
        response = asyncio.run(agent.chat(user_input))
        history.append((user_input, response.content))


async def _chat_single(prompt: str):
    """Handle single prompt mode."""
    try:
        agent = await Agent.create()
    except ValueError:
        console.print()
        console.print("[bold red]⚠️  API Key Not Configured[/bold red]")
        console.print()
        console.print("You need to configure your Alibaba Cloud Bailian API key.")
        console.print()
        console.print("[bold]Option 1: Set in settings.json[/bold]")
        console.print('  Add "api_key" to your settings.json:')
        console.print()
        console.print("  [dim]{[/dim]")
        console.print("    [cyan]\"llm\"[/cyan]: [dim]{[/dim]")
        console.print("      [cyan]\"bailian\"[/cyan]: [dim]{[/dim]")
        console.print("        [cyan]\"api_key\"[/cyan]: [green]\"sk-your-key-here\"[/green],")
        console.print("        [cyan]\"model\"[/cyan]: [cyan]\"qwen-max\"[/cyan]")
        console.print("      [dim]}[/dim]")
        console.print("    [dim]}[/dim]")
        console.print("  [dim]}[/dim]")
        console.print()
        console.print("[bold]Option 2: Set environment variable[/bold]")
        console.print("  [dim]# bash/zsh[/dim]")
        console.print("  [green]export DASHSCOPE_API_KEY=sk-your-key-here[/green]")
        console.print()
        console.print("  [dim]# fish[/dim]")
        console.print("  [green]set -gx DASHSCOPE_API_KEY sk-your-key-here[/green]")
        console.print()
        raise typer.Exit(1)

    with console.status("[bold green]Thinking..."):
        response = await agent.chat(prompt)
    console.print()
    console.print(Markdown(response.content))


async def _run_async(prompt: str, stream: bool):
    """Async implementation of run command."""
    try:
        agent = await Agent.create()
    except ValueError:
        console.print()
        console.print("[bold red]⚠️  API Key Not Configured[/bold red]")
        console.print()
        console.print("You need to configure your Alibaba Cloud Bailian API key.")
        console.print()
        console.print("[bold]Option 1: Set in settings.json[/bold]")
        console.print('  Add "api_key" to your settings.json:')
        console.print()
        console.print("  [dim]{[/dim]")
        console.print("    [cyan]\"llm\"[/cyan]: [dim]{[/dim]")
        console.print("      [cyan]\"bailian\"[/cyan]: [dim]{[/dim]")
        console.print("        [cyan]\"api_key\"[/cyan]: [green]\"sk-your-key-here\"[/green],")
        console.print("        [cyan]\"model\"[/cyan]: [cyan]\"qwen-max\"[/cyan]")
        console.print("      [dim]}[/dim]")
        console.print("    [dim]}[/dim]")
        console.print("  [dim]}[/dim]")
        console.print()
        console.print("[bold]Option 2: Set environment variable[/bold]")
        console.print("  [dim]# bash/zsh[/dim]")
        console.print("  [green]export DASHSCOPE_API_KEY=sk-your-key-here[/green]")
        console.print()
        console.print("  [dim]# fish[/dim]")
        console.print("  [green]set -gx DASHSCOPE_API_KEY sk-your-key-here[/green]")
        console.print()
        raise typer.Exit(1)

    if stream:
        console.print()
        async for chunk in agent.llm_provider.stream(
            messages=[{"role": "user", "content": prompt}],
        ):
            sys.stdout.write(chunk)
            sys.stdout.flush()
        console.print()
    else:
        with console.status("[bold green]Thinking..."):
            response = await agent.run(prompt)
        console.print()
        console.print(Markdown(response.content))


@app.command()
def run(
    prompt: str = typer.Argument(..., help="Prompt to send"),
    stream: bool = typer.Option(False, "--stream", "-s", help="Stream response"),
):
    """Run a single prompt and print response."""
    asyncio.run(_run_async(prompt, stream))


def main():
    """Entry point for CLI."""
    app()


if __name__ == "__main__":
    app()
