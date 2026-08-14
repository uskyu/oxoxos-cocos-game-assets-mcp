# Troubleshooting

## Server is missing

- Confirm the client is reading the intended project/user scope.
- Use absolute paths.
- Confirm the configured Python executable exists.
- Restart the client after changing MCP configuration.

## Server exits immediately

Run the same command in a terminal and inspect stderr. Do not redirect MCP stdout to a normal log file because stdout carries JSON-RPC.

## Token error

Check only whether `OXOXOS_API_KEY` is present and non-empty. Never print it. Create or rotate tokens at https://api.oxoxos.com/console/token.

## No model can be selected

Call `list_models(force_refresh=true)`. Capability labels are inferred from changing marketplace metadata. Pass a known model id explicitly or set `OXOXOS_IMAGE_MODEL` / `OXOXOS_VISION_MODEL` locally.

## Windows path error

Use an absolute `.venv\Scripts\python.exe` path. In JSON, escape backslashes or use forward slashes.

## Existing entry conflict

Back up the client config and compare the existing entry. Ask whether to update, use another name, or leave it untouched. Never overwrite silently.
