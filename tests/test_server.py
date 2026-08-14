from __future__ import annotations

import json

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
