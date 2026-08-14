from __future__ import annotations

import base64
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

    with pytest.raises(client.OxoxosApiError) as exc_info:
        client._make_client()

    message = str(exc_info.value)
    assert "OXOXOS_API_KEY" in message
    assert "https://api.oxoxos.com/console/token" in message
    assert "Bearer" not in message


def test_legacy_token_alias_has_lower_priority(monkeypatch) -> None:
    monkeypatch.setenv("OXOXOS_API_KEY", "new-token")
    monkeypatch.setenv("QWAPI_API_KEY", "legacy-token")
    assert client._configured("OXOXOS_API_KEY", "QWAPI_API_KEY") == "new-token"
