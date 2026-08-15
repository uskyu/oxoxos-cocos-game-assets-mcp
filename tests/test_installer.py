from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / ".agents"
    / "skills"
    / "install-oxoxos-cocos-game-assets-mcp"
    / "scripts"
    / "install.py"
)
SPEC = importlib.util.spec_from_file_location("oxoxos_installer", SCRIPT)
assert SPEC and SPEC.loader
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)


def test_deferred_token_does_not_block_client_install(monkeypatch, tmp_path) -> None:
    credential = tmp_path / "credentials.env"
    monkeypatch.setattr(installer, "credential_file", lambda: credential)
    monkeypatch.setattr(installer, "install_dependencies", lambda: {"method": "test", "ok": True})
    monkeypatch.setattr(installer, "detect_clients", lambda requested: [("zcode", None)])
    monkeypatch.setattr(
        installer,
        "configure_zcode",
        lambda: {"client": "zcode", "configured": True, "config": "test-config"},
    )

    report = installer.apply(["auto"], False, False, True)

    assert report["ok"] is True
    assert report["token_configured"] is False
    assert report["token_setup_required"] is True
    assert report["credential_file"] == str(credential)
    assert not credential.exists()
    assert "initialize OXOXOS API configuration" in report["next"]


def test_apply_requires_an_explicit_token_mode(monkeypatch) -> None:
    monkeypatch.setattr(installer, "install_dependencies", lambda: {"ok": True})

    try:
        installer.apply(["auto"], False, False, False)
    except installer.InstallError as exc:
        assert "--defer-token" in str(exc)
    else:
        raise AssertionError("installer should require an explicit token mode")


def test_token_only_stores_credential_without_installing_clients(monkeypatch, tmp_path) -> None:
    credential = tmp_path / "credentials.env"
    calls = []
    monkeypatch.setattr(installer, "credential_file", lambda: credential)
    monkeypatch.setattr(installer, "read_token_from_stdin", lambda: "test-token-value")
    monkeypatch.setattr(installer, "install_dependencies", lambda: calls.append("dependencies"))
    monkeypatch.setattr(installer, "detect_clients", lambda requested: calls.append("clients"))

    report = installer.configure_token_only()

    assert report["ok"] is True
    assert report["mode"] == "token-only"
    assert report["credential_file"] == str(credential)
    assert credential.exists()
    assert calls == []
    assert "list_models" in report["next"]
