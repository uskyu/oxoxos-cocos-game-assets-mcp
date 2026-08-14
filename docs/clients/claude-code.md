# Claude Code

Official documentation: https://code.claude.com/docs/en/mcp

Confirm current syntax with `claude mcp add --help`. Typical local stdio registration:

```bash
claude mcp add --scope local oxoxos-cocos-game-assets -- /ABSOLUTE/PATH/.venv/bin/python /ABSOLUTE/PATH/mcp/server.py
```

Windows uses `.venv\Scripts\python.exe`. Choose `local`, `project`, or `user` scope deliberately. Do not commit a real token to project `.mcp.json`; use environment-variable references supported by the current Claude Code version.

Verify:

```bash
claude mcp list
claude mcp get oxoxos-cocos-game-assets
```

Then initialize the server and call `list_models` from Claude Code. Remove with the current `claude mcp remove` command after confirming its scope.
