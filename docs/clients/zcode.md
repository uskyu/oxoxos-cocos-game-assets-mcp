# ZCode

This repository is a ZCode plugin with bundled `.zcode-plugin/plugin.json` and `.mcp.json`.

1. Open Settings → Plugin Management → Discover and click `+`.
2. Add the Marketplace by GitHub URL: `https://github.com/uskyu/oxoxos-cocos-game-assets-mcp`. If Git cloning needs a proxy, start ZCode with `ZCODE_HTTP_PROXY=http://127.0.0.1:7890` (replace the address for your proxy). A local directory is supported only when it is a clean clone containing `marketplace.json`; do not select a development working tree that contains `.env`, `.venv`, generated assets, or build output because directory sources copy ignored files too.
3. Find `oxoxos-cocos-game-assets-mcp` in the new `oxoxos-game-dev` marketplace and click **Get**; it is enabled by default.
4. Open the plugin's Advanced/user configuration. Enter the OXOXOS token created at the portal (default https://api.oxoxos.com/console/token), or let the repository installation Skill store it outside the plugin cache.
5. Leave image and vision model overrides empty for dynamic discovery. Confirm `uv --version` works in the environment used to launch ZCode; the installation Skill can prepare uv when it is missing.
6. Disable or uninstall the old `image-gen-mcp@game-dev` plugin so it no longer contributes `qweapi-image-gen`.
7. If an earlier installer created a user-level `mcp.servers.oxoxos-cocos-game-assets` entry, remove or disable that explicit entry after the new plugin is installed. User-scope MCP configuration overrides plugin-provided servers, so leaving it enabled would hide the bundled plugin version.
8. Open Settings → MCP and confirm the namespaced bundled `oxoxos-cocos-game-assets` server is running. The first start uses `uv` to create the isolated environment under plugin data and may take longer.
9. Start a fresh ZCode session so the MCP tools and installation Skill are injected.
10. Call `list_models` before generation.

ZCode adds the plugin identity as a namespace to its bundled MCP tools. Do not import the single plugin directory through an interface that expects a marketplace; add the repository marketplace first, then install the plugin card.

The token is mapped from plugin user configuration to `OXOXOS_API_KEY`; do not create a committed `.env` file. ZCode does not run a plugin post-install script, so `uv` in `.mcp.json` prepares Python dependencies on first MCP startup.
