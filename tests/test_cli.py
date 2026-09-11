import pytest
from typer.testing import CliRunner

from oto_commit import cli

runner = CliRunner()


def _diff(line, filename="src/settings.py"):
    return (
        f"diff --git a/{filename} b/{filename}\n"
        f"--- a/{filename}\n+++ b/{filename}\n@@ -1 +1 @@\n+{line}\n"
    )


@pytest.fixture
def plain_diff(monkeypatch):
    monkeypatch.setattr(cli, "get_git_diff", lambda: _diff("x = 1"))
    monkeypatch.setattr(cli, "get_excluded_files", lambda: [])


def test_setup_does_not_echo_the_key(monkeypatch):
    saved = []
    monkeypatch.setattr(cli, "save_api_key", saved.append)
    result = runner.invoke(cli.app, ["setup"], input="COK-GIZLI-ANAHTAR\n")
    assert result.exit_code == 0
    assert saved == ["COK-GIZLI-ANAHTAR"]
    assert "COK-GIZLI-ANAHTAR" not in result.output


def test_model_output_is_printed_literally_not_as_markup(plain_diff, monkeypatch):
    monkeypatch.setattr(cli, "generate_commit_message", lambda diff: "[link=https://kotu.example]feat: a[/link]")
    result = runner.invoke(cli.app, ["generate"])
    assert result.exit_code == 0
    assert "[link=https://kotu.example]feat: a[/link]" in result.output


def test_model_output_control_characters_are_stripped(plain_diff, monkeypatch):
    evil = "\x1b]8;;https://kotu.example\x1b\\feat: a\x1b]8;;\x1b\\ \x1b[31mb\x1b[0m\x07"
    monkeypatch.setattr(cli, "generate_commit_message", lambda diff: evil)
    result = runner.invoke(cli.app, ["generate"])
    assert "\x1b" not in result.output
    assert "\x07" not in result.output
    assert "feat: a b" in result.output


def test_api_error_with_brackets_does_not_crash(plain_diff, monkeypatch):
    monkeypatch.setattr(cli, "generate_commit_message", lambda diff: 'ERROR: API request rejected (400). {"error": "[/x]"}')
    result = runner.invoke(cli.app, ["generate"])
    assert result.exit_code == 0
    assert '{"error": "[/x]"}' in result.output


def test_excluded_sensitive_files_are_listed(monkeypatch):
    monkeypatch.setattr(cli, "get_git_diff", lambda: _diff("x = 1"))
    monkeypatch.setattr(cli, "get_excluded_files", lambda: ["config/.env"])
    monkeypatch.setattr(cli, "generate_commit_message", lambda diff: "feat: a")
    result = runner.invoke(cli.app, ["generate"])
    assert "config/.env" in result.output
    assert "were not sent" in result.output


def test_secret_in_diff_declining_confirmation_aborts(monkeypatch):
    monkeypatch.setattr(cli, "get_git_diff", lambda: _diff('KEY = "AIzaSyA1234567890abcdefghijklmnopqrstuvw"'))
    monkeypatch.setattr(cli, "get_excluded_files", lambda: [])
    sent = []
    monkeypatch.setattr(cli, "generate_commit_message", lambda diff: sent.append(diff) or "feat: a")
    result = runner.invoke(cli.app, ["generate"], input="n\n")
    assert sent == []
    assert "Google API key" in result.output
    assert "AIzaSy" not in result.output


def test_secret_in_diff_is_sent_after_confirmation(monkeypatch):
    diff = _diff('KEY = "AIzaSyA1234567890abcdefghijklmnopqrstuvw"')
    monkeypatch.setattr(cli, "get_git_diff", lambda: diff)
    monkeypatch.setattr(cli, "get_excluded_files", lambda: [])
    sent = []
    monkeypatch.setattr(cli, "generate_commit_message", lambda d: sent.append(d) or "feat: a")
    result = runner.invoke(cli.app, ["generate"], input="y\n")
    assert sent == [diff]
    assert "feat: a" in result.output
