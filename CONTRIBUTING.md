# Contributing

Thank you for improving OXOXOS Cocos Game Assets MCP.

## Setup

```bash
uv sync --group dev
uv run pytest
uv run ruff check .
```

Do not run manual integration probes unless you understand that they may consume OXOXOS credit.

## Pull requests

- Keep production code in `src/oxoxos_cocos_game_assets_mcp/`.
- Preserve MCP tool names and JSON response shapes unless the change includes a migration plan.
- Add offline tests for API URL construction, model discovery, errors, and local image processing.
- Never hardcode a model marketplace id as a permanent default.
- Never add real tokens, `.env`, generated images, private paths, or client user configuration.
- Keep stdio stdout clean; diagnostics use logging or stderr.
- Update `CHANGELOG.md` for user-visible changes.

## Issues

Use public issues for non-sensitive bugs and feature requests. Use the process in `SECURITY.md` for vulnerabilities or secret exposure.

## Trademarks

This is an independent project. Contributions must not imply Cocos endorsement or include unlicensed anime, game, logo, or other copyrighted assets.
