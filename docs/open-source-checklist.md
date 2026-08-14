# Open-source release checklist

- [x] Rename the GitHub repository to `oxoxos-cocos-game-assets-mcp`.
- [x] Replace every `<PUBLIC_REPOSITORY_URL>` placeholder.
- [ ] Enable GitHub private vulnerability reporting and update `SECURITY.md` contact details.
- [ ] Confirm copyright ownership for every tracked image, logo, and anime-inspired asset.
- [ ] Rotate the local development token and inspect Git history and CI logs for secrets.
- [ ] Run a secret scanner against the full Git history.
- [ ] Align package, plugin, tag, and release versions.
- [ ] Run CI on Windows and Linux.
- [ ] Publish a signed/tagged GitHub release before publishing PyPI or MCP Registry metadata.
- [ ] Configure PyPI Trusted Publishing; do not store a long-lived PyPI token.
- [ ] Reserve the PyPI name `oxoxos-cocos-game-assets-mcp` if available.
- [ ] Choose an MCP Registry namespace after the public GitHub owner is final, then create `server.json` whose package identifier and version match the published artifact.
- [ ] Add accurate GitHub description and relevant topics; do not imply official Cocos affiliation.
- [ ] Verify Claude Code, Codex, and ZCode instructions against their current releases.
- [ ] Test fresh-clone installation without a developer `.env` file.
- [ ] Verify `update.py --plan` on a clean clone and confirm dirty-worktree refusal.
- [ ] Verify an update preserves the per-user credential file and creates a rollback tag.
