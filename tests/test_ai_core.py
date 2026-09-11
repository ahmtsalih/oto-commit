import io
import json
import urllib.request

import pytest

from oto_commit import ai_core


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


@pytest.fixture
def captured(monkeypatch):
    seen = {}

    def fake_urlopen(req, *args, **kwargs):
        seen["request"] = req
        seen["kwargs"] = kwargs
        body = {"candidates": [{"content": {"parts": [{"text": "feat: test"}]}}]}
        return FakeResponse(json.dumps(body).encode("utf-8"))

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(ai_core, "load_api_key", lambda: "GIZLI-ANAHTAR")
    return seen


def test_api_key_is_sent_in_header_not_in_url(captured):
    ai_core.generate_commit_message("diff")
    req = captured["request"]
    assert "GIZLI-ANAHTAR" not in req.full_url
    assert req.get_header("X-goog-api-key") == "GIZLI-ANAHTAR"


def test_request_has_timeout(captured):
    ai_core.generate_commit_message("diff")
    assert captured["kwargs"].get("timeout", 0) > 0


def test_returns_model_text(captured):
    assert ai_core.generate_commit_message("diff") == "feat: test"


def test_http_error_with_invalid_utf8_body_is_reported_not_raised(monkeypatch):
    import urllib.error

    def failing_urlopen(req, *args, **kwargs):
        raise urllib.error.HTTPError(req.full_url, 400, "Bad Request", {}, io.BytesIO(b"\xff\xfe bad"))

    monkeypatch.setattr(urllib.request, "urlopen", failing_urlopen)
    monkeypatch.setattr(ai_core, "load_api_key", lambda: "GIZLI-ANAHTAR")
    result = ai_core.generate_commit_message("diff")
    assert result.startswith("ERROR: API request rejected (400)")
    assert "GIZLI-ANAHTAR" not in result
