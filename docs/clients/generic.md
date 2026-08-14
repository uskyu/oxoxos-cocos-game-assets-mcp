# Generic MCP client

Configure a local stdio server:

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

This is a structural example. Confirm whether your client supports `${...}` interpolation; if not, use its secret UI or launch environment rather than writing a real token into a shared file.

Restart the client, initialize the MCP server, enumerate tools, and call `list_models`. Use absolute paths and keep stdout reserved for the protocol.
