import typer
from rich.console import Console
from .git_core import get_git_diff
from .ai_core import generate_commit_message
from .config import save_api_key

app = typer.Typer(help="Yapay Zeka Destekli Git Commit Asistanı")
console = Console()

@app.command()
def ayar(api_key: str = typer.Option(..., prompt="Google Gemini API Anahtarınız")):
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
        
    if not diff_text:
        console.print("[bold red]❌ Hata: Değişiklik bulunamadı! 'git add .' yapmayı unutmayın.[/bold red]")
        raise typer.Exit()

    console.print("[bold green]✔ Değişiklikler başarıyla yakalandı![/bold green]")
    console.print("[yellow]🧠 Yapay zeka analiz edip profesyonel bir mesaj üretiyor...[/yellow]")
    
    commit_mesaji = generate_commit_message(diff_text)
    
    if commit_mesaji.startswith("HATA"):
        console.print(f"[bold red]❌ {commit_mesaji}[/bold red]")
        raise typer.Exit()
        
    console.print(f"\n[bold green]✨ Önerilen Commit Mesajı:[/bold green]")
    console.print(f"[bold white]{commit_mesaji}[/bold white]\n")

def main():
    app()