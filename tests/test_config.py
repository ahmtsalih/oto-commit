import json
import os
import stat

import pytest

from oto_commit import config


@pytest.fixture
def config_file(tmp_path, monkeypatch):
    path = tmp_path / "cfg.json"
    monkeypatch.setattr(config, "CONFIG_FILE", path)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    return path


@pytest.mark.skipif(os.name == "nt", reason="POSIX file permissions")
def test_save_api_key_creates_file_readable_only_by_owner(config_file):
    config.save_api_key("KEY")
    assert stat.S_IMODE(config_file.stat().st_mode) == 0o600


@pytest.mark.skipif(os.name == "nt", reason="POSIX file permissions")
def test_save_api_key_fixes_permissions_of_existing_file(config_file):
    config_file.write_text("{}")
    config_file.chmod(0o644)
    config.save_api_key("KEY")
    assert stat.S_IMODE(config_file.stat().st_mode) == 0o600


def test_save_api_key_sets_owner_only_mode(config_file, monkeypatch):
    # Windows does not expose POSIX modes, so the chmod call itself is observed.
    modes = []
    real_chmod = os.chmod

    def spy(path, mode, *args, **kwargs):
        modes.append((str(path), mode))
        real_chmod(path, mode, *args, **kwargs)

    monkeypatch.setattr(os, "chmod", spy)
    config.save_api_key("KEY")
    assert (str(config_file), 0o600) in modes


def test_save_then_load_roundtrip(config_file):
    config.save_api_key("KEY-123")
    assert config.load_api_key() == "KEY-123"


def test_load_api_key_prefers_environment_variable(config_file, monkeypatch):
    config_file.write_text(json.dumps({"api_key": "FILE-KEY"}))
    monkeypatch.setenv("GEMINI_API_KEY", "ENV-KEY")
    assert config.load_api_key() == "ENV-KEY"


def test_load_api_key_returns_none_when_file_missing(config_file):
    assert config.load_api_key() is None


def test_load_api_key_returns_none_for_broken_json(config_file):
    config_file.write_text("{bozuk")
    assert config.load_api_key() is None
