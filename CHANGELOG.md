# Changelog

All notable changes follow a simplified Keep a Changelog format.

## [Unreleased]

### Added

- Repository-root `marketplace.json` for direct ZCode Marketplace discovery and installation.
- ZCode plugin MCP startup through `uv`, so a fresh cache install does not depend on a prebuilt `.venv`.
- Explicit plugin discovery of the cross-agent installation Skill under `.agents/skills`.
- Cross-agent installation Skill for Claude Code, Codex, ZCode, and generic MCP clients.
- Dynamic OXOXOS model discovery and optional model overrides.
- Standard Python `src/` package layout, CLI entry point, offline tests, and open-source governance files.

### Changed

- Renamed the project to `oxoxos-cocos-game-assets-mcp`.
- Migrated the default API base URL to `https://api.oxoxos.com/v1`.
- Renamed primary environment variables from `QWAPI_*` to `OXOXOS_*`.

### Deprecated

- `QWAPI_API_KEY`, `QWAPI_IMAGE_MODEL`, `QWAPI_VISION_MODEL`, and `QWAPI_PROXY` compatibility aliases.
- The `mcp/qweapi_client.py` import wrapper.

### Security

- Missing-token errors direct users to the token console without revealing secret values.
- Installation guidance prohibits tokens in prompts, command arguments, source, and Git.
