import re
import typer
from rich.console import Console
from rich.text import Text
from .git_core import get_git_diff, get_excluded_files, find_secret_patterns
from .ai_core import generate_commit_message
from .config import save_api_key

# Local variables (which may hold the API key) must never be dumped into an unexpected traceback.
app = typer.Typer(help="AI-powered Git commit message assistant", pretty_exceptions_show_locals=False)
console = Console()

# OSC (ESC ] ... BEL/ST), CSI and other ESC sequences, and every C0/C1 control character
# except \n and \t (8-bit C1 codes such as U+009B act like ESC [ on xterm/VTE terminals).
_CONTROL_CHARS = re.compile(
    r"\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)"
    r"|\x1b[@-_][0-?]*[ -/]*[@-~]"
    r"|[\x00-\x08\x0b-\x1f\x7f-\x9f]"
)

def _print_untrusted(text: str, style: str = ""):
    """Print text that came from the model/API without interpreting Rich markup and with
    terminal escape sequences stripped, so a prompt injection in the diff cannot drive the terminal."""
    console.print(Text(_CONTROL_CHARS.sub("", text), style=style))

@app.command()
def setup(
    api_key: str = typer.Option(
        ...,
        prompt="Your Google Gemini API key",
        hide_input=True,
        help="Passing the key on the command line is not recommended (it ends up in your shell history); omit it to be prompted with hidden input.",
    )
):
    """Store your Google Gemini API key."""
    save_api_key(api_key)
    console.print("[bold green]✔ API key saved.[/bold green]")

@app.command()
def generate():
    """Generate a commit message for the staged changes."""
    console.print("\n[bold cyan]🤖 Waking up the AI assistant...[/bold cyan]")
    console.print("[yellow]🔍 Scanning staged changes...[/yellow]")

    diff_text = get_git_diff()

    if diff_text.startswith("ERROR"):
        console.print(f"[bold red]❌ {diff_text}[/bold red]")
        raise typer.Exit()

    excluded = get_excluded_files()
    if excluded:
        console.print("[yellow]⚠ These files look sensitive and were not sent to the AI:[/yellow]")
        for name in excluded:
            _print_untrusted(f"   • {name}", "yellow")

    if not diff_text:
        console.print("[bold red]❌ Error: no staged changes found. Did you forget 'git add .'?[/bold red]")
        raise typer.Exit()

    findings = find_secret_patterns(diff_text)
    if findings:
        console.print("[bold red]⚠ The diff contains content that looks like a secret:[/bold red]")
        for file_name, kind in findings:
            _print_untrusted(f"   • {file_name}: {kind}", "red")
        console.print("[red]This content would be sent to Google as-is.[/red]")
        if not typer.confirm("Send it anyway?", default=False):
            raise typer.Exit()

    console.print("[bold green]✔ Changes captured.[/bold green]")
    console.print("[yellow]🧠 The AI is analysing the changes and writing a message...[/yellow]")

    commit_message = generate_commit_message(diff_text)

    if commit_message.startswith("ERROR"):
        _print_untrusted(f"❌ {commit_message}", "bold red")
        raise typer.Exit()

    console.print(f"\n[bold green]✨ Suggested commit message:[/bold green]")
    _print_untrusted(commit_message, "bold white")
    console.print()

def main():
    app()
