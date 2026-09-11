import re
import subprocess

# Files that very likely contain secrets. They are left out of the diff
# entirely, so they are never sent to the AI.
SENSITIVE_FILE_GLOBS = [
    "*.env", ".env.*",
    "*.pem", "*.key", "*.p12", "*.pfx", "*.ppk", "*.jks", "*.keystore",
    "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519",
]

# Things in a diff that look like secrets. The matched text itself is never reported.
SECRET_PATTERNS = [
    ("Google API key", re.compile(r"AIza[0-9A-Za-z_\-]{35}")),
    ("OpenAI/Anthropic key", re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}")),
    ("Private key (PEM)", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("Password/secret assignment", re.compile(
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
    # "top": match from the repository root even when run from a subdirectory.
    # "glob": **/ matches the file at any depth.
    magic = "top,glob,exclude" if exclude else "top,glob"
    return [f":({magic})**/{g}" for g in SENSITIVE_FILE_GLOBS]

def get_git_diff() -> str:
    try:
        result = _run_git(["diff", "--staged", "--", *_pathspecs(exclude=True)])
        return result.stdout.strip()
    
    except subprocess.CalledProcessError:
        return "ERROR: This folder is not a Git repository (run 'git init' first)."
    except FileNotFoundError:
        return "ERROR: The git command was not found on this computer."

def get_excluded_files() -> list:
    """Names of staged files that were left out of the diff because they look sensitive."""
    try:
        result = _run_git(["diff", "--staged", "--name-only", "-z", "--", *_pathspecs(exclude=False)])
        return [name for name in result.stdout.split("\0") if name]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []

def find_secret_patterns(diff_text: str) -> list:
    """Scan the diff for lines that look like secrets; returns (file, description) pairs."""
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
