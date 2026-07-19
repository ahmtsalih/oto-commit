import subprocess

def get_git_diff() -> str:
    try:
        result = subprocess.run(
            ["git", "diff", "--staged"], 
            capture_output=True, 
            text=True, 
            check=True,
            encoding='utf-8'
        )
        return result.stdout.strip()
    
    except subprocess.CalledProcessError:
        return "HATA: Bu klasör bir Git deposu değil (git init çalıştırılmamış)."
    except FileNotFoundError:
        return "HATA: Bilgisayarında Git komutu bulunamadı."