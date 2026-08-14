# Claude Code

Official reference: https://code.claude.com/docs/en/mcp

Use the current official CLI syntax rather than editing undocumented internal state. A typical local stdio registration is:

```bash
claude mcp add --scope local oxoxos-cocos-game-assets -- /ABSOLUTE/PATH/.venv/bin/python /ABSOLUTE/PATH/mcp/server.py
```

On Windows, use the absolute `.venv\Scripts\python.exe` path. Confirm the exact command with `claude mcp add --help` because client releases can change flags.

Scopes documented by Claude Code include `local`, `project`, and `user`. Prefer local or project scope unless the user explicitly wants the MCP in every project. Project `.mcp.json` is shareable and must reference environment variables rather than containing a real token.

Verify with:

```bash
claude mcp list
claude mcp get oxoxos-cocos-game-assets
```

Claude Code project instructions may use `CLAUDE.md`; this repository keeps the canonical cross-agent rules in `AGENTS.md` and links them from `CLAUDE.md` to avoid drift.
