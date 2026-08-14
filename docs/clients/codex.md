# OpenAI Codex

Official documentation: https://developers.openai.com/codex/mcp/

Confirm current syntax with `codex mcp --help`. Typical stdio registration:

```bash
codex mcp add oxoxos-cocos-game-assets -- /ABSOLUTE/PATH/.venv/bin/python /ABSOLUTE/PATH/mcp/server.py
```

Prefer the CLI instead of hand-editing `~/.codex/config.toml`. Client releases and project trust rules can change. Supply `OXOXOS_API_KEY` through a supported environment or secret mechanism; do not store it in a shared project file.

Verify:

```bash
codex mcp list
codex mcp get oxoxos-cocos-game-assets
```

Codex reads repository `AGENTS.md`; it still must ask before persistent installation and secret configuration.
