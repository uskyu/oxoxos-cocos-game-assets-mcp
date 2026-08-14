"""Manual OXOXOS integration probe.

This script can consume API credit. It is excluded from normal tests and must be
run only after reviewing the current marketplace models and explicitly opting in.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path

import httpx
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT / "assets"


def credential_values() -> dict[str, str | None]:
    if os.name == "nt":
        base = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))
    values = dotenv_values(base / "OXOXOS" / "oxoxos-cocos-game-assets-mcp.env")
    values.update(dotenv_values(ROOT / ".env"))
    return values


def configured(key: str, default: str = "") -> str:
    return os.getenv(key, "").strip() or str(credential_values().get(key, "") or "").strip() or default


def client() -> httpx.Client:
    token = configured("OXOXOS_API_KEY")
    if not token:
        raise RuntimeError("OXOXOS_API_KEY is not configured")
    return httpx.Client(
        base_url=configured("OXOXOS_BASE_URL", "https://api.oxoxos.com/v1").rstrip("/") + "/",
        headers={"Authorization": f"Bearer {token}"},
        proxy=configured("OXOXOS_PROXY") or None,
        timeout=180.0,
    )


def probe_models() -> list[dict]:
    with client() as connection:
        response = connection.get("models")
    response.raise_for_status()
    models = response.json().get("data", [])
    print(json.dumps({"model_count": len(models), "models": models}, ensure_ascii=False, indent=2))
    return models


def probe_generate(model: str) -> dict:
    payload = {
        "model": model,
        "prompt": "a tiny red gem icon, flat pixel art style, centered on a plain background",
        "size": "1024x1024",
        "quality": "low",
        "n": 1,
    }
    with client() as connection:
        response = connection.post("images/generations", json=payload)
    response.raise_for_status()
    return response.json()


def save_result(data: dict) -> None:
    ASSETS_DIR.mkdir(exist_ok=True)
    item = data.get("data", [{}])[0]
    encoded = item.get("b64_json")
    if encoded:
        path = ASSETS_DIR / "probe_b64.png"
        path.write_bytes(base64.b64decode(encoded))
        print(json.dumps({"saved": str(path.resolve())}, ensure_ascii=False))
        return
    url = item.get("url")
    if url:
        with client() as connection:
            image = connection.get(url)
        image.raise_for_status()
        path = ASSETS_DIR / "probe_url.png"
        path.write_bytes(image.content)
        print(json.dumps({"saved": str(path.resolve())}, ensure_ascii=False))
        return
    raise RuntimeError("Generation response contains neither b64_json nor url")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generate-model", help="explicit live model id; this opts into a paid request")
    args = parser.parse_args()
    probe_models()
    if args.generate_model:
        save_result(probe_generate(args.generate_model))


if __name__ == "__main__":
    main()
