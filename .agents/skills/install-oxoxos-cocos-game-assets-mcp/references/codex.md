# OpenAI Codex

Official reference: https://developers.openai.com/codex/mcp/

Use `codex mcp --help` and the current official page to confirm flags before changing configuration. A typical stdio registration is:

```bash
codex mcp add oxoxos-cocos-game-assets -- /ABSOLUTE/PATH/.venv/bin/python /ABSOLUTE/PATH/mcp/server.py
```

On Windows, use `.venv\Scripts\python.exe`. Codex normally stores MCP settings in `~/.codex/config.toml`; project configuration behavior depends on the installed version and project trust settings. Prefer the CLI over hand-editing TOML.

Verify with:

```bash
codex mcp list
codex mcp get oxoxos-cocos-game-assets
```

Codex supports repository `AGENTS.md`. Follow it, but still ask before installing dependencies, changing user config, or storing a token. Do not assume Claude-specific `CLAUDE.md` is a Codex instruction source.
