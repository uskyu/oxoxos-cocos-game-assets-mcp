# ZCode

This repository is a ZCode plugin with bundled `.zcode-plugin/plugin.json` and `.mcp.json`.

1. Add the cloned directory as a local plugin in Settings → Plugins.
2. Enable `oxoxos-cocos-game-assets-mcp`.
3. Open the plugin's Advanced/user configuration and enter the OXOXOS token created at the portal (default https://api.oxoxos.com/console/token; forks override it with `OXOXOS_PORTAL_URL`/`OXOXOS_TOKEN_URL`).
4. Leave image and vision model overrides empty for dynamic discovery.
5. Open Settings → MCP and confirm the bundled `oxoxos-cocos-game-assets` server is running.
6. Start a fresh ZCode session so the new namespaced tools are injected.
7. Call `list_models` before generation.

The token is mapped from plugin user configuration to `OXOXOS_API_KEY`; do not create a committed `.env` file.
