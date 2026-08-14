"""Compatibility import wrapper. Use oxoxos_cocos_game_assets_mcp.oxoxos_client."""
from __future__ import annotations

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from oxoxos_cocos_game_assets_mcp.oxoxos_client import *
