# Repository agent instructions

Read `README.md`, `pyproject.toml`, and the relevant files under `docs/` before changing installation or runtime behavior.

## Safety

- Never read, print, log, commit, or include an API token in a command argument.
- Treat `.env` and client configuration as sensitive. Check only whether a secret is configured.
- Ask before network calls that can consume image or vision credit.
- Ask before installing global dependencies or modifying user-level client configuration.
- Back up existing client configuration before changing it and preserve unrelated entries.
- Keep MCP stdio stdout exclusively for JSON-RPC. Use logging/stderr for diagnostics.

## Development

```bash
uv sync --group dev
uv run pytest
uv run ruff check .
```

Core code belongs in `src/oxoxos_cocos_game_assets_mcp/`. Files under `mcp/` preserve repository-based launch compatibility. Do not add new production logic only to a compatibility wrapper.

The OXOXOS model marketplace changes. Do not hardcode a permanent image or vision model id in source, manifests, tests, or documentation. Discover models at runtime and allow explicit user overrides.

Do not rename existing MCP tool names or change their JSON success/error shapes without a documented compatibility plan.

For installation work, read `.agents/skills/install-oxoxos-cocos-game-assets-mcp/SKILL.md` and the selected client reference.
