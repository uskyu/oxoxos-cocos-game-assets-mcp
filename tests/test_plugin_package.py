from __future__ import annotations

import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_NAME = "oxoxos-cocos-game-assets-mcp"
VERSION = "0.4.1"


def read_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def test_marketplace_discovers_repository_root_plugin() -> None:
    marketplace = read_json("marketplace.json")
    assert marketplace["name"] == "oxoxos-game-dev"
    assert len(marketplace["plugins"]) == 1
    plugin = marketplace["plugins"][0]
    assert plugin["name"] == PLUGIN_NAME
    assert plugin["source"] == "."
    assert plugin["version"] == VERSION


def test_manifest_exposes_installation_skill() -> None:
    manifest = read_json(".zcode-plugin/plugin.json")
    assert manifest["name"] == PLUGIN_NAME
    assert manifest["version"] == VERSION
    assert manifest["skills"] == ".agents/skills"
    assert "api_key" not in manifest["userConfig"]
    assert (ROOT / manifest["skills"] / "install-oxoxos-cocos-game-assets-mcp" / "SKILL.md").is_file()


def test_plugin_mcp_bootstraps_locked_uv_environment_in_plugin_data() -> None:
    config = read_json(".mcp.json")
    server = config["mcpServers"]["oxoxos-cocos-game-assets"]
    assert server["command"] == "uv"
    assert server["args"] == [
        "--directory",
        "${ZCODE_PLUGIN_ROOT}",
        "run",
        "--locked",
        "--no-dev",
        "python",
        "mcp/server.py",
    ]
    assert server["env"]["UV_PROJECT_ENVIRONMENT"] == "${ZCODE_PLUGIN_DATA}/venv"
    assert server["env"]["UV_CACHE_DIR"] == "${ZCODE_PLUGIN_DATA}/uv-cache"
    assert server["env"]["UV_HTTP_TIMEOUT"] == "120"
    assert "OXOXOS_API_KEY" not in server["env"]
    assert server["timeoutMs"] >= 120000


def test_package_versions_stay_aligned() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    manifest = read_json(".zcode-plugin/plugin.json")
    marketplace = read_json("marketplace.json")
    assert pyproject["project"]["version"] == VERSION
    assert manifest["version"] == VERSION
    assert marketplace["plugins"][0]["version"] == VERSION
