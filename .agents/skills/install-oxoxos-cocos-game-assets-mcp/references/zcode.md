# ZCode

ZCode plugins can bundle `.mcp.json` and `.zcode-plugin/plugin.json`. Install the repository as a local plugin through ZCode's plugin settings, then configure `api_key` in the plugin's Advanced/user configuration panel.

The bundled server declaration uses `${ZCODE_PLUGIN_ROOT}` and maps user configuration to `OXOXOS_API_KEY`. This is preferable to committing a `.env` file.

After enabling the plugin:

1. open Settings → Plugins and confirm `oxoxos-cocos-game-assets-mcp` is enabled;
2. open Settings → MCP and confirm the bundled `oxoxos-cocos-game-assets` server starts;
3. invoke `list_models` before selecting a model;
4. do not expect an existing session to discover newly installed tools—start a fresh ZCode session if needed.

ZCode project skills are discovered from `.zcode/skills` and `.agents/skills`, with `.zcode/skills` taking precedence. This repository uses `.agents/skills` as the cross-tool location.
