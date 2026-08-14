"""Read-only installation readiness check. Never prints secret values."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


def credential_file() -> Path:
    override = os.getenv("OXOXOS_CREDENTIAL_FILE", "").strip()
    if override:
        return Path(override).expanduser()
    if os.name == "nt":
        base = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "OXOXOS" / "oxoxos-cocos-game-assets-mcp.env"


def detect() -> dict:
    venv_python = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    return {
        "ok": True,
        "repository": str(ROOT),
        "platform": sys.platform,
        "python": sys.executable,
        "python_version": ".".join(map(str, sys.version_info[:3])),
        "uv": shutil.which("uv"),
        "venv_python": str(venv_python),
        "venv_ready": venv_python.exists(),
        "clients": {
            "claude": shutil.which("claude"),
            "codex": shutil.which("codex"),
            "zcode": shutil.which("zcode"),
        },
        "credential_file": str(credential_file()),
        "token_configured": bool(
            os.getenv("OXOXOS_API_KEY", "").strip()
            or os.getenv("QWAPI_API_KEY", "").strip()
            or credential_file().exists()
        ),
        "required_files": {
            name: (ROOT / name).exists()
            for name in ("README.md", "pyproject.toml", ".mcp.json", "mcp/server.py")
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()
    result = detect()
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    print("OXOXOS Cocos Game Assets MCP doctor")
    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
