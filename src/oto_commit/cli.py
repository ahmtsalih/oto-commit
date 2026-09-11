import re
import typer
from rich.console import Console
from rich.text import Text
from .git_core import get_git_diff, get_excluded_files, find_secret_patterns
from .ai_core import generate_commit_message
from .config import save_api_key

app = typer.Typer(help="Yapay Zeka Destekli Git Commit Asistanı")
console = Console()

# OSC (ESC ] ... BEL/ST), CSI/diğer ESC dizileri ve \n, \t dışındaki kontrol karakterleri.
_CONTROL_CHARS = re.compile(
    r"\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)"
    r"|\x1b[@-_][0-?]*[ -/]*[@-~]"
    r"|[\x00-\x08\x0b-\x1f\x7f]"
)

def _print_untrusted(text: str, style: str = ""):
    """Model/API'den gelen metni markup yorumlamadan ve terminal kaçış dizilerini
    ayıklayarak basar; diff'e gömülü bir prompt injection terminali kandıramaz."""
    console.print(Text(_CONTROL_CHARS.sub("", text), style=style))

@app.command()
def ayar(
    api_key: str = typer.Option(
        ...,
        prompt="Google Gemini API Anahtarınız",
        hide_input=True,
        help="Komut satırında vermek önerilmez (shell geçmişine düşer); boş bırakın, gizli olarak sorulur.",
    )
):
    save_api_key(api_key)
    console.print("[bold green]✔ API Anahtarı başarıyla kaydedildi![/bold green]")

@app.command()
def uret():
    console.print("\n[bold cyan]🤖 AI Asistanı uyandırılıyor...[/bold cyan]")
    console.print("[yellow]🔍 Değişen kod satırları taranıyor...[/yellow]")
    
    diff_text = get_git_diff()
    
    if diff_text.startswith("HATA"):
        console.print(f"[bold red]❌ {diff_text}[/bold red]")
        raise typer.Exit()

    excluded = get_excluded_files()
    if excluded:
        console.print("[yellow]⚠ Hassas görünen dosyalar yapay zekaya gönderilmedi:[/yellow]")
        for name in excluded:
            _print_untrusted(f"   • {name}", "yellow")
        
    if not diff_text:
        console.print("[bold red]❌ Hata: Değişiklik bulunamadı! 'git add .' yapmayı unutmayın.[/bold red]")
        raise typer.Exit()

    findings = find_secret_patterns(diff_text)
    if findings:
        console.print("[bold red]⚠ Diff içinde sır gibi görünen içerik var:[/bold red]")
        for file_name, kind in findings:
            _print_untrusted(f"   • {file_name}: {kind}", "red")
        console.print("[red]Bu içerik olduğu gibi Google'a gönderilecek.[/red]")
        if not typer.confirm("Yine de gönderilsin mi?", default=False):
            raise typer.Exit()

    console.print("[bold green]✔ Değişiklikler başarıyla yakalandı![/bold green]")
    console.print("[yellow]🧠 Yapay zeka analiz edip profesyonel bir mesaj üretiyor...[/yellow]")
    
    commit_mesaji = generate_commit_message(diff_text)
    
    if commit_mesaji.startswith("HATA"):
        _print_untrusted(f"❌ {commit_mesaji}", "bold red")
        raise typer.Exit()
        
    console.print(f"\n[bold green]✨ Önerilen Commit Mesajı:[/bold green]")
    _print_untrusted(commit_mesaji, "bold white")
    console.print()

def main():
    app()
