from __future__ import annotations

import base64
import json
from contextlib import contextmanager

import httpx
import pytest

from oxoxos_cocos_game_assets_mcp import oxoxos_client as client


@contextmanager
def mock_client(handler):
    transport = httpx.MockTransport(handler)
    with httpx.Client(
        base_url="https://api.oxoxos.com/v1/",
        headers={"Authorization": "Bearer test-token"},
        transport=transport,
    ) as http:
        yield http


def test_relative_paths_preserve_v1_prefix() -> None:
    with httpx.Client(base_url="https://api.oxoxos.com/v1") as http:
        request = http.build_request("GET", "models")
    assert str(request.url) == "https://api.oxoxos.com/v1/models"


def test_list_models_keeps_live_marketplace_and_infers_hints(monkeypatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/models"
        return httpx.Response(
            200,
            json={
                "data": [
                    {"id": "current-image-model", "type": "image"},
                    {"id": "current-vision-model", "type": "multimodal-vision"},
                    {"id": "current-chat-model", "type": "chat"},
                ]
            },
        )

    monkeypatch.setattr(client, "_make_client", lambda: mock_client(handler))
    monkeypatch.setattr(client, "_MODEL_CACHE", None)

    models = client.list_models(force_refresh=True)

    assert [model["id"] for model in models] == [
        "current-image-model",
        "current-vision-model",
        "current-chat-model",
    ]
    assert "image_generation" in models[0]["capabilities"]
    assert "vision" in models[1]["capabilities"]
    assert "chat" in models[2]["capabilities"]
    assert "vision_candidate" in client._infer_capabilities({"id": "gpt-5.6-sol", "type": "model"})


def test_model_selection_prefers_explicit_then_config_then_discovery(monkeypatch) -> None:
    monkeypatch.setattr(client, "IMAGE_MODEL", "configured-image")
    assert client._select_model("image_generation", "explicit-image") == "explicit-image"
    assert client._select_model("image_generation") == "configured-image"

    monkeypatch.setattr(client, "IMAGE_MODEL", "")
    monkeypatch.setattr(
        client,
        "list_models",
        lambda: [
            {"id": "chat-only", "capabilities": ["chat"]},
            {"id": "live-image", "capabilities": ["image_generation"]},
        ],
    )
    assert client._select_model("image_generation") == "live-image"


def test_model_selection_has_actionable_error(monkeypatch) -> None:
    monkeypatch.setattr(client, "VISION_MODEL", "")
    monkeypatch.setattr(client, "list_models", list)

    with pytest.raises(client.OxoxosApiError, match="list_models"):
        client._select_model("vision")


def test_generate_image_uses_dynamic_model_and_decodes_base64(monkeypatch) -> None:
    image_bytes = b"fake-png-bytes"

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/images/generations"
        payload = __import__("json").loads(request.content)
        assert payload["model"] == "live-image"
        return httpx.Response(
            200,
            json={"data": [{"b64_json": base64.b64encode(image_bytes).decode()}]},
        )

    monkeypatch.setattr(client, "_make_client", lambda: mock_client(handler))
    monkeypatch.setattr(client, "_select_model", lambda kind, explicit="": "live-image")

    result = client.generate_image("a Cocos game coin", quality="low")

    assert result.images == [image_bytes]
    assert result.notes == ["使用模型: live-image"]


def test_missing_token_error_is_safe_and_actionable(monkeypatch) -> None:
    monkeypatch.setattr(client, "API_KEY", "")

    with pytest.raises(client.TokenSetupRequired) as exc_info:
        client._make_client()

    message = str(exc_info.value)
    assert isinstance(exc_info.value, client.OxoxosApiError)
    assert "OXOXOS" in message
    assert "https://api.oxoxos.com" in message
    assert "令牌管理" in message
    assert "Bearer" not in message
    assert "sk-" not in message.lower()


def test_token_setup_guide_default_steps(monkeypatch) -> None:
    monkeypatch.setattr(client, "BRAND_NAME", "OXOXOS")
    monkeypatch.setattr(client, "PORTAL_URL", "https://api.oxoxos.com")
    monkeypatch.setattr(client, "TOKEN_URL", "https://api.oxoxos.com/console/token")

    guide = client.token_setup_guide()

    assert guide["code"] == "token_setup_required"
    assert guide["brand"] == "OXOXOS"
    assert guide["portal_url"] == "https://api.oxoxos.com"
    assert guide["token_url"] == "https://api.oxoxos.com/console/token"
    assert len(guide["steps"]) == 4
    assert guide["steps"][0] == "前往 https://api.oxoxos.com 注册或登录"
    assert "令牌管理" in guide["steps"][1]
    assert "创建" in guide["steps"][2]
    assert "AI 会自动保存、配置并验证" in guide["steps"][3]
    assert "install.py" in guide["ai_instruction"]
    assert guide["customization"] == {
        "brand_env": "OXOXOS_BRAND_NAME",
        "portal_env": "OXOXOS_PORTAL_URL",
        "token_env": "OXOXOS_TOKEN_URL",
    }


def test_token_setup_guide_uses_configured_brand_and_urls(monkeypatch) -> None:
    monkeypatch.setattr(client, "BRAND_NAME", "MyFork")
    monkeypatch.setattr(client, "PORTAL_URL", "https://portal.example.com")
    monkeypatch.setattr(client, "TOKEN_URL", "https://portal.example.com/console/token")

    guide = client.token_setup_guide()

    assert guide["brand"] == "MyFork"
    assert guide["portal_url"] == "https://portal.example.com"
    assert guide["token_url"] == "https://portal.example.com/console/token"
    assert guide["steps"][0] == "前往 https://portal.example.com 注册或登录"


def test_token_setup_guide_never_exposes_a_token_value(monkeypatch) -> None:
    monkeypatch.setattr(client, "BRAND_NAME", "OXOXOS")
    monkeypatch.setattr(client, "PORTAL_URL", "https://api.oxoxos.com")
    monkeypatch.setattr(client, "TOKEN_URL", "https://api.oxoxos.com/console/token")

    serialized = json.dumps(client.token_setup_guide(), ensure_ascii=False)

    assert "Bearer" not in serialized
    assert "sk-" not in serialized.lower()
    assert "secret" not in serialized.lower()
    # Only environment-variable *names* may mention the token word.
    assert "OXOXOS_API_KEY" not in serialized


def test_missing_token_error_message_builds_from_guide(monkeypatch) -> None:
    monkeypatch.setattr(client, "API_KEY", "")
    monkeypatch.setattr(client, "BRAND_NAME", "ForkBrand")
    monkeypatch.setattr(client, "PORTAL_URL", "https://portal.example.com")

    with pytest.raises(client.TokenSetupRequired) as exc_info:
        client._make_client()

    message = str(exc_info.value)
    assert message.startswith("未检测到 ForkBrand API 令牌")
    assert "https://portal.example.com" in message
    assert "不需要手工编辑配置" in message
    assert "Git" in message


def test_legacy_token_alias_has_lower_priority(monkeypatch) -> None:
    monkeypatch.setenv("OXOXOS_API_KEY", "new-token")
    monkeypatch.setenv("QWAPI_API_KEY", "legacy-token")
    assert client._configured("OXOXOS_API_KEY", "QWAPI_API_KEY") == "new-token"
