# Generic MCP Client

Configure a local stdio server with:

- name: `oxoxos-cocos-game-assets`
- command: absolute path to this repository's virtual-environment Python
- args: absolute path to `mcp/server.py`
- environment: `OXOXOS_API_KEY` supplied by the client's secret or environment mechanism

Example shape only—adapt it to the client's documented format:

```json
{
  "mcpServers": {
    "oxoxos-cocos-game-assets": {
      "command": "/absolute/path/.venv/bin/python",
      "args": ["/absolute/path/mcp/server.py"],
      "env": {
        "OXOXOS_API_KEY": "${OXOXOS_API_KEY}"
      }
    }
  }
}
```

Do not assume `${OXOXOS_API_KEY}` interpolation is supported until the client's documentation confirms it. If it is unsupported, use the client's secret UI or launch environment instead of putting a real token in a shared config.
