import subprocess

import pytest

from oto_commit import git_core


@pytest.fixture
def stage(tmp_path, monkeypatch):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    monkeypatch.chdir(tmp_path)

    def _stage(relpath, content):
        path = tmp_path / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        subprocess.run(["git", "add", "-f", relpath], cwd=tmp_path, check=True)

    return _stage


def test_diff_includes_normal_files(stage):
    stage("app.py", "print('merhaba')\n")
    assert "merhaba" in git_core.get_git_diff()


@pytest.mark.parametrize(
    "path",
    [".env", "config/.env.production", "certs/server.pem", "keys/deploy.key", ".ssh/id_rsa"],
)
def test_diff_excludes_sensitive_files(stage, path):
    stage("app.py", "print('merhaba')\n")
    stage(path, "SUPER_SECRET_VALUE\n")
    diff = git_core.get_git_diff()
    assert "merhaba" in diff
    assert "SUPER_SECRET_VALUE" not in diff


def test_diff_from_subdirectory_still_covers_whole_repo(stage, tmp_path, monkeypatch):
    stage("app.py", "print('merhaba')\n")
    stage("sub/.env", "SUPER_SECRET_VALUE\n")
    monkeypatch.chdir(tmp_path / "sub")
    diff = git_core.get_git_diff()
    assert "merhaba" in diff
    assert "SUPER_SECRET_VALUE" not in diff


def test_excluded_files_are_reported_by_name(stage):
    stage("app.py", "x = 1\n")
    stage("config/.env", "A=1\n")
    assert git_core.get_excluded_files() == ["config/.env"]


def test_no_excluded_files_for_normal_changes(stage):
    stage("app.py", "x = 1\n")
    assert git_core.get_excluded_files() == []


def _diff(line, filename="src/settings.py"):
    return (
        f"diff --git a/{filename} b/{filename}\n"
        f"--- a/{filename}\n+++ b/{filename}\n@@ -1 +1 @@\n+{line}\n"
    )


@pytest.mark.parametrize(
    "line,expected",
    [
        ('GOOGLE_KEY = "AIzaSyA1234567890abcdefghijklmnopqrstuvw"', "Google API key"),
        ('OPENAI = "sk-abcdefghijklmnopqrstuvwxyz123456"', "OpenAI/Anthropic key"),
        ("-----BEGIN RSA PRIVATE KEY-----", "Private key (PEM)"),
        ('password = "cokgizlisifre123"', "Password/secret assignment"),
        ("aws_key = AKIAIOSFODNN7EXAMPLE", "AWS access key"),
        ('gh = "ghp_abcdefghijklmnopqrstuvwxyz0123456789"', "GitHub token"),
    ],
)
def test_secret_patterns_are_detected(line, expected):
    assert git_core.find_secret_patterns(_diff(line)) == [("src/settings.py", expected)]


def test_findings_do_not_contain_the_secret_itself():
    findings = git_core.find_secret_patterns(_diff('password = "cokgizlisifre123"'))
    assert "cokgizlisifre123" not in repr(findings)


def test_same_finding_is_reported_once_per_file():
    diff = _diff('a = "AIzaSyA1234567890abcdefghijklmnopqrstuvw"\n+b = "AIzaSyB1234567890abcdefghijklmnopqrstuvw"')
    assert len(git_core.find_secret_patterns(diff)) == 1


def test_normal_code_has_no_findings():
    diff = _diff("def hesapla(x):\n+    return x * 2  # token count, no password field")
    assert git_core.find_secret_patterns(diff) == []
