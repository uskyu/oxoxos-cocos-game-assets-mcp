from __future__ import annotations

import json

from oxoxos_cocos_game_assets_mcp import oxoxos_client as client
from oxoxos_cocos_game_assets_mcp import server


def test_list_models_returns_capabilities(monkeypatch) -> None:
    monkeypatch.setattr(
        server,
        "api_list_models",
        lambda force_refresh=False: [
            {
                "id": "market-image",
                "type": "image",
                "capabilities": ["image_generation"],
            }
        ],
    )

    result = json.loads(server.list_models(force_refresh=True))

    assert result["ok"] is True
    assert result["models"][0]["id"] == "market-image"
    assert "image_generation" in result["table"]


def test_safe_prefix_removes_path_separators() -> None:
    assert server._safe_prefix("../hero/icon") == "hero_icon"
    assert server._safe_prefix("***") == "img"


def test_missing_task_is_clear() -> None:
    result = json.loads(server.check_task("not-found"))
    assert result["ok"] is False
    assert "任务不存在" in result["error"]


def test_describe_image_forwards_explicit_model(monkeypatch) -> None:
    captured = {}

    def fake_describe(path, question, model=""):
        captured.update(path=path, question=question, model=model)
        return "ok"

    monkeypatch.setattr(server, "api_describe_image", fake_describe)
    result = json.loads(server.describe_image("a.png", "inspect", model="live-vision"))

    assert result == {"ok": True, "answer": "ok"}
    assert captured["model"] == "live-vision"


def test_token_error_json_includes_setup_without_leaking_token() -> None:
    raw = server._api_error(client.TokenSetupRequired("未检测到 OXOXOS API 令牌"))
    payload = json.loads(raw)

    assert payload["ok"] is False
    assert payload["error"]
    setup = payload["setup"]
    assert setup["code"] == "token_setup_required"
    assert setup["brand"] == "OXOXOS"
    assert setup["portal_url"] == "https://api.oxoxos.com"
    assert setup["token_url"] == "https://api.oxoxos.com/console/token"
    assert isinstance(setup["steps"], list) and len(setup["steps"]) == 4
    assert "令牌管理" in "；".join(setup["steps"])
    assert "Bearer" not in raw
    assert "sk-" not in raw.lower()


def test_token_error_json_uses_configured_brand_and_urls(monkeypatch) -> None:
    monkeypatch.setattr(client, "BRAND_NAME", "ForkBrand")
    monkeypatch.setattr(client, "PORTAL_URL", "https://portal.example.com")
    monkeypatch.setattr(client, "TOKEN_URL", "https://portal.example.com/tokens/new")

    payload = json.loads(server._api_error(client.TokenSetupRequired("缺少令牌")))

    assert payload["setup"]["brand"] == "ForkBrand"
    assert payload["setup"]["portal_url"] == "https://portal.example.com"
    assert payload["setup"]["token_url"] == "https://portal.example.com/tokens/new"
    assert "https://portal.example.com" in payload["setup"]["steps"][0]


def test_generate_image_token_missing_returns_setup(monkeypatch) -> None:
    def raise_missing_token(**kwargs):
        raise client.TokenSetupRequired("未检测到 OXOXOS API 令牌")

    monkeypatch.setattr(server, "api_generate_image", raise_missing_token)
    payload = json.loads(server.generate_image("a coin"))

    assert payload["ok"] is False
    assert payload["setup"]["code"] == "token_setup_required"
    assert payload["setup"]["token_url"] == "https://api.oxoxos.com/console/token"
    assert "sk-" not in json.dumps(payload, ensure_ascii=False).lower()


def test_plain_api_error_has_no_setup_field() -> None:
    payload = json.loads(server._api_error(client.OxoxosApiError("普通错误")))

    assert payload == {"ok": False, "error": "普通错误"}
    assert "setup" not in payload
