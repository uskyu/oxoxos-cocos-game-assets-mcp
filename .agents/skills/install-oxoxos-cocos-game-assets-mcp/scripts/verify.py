"""Verify MCP initialization and optionally query live OXOXOS models."""
from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path

from mcp.client.stdio import stdio_client

from mcp import ClientSession, StdioServerParameters

ROOT = Path(__file__).resolve().parents[4]
VENV_PYTHON = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
SERVER = ROOT / "mcp" / "server.py"


async def verify(live_models: bool) -> dict:
    params = StdioServerParameters(
        command=str(VENV_PYTHON),
        args=[str(SERVER)],
        read_timeout_seconds=45,
    )
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        tools_result = await session.list_tools()
        resources_result = await session.list_resources()
        report = {
            "ok": True,
            "tools": [tool.name for tool in tools_result.tools],
            "resources": [str(resource.uri) for resource in resources_result.resources],
            "live_models_checked": False,
        }
        if live_models:
            result = await session.call_tool("list_models", {"force_refresh": True})
            payload = json.loads(result.content[0].text)
            if not payload.get("ok"):
                return {"ok": False, "stage": "list_models", "error": payload.get("error")}
            models = payload.get("models", [])
            report.update(
                live_models_checked=True,
                model_count=len(models),
                image_candidates=[
                    model["id"]
                    for model in models
                    if "image_generation" in model.get("capabilities", [])
                ],
                vision_candidates=[
                    model["id"]
                    for model in models
                    if "vision" in model.get("capabilities", [])
                    or "vision_candidate" in model.get("capabilities", [])
                ],
            )
        return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live-models", action="store_true")
    args = parser.parse_args()
    try:
        result = asyncio.run(verify(args.live_models))
    except (OSError, RuntimeError, ValueError, TimeoutError, ExceptionGroup) as exc:
        result = {"ok": False, "stage": "initialize", "error": str(exc)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result.get("ok") else 1)


if __name__ == "__main__":
    main()
