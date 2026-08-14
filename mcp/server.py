"""Compatibility launcher for repository-based MCP client configurations."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from oxoxos_cocos_game_assets_mcp.server import main

if __name__ == "__main__":
    main()
