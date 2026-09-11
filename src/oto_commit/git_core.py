import re
import subprocess

# Sır içerme ihtimali yüksek dosyalar. Bunlar diff'e hiç alınmaz,
# dolayısıyla yapay zekaya da gönderilmez.
SENSITIVE_FILE_GLOBS = [
    "*.env", ".env.*",
    "*.pem", "*.key", "*.p12", "*.pfx", "*.ppk", "*.jks", "*.keystore",
    "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519",
]

# Diff içinde sır gibi görünen kalıplar. Eşleşen metnin kendisi asla raporlanmaz.
SECRET_PATTERNS = [
    ("Google API anahtarı", re.compile(r"AIza[0-9A-Za-z_\-]{35}")),
    ("OpenAI/Anthropic anahtarı", re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}")),
    ("AWS erişim anahtarı", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}")),
    ("Özel anahtar (PEM)", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("Şifre/sır ataması", re.compile(
        r"\b(?:password|passwd|secret|api[_-]?key|token)\w*\s*[:=]\s*['\"][^'\"\s]{8,}['\"]",
        re.IGNORECASE,
    )),
]

def _run_git(args):
    return subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        check=True,
        encoding='utf-8'
    )

def _pathspecs(exclude: bool):
    # "top": alt klasörden çalıştırılsa bile depo kökünden eşleşir.
    # "glob": **/ ile her derinlikteki dosyayı yakalar.
    magic = "top,glob,exclude" if exclude else "top,glob"
    return [f":({magic})**/{g}" for g in SENSITIVE_FILE_GLOBS]

def get_git_diff() -> str:
    try:
        result = _run_git(["diff", "--staged", "--", *_pathspecs(exclude=True)])
        return result.stdout.strip()
    
    except subprocess.CalledProcessError:
        return "HATA: Bu klasör bir Git deposu değil (git init çalıştırılmamış)."
    except FileNotFoundError:
        return "HATA: Bilgisayarında Git komutu bulunamadı."

def get_excluded_files() -> list:
    """Staged olup hassas görüldüğü için diff'e alınmayan dosyaların adları."""
    try:
        result = _run_git(["diff", "--staged", "--name-only", "-z", "--", *_pathspecs(exclude=False)])
        return [name for name in result.stdout.split("\0") if name]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []

def find_secret_patterns(diff_text: str) -> list:
    """Diff içinde sır gibi görünen satırları arar; (dosya, açıklama) çiftleri döner."""
    findings = []
    current_file = "?"
    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            current_file = line.split(" b/", 1)[-1]
            continue
        for name, pattern in SECRET_PATTERNS:
            if pattern.search(line) and (current_file, name) not in findings:
                findings.append((current_file, name))
    return findings
