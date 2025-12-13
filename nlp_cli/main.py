"""
NLP CLI - Main Entry Point

A natural language to shell command translator using local LLMs.
"""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.prompt import Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich import box
from typing import Optional
import sys

from .local_translator import create_translator, TranslationResult
from .executor import create_executor, RiskLevel
from .system_info import get_system_context

# Initialize Rich console for beautiful output
console = Console()

# Initialize Typer app
app = typer.Typer(
    name="nlp",
    help="🧠 Natural Language to Shell Command Translator",
    add_completion=False,
    rich_markup_mode="rich",
    no_args_is_help=False,
)


def print_banner():
    """Display the application banner."""
    banner = """
[bold cyan]╔═══════════════════════════════════════════════════════════╗
║   [bold white]NLP CLI[/bold white] - Natural Language Shell Commander           ║
║   [dim]Powered by Local ML (TF-IDF + SVM) - No LLM Required![/dim]   ║
╚═══════════════════════════════════════════════════════════╝[/bold cyan]
"""
    console.print(banner)


def get_risk_style(risk_level: RiskLevel) -> str:
    """Get Rich style string for risk level."""
    styles = {
        RiskLevel.LOW: "green",
        RiskLevel.MEDIUM: "yellow",
        RiskLevel.HIGH: "red",
        RiskLevel.CRITICAL: "bold red on white",
    }
    return styles.get(risk_level, "white")


def get_risk_emoji(risk_level: RiskLevel) -> str:
    """Get emoji for risk level."""
    emojis = {
        RiskLevel.LOW: "[OK]",
        RiskLevel.MEDIUM: "[WARN]",
        RiskLevel.HIGH: "[DANGER]",
        RiskLevel.CRITICAL: "[CRITICAL]",
    }
    return emojis.get(risk_level, "?")


def _run_translate(
    query: str,
    execute: bool = True,
    yes: bool = False,
    explain: bool = False,
    timeout: int = 30,
):
    """Core translation logic used by both the callback and translate command."""
    try:
        # Show progress while loading
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Translating your request...[/bold blue]"),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task("translate", total=None)
            
            # Initialize translator
            translator = create_translator()
            
            # Translate the query
            results = translator.translate(query)
        
        # Handle empty results (empty query)
        if not results:
            return

        # Get system context for display
        context = get_system_context()
        executor = create_executor(timeout=timeout)
        
        for i, result in enumerate(results):
            if not result.success:
                console.print(
                    Panel(
                        f"[red]Translation failed:[/red]\n{result.error_message}",
                        title="Error",
                        border_style="red",
                    )
                )
                continue
            
            # Ambiguity Check (Feature Request)
            # If top confidence is low (< 50%) and there's a close second alternative
            if not yes and result.confidence < 0.5 and result.alternative_intents:
                alt_intent, alt_score = result.alternative_intents[0]
                if abs(result.confidence - alt_score) < 0.15:
                    console.print(f"\n[bold yellow]?? I'm not entirely sure. Did you mean:[/bold yellow]")
                    console.print(f"1. [cyan]{result.intent}[/cyan] ({result.confidence:.0%}) -> {result.description}")
                    console.print(f"2. [cyan]{alt_intent}[/cyan] ({alt_score:.0%})")
                    
                    if not Confirm.ask("Is the first option correct?"):
                        console.print("[yellow]Skipping command.[/yellow]")
                        continue

            risk_level, risk_reasons = executor.assess_risk(result.command)
            
            # Display the translated command
            console.print()
            if len(results) > 1:
                console.print(f"[bold]Command {i+1}/{len(results)}:[/bold]")
            
            # Command panel with syntax highlighting
            syntax = Syntax(
                result.command,
                "powershell" if "windows" in context.os_type.value else "bash",
                theme="monokai",
                line_numbers=False,
            )
            
            risk_style = get_risk_style(risk_level)
            risk_emoji = get_risk_emoji(risk_level)
            
            console.print(
                Panel(
                    syntax,
                    title=f"[bold white]Generated Command[/bold white] | {risk_emoji} [{risk_style}]{risk_level.value.upper()}[/{risk_style}]",
                    subtitle=f"[dim]Model: {result.model_used} | Shell: {context.get_shell_name()}[/dim]",
                    border_style="cyan",
                    box=box.ROUNDED,
                )
            )
            
            # Show risk warnings if any
            if risk_reasons:
                warning_text = "\n".join(f"• {reason}" for reason in risk_reasons)
                console.print(
                    Panel(
                        f"[{risk_style}]{warning_text}[/{risk_style}]",
                        title=f"{risk_emoji} Risk Assessment",
                        border_style=risk_style,
                    )
                )
            
            # Show explanation if requested
            if explain:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[bold blue]Generating explanation...[/bold blue]"),
                    console=console,
                    transient=True,
                ) as progress:
                    progress.add_task("explain", total=None)
                    explanation = translator.explain_command(result.command)
                
                console.print(
                    Panel(
                        explanation,
                        title="📖 Explanation",
                        border_style="blue",
                    )
                )
            
            # Execute if requested
            if execute:
                console.print()
                
                # Confirm before execution (unless --yes)
                if yes:
                    should_execute = True
                else:
                    if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                        console.print(
                            f"[bold {risk_style}]{risk_emoji} WARNING: This command has been flagged as {risk_level.value.upper()} risk![/{risk_style}]"
                        )
                    should_execute = Confirm.ask(
                        "[bold yellow]Execute this command?[/bold yellow]",
                        default=risk_level == RiskLevel.LOW,
                    )
                
                if should_execute:
                    console.print()
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[bold green]Executing...[/bold green]"),
                        console=console,
                        transient=True,
                    ) as progress:
                        progress.add_task("execute", total=None)
                        exec_result = executor.execute(result.command)
                    
                    if exec_result.success:
                        if exec_result.output:
                            console.print(
                                Panel(
                                    exec_result.output,
                                    title="Output",
                                    border_style="green",
                                )
                            )
                        else:
                            console.print("[green]Command executed successfully (no output)[/green]")
                    else:
                        console.print(
                            Panel(
                                exec_result.stderr or "Unknown error",
                                title=f"Failed (Exit Code: {exec_result.return_code})",
                                border_style="red",
                            )
                        )
                        # Don't exit the whole loop if one fails, but maybe ask to continue?
                        if i < len(results) - 1:
                            if not Confirm.ask("Command failed. Continue with next commands?"):
                                break
                else:
                    console.print("[yellow]Command cancelled.[/yellow]")
                    # If cancelled, maybe stop the chain?
                    if i < len(results) - 1:
                        if not Confirm.ask("Continue with next commands?"):
                            break
    
    except typer.Exit:
        raise
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled.[/yellow]")
        raise typer.Exit(130)
    except Exception as e:
        console.print(
            Panel(
                f"[red]{str(e)}[/red]",
                title="Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)


def interactive_learn():
    """
    Interactive mode to add new training data.
    """
    from .training_data import add_training_example, get_intent_list
    
    console.print(Panel("🎓 [bold white]Teach NLP CLI[/bold white]", border_style="cyan"))
    console.print("Add a new command to the training data.\n")
    
    # Get the natural language command
    text = typer.prompt("Enter the natural language command (e.g., 'show hidden files')")
    
    # Get the intent
    intents = get_intent_list()
    console.print("\n[bold]Existing Intents:[/bold]")
    
    # Show intents in columns
    columns = typer.get_terminal_size()[0] // 25
    rows = len(intents) // columns + 1
    
    grid = Table.grid(expand=True)
    for _ in range(columns):
        grid.add_column()
        
    for i in range(0, len(intents), columns):
        row_items = intents[i:i+columns]
        grid.add_row(*row_items)
        
    console.print(grid)
    console.print()
    
    intent = typer.prompt("Enter the intent (or new intent name)")
    
    # Confirm
    console.print(f"\n[bold]Adding Example:[/bold]")
    console.print(f"Text:   [cyan]{text}[/cyan]")
    console.print(f"Intent: [green]{intent}[/green]")
    
    if Confirm.ask("Is this correct?"):
        if add_training_example(text, intent):
            console.print("[green]✅ Added successfully![/green]")
            
            if Confirm.ask("Do you want to retrain the model now?"):
                # Call retrain command logic
                from .intent_classifier import get_classifier
                
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[bold blue]Retraining model...[/bold blue]"),
                    console=console,
                    transient=True,
                ) as progress:
                    progress.add_task("train", total=None)
                    get_classifier().retrain()
                
                console.print("[green]✅ Model retrained![/green]")
        else:
            console.print("[yellow]⚠️  Example already exists.[/yellow]")
    else:
        console.print("[yellow]Cancelled.[/yellow]")


@app.command(name="run")
def translate_cmd(
    query: str = typer.Argument(
        ...,
        help="Natural language description of the command you want"
    ),
    execute: bool = typer.Option(
        True,
        "--execute/--no-execute",
        "-e/-n",
        help="Execute the command after confirmation"
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation prompt (use with caution!)"
    ),
    explain: bool = typer.Option(
        False,
        "--explain",
        "-x",
        help="Show explanation of what the command does"
    ),
    timeout: int = typer.Option(
        30,
        "--timeout",
        "-t",
        help="Command execution timeout in seconds"
    ),
):
    """
    🚀 Translate natural language to shell commands (same as passing query directly).
    """
    _run_translate(query, execute, yes, explain, timeout)


@app.command()
def info():
    """
    📊 Display system and model information.
    """
    context = get_system_context()
    
    print_banner()
    
    # System info table
    table = Table(title="System Information", box=box.ROUNDED)
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("Operating System", context.get_os_name())
    table.add_row("OS Version", context.os_version[:50] + "..." if len(context.os_version) > 50 else context.os_version)
    table.add_row("Shell", context.get_shell_name())
    table.add_row("Architecture", context.architecture)
    table.add_row("Current Directory", context.current_directory)
    
    console.print(table)
    console.print()
    
    # Get NLP model info
    try:
        translator = create_translator()
        model_info = translator.get_model_info()
        
        model_table = Table(title="NLP Model", box=box.ROUNDED)
        model_table.add_column("Property", style="cyan")
        model_table.add_column("Value", style="white")
        
        model_table.add_row("Model Type", model_info.get("name", "Unknown"))
        model_table.add_row("Requires Internet", "No ✅" if not model_info.get("requires_internet") else "Yes")
        model_table.add_row("Supported Intents", str(model_info.get("num_intents", 0)))
        
        console.print(model_table)
        
    except Exception as e:
        console.print(f"[yellow]⚠️  Error loading model: {e}[/yellow]")


@app.command()
def intents():
    """
    📋 List all supported command intents.
    """
    from .command_templates import COMMAND_TEMPLATES
    
    table = Table(title="Supported Intents", box=box.ROUNDED)
    table.add_column("Intent", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Risk", style="dim")
    
    for intent, template in sorted(COMMAND_TEMPLATES.items()):
        risk = "[red]⚠️ Dangerous[/red]" if template.is_dangerous else "[green]Safe[/green]"
        table.add_row(intent, template.description, risk)
    
    console.print(table)
    console.print(f"\n[dim]Total: {len(COMMAND_TEMPLATES)} supported operations[/dim]")


@app.command()
def retrain():
    """
    🔄 Retrain the NLP model with latest training data.
    """
    from .intent_classifier import get_classifier
    
    console.print("[bold blue]Retraining the intent classifier...[/bold blue]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]Training model...[/bold blue]"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task("train", total=None)
        classifier = get_classifier()
        metrics = classifier.retrain()
    
    table = Table(title="Training Complete", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("Accuracy (CV)", f"{metrics['accuracy']:.2%}")
    table.add_row("Std Deviation", f"{metrics['std']:.4f}")
    table.add_row("Training Samples", str(metrics['num_samples']))
    table.add_row("Unique Intents", str(metrics['num_intents']))
    
    console.print(table)
    console.print("[green]Model retrained successfully![/green]")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    query: Optional[str] = typer.Argument(
        None,
        help="Natural language description of the command you want"
    ),
    execute: bool = typer.Option(
        True,
        "--execute/--no-execute",
        "-e/-n",
        help="Execute the command after confirmation"
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation prompt (use with caution!)"
    ),
    explain: bool = typer.Option(
        False,
        "--explain",
        "-x",
        help="Show explanation of what the command does"
    ),
    timeout: int = typer.Option(
        30,
        "--timeout",
        "-t",
        help="Command execution timeout in seconds"
    ),
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show version information"
    ),
):
    """
    🧠 NLP CLI - Transform natural language into shell commands.
    
    Powered by local AI models. No internet required!
    
    Usage:
        nlp "list all files"
        nlp "create folder named test" --explain
        nlp "find python files" -y
    """
    if version:
        from . import __version__
        console.print(f"[cyan]NLP CLI[/cyan] version [bold]{__version__}[/bold]")
        raise typer.Exit()
    
    # If a subcommand is being invoked, let it handle everything
    if ctx.invoked_subcommand is not None:
        return
    
    # If no query provided, show help
    if query is None:
        print_banner()
        console.print("Run [cyan]nlp --help[/cyan] for usage information.")
        console.print("\n[bold]Quick Start:[/bold]")
        console.print('  [cyan]nlp "list all files"[/cyan]')
        console.print('  [cyan]nlp "create folder named test"[/cyan]')
        console.print('  [cyan]nlp "find python files" --explain[/cyan]')
        return
    
    # Check if query matches a subcommand name (user might have forgotten quotes)
    subcommand_names = ["info", "intents", "retrain", "run", "learn"]
    if query.lower() in subcommand_names:
        # Redirect to the appropriate subcommand
        if query.lower() == "info":
            ctx.invoke(info)
            return
        elif query.lower() == "intents":
            ctx.invoke(intents)
            return
        elif query.lower() == "retrain":
            ctx.invoke(retrain)
            return
        elif query.lower() == "learn":
            interactive_learn()
            return

    
    # Otherwise, run the translate logic directly
    _run_translate(query, execute, yes, explain, timeout)


def cli():
    """Entry point for the CLI application."""
    app()


if __name__ == "__main__":
    cli()

