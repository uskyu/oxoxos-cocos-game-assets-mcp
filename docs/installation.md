# Installation

## Prerequisites

- Python 3.13 or newer for the current locked project
- [uv](https://docs.astral.sh/uv/) recommended
- an MCP-compatible client
- an OXOXOS token from https://api.oxoxos.com/console/token

## Install the repository

```bash
git clone https://github.com/uskyu/oxoxos-cocos-game-assets-mcp.git
cd oxoxos-cocos-game-assets-mcp
uv sync
```

The virtual-environment Python is `.venv/bin/python` on macOS/Linux and `.venv\Scripts\python.exe` on Windows.

## Fully automated AI path

Use `.agents/skills/install-oxoxos-cocos-game-assets-mcp/SKILL.md`. The agent runs the installer plan, receives one approval and one token, then automatically stores the token outside the repository, installs dependencies, backs up and configures detected clients, and verifies initialization plus live model discovery. The user does not edit `.env`, JSON, or TOML.

Read-only doctor:

```bash
python .agents/skills/install-oxoxos-cocos-game-assets-mcp/scripts/doctor.py --json
```

## Manual path

Choose a client guide:

- [Claude Code](clients/claude-code.md)
- [Codex](clients/codex.md)
- [ZCode](clients/zcode.md)
- [Generic MCP](clients/generic.md)

Use an absolute Python path and an absolute `mcp/server.py` path. Supply `OXOXOS_API_KEY` through the client's secret/environment mechanism.

## Verify

Verify in this order:

1. server initialization;
2. tool enumeration;
3. `list_models`;
4. local image-processing tools;
5. only with separate approval, one minimal paid generation or vision request.

## Update

Ask the Skill to run the read-only updater plan:

```bash
python .agents/skills/install-oxoxos-cocos-game-assets-mcp/scripts/update.py --plan
```

After approval, it refuses to overwrite a dirty worktree, creates a local backup tag, pulls with `--ff-only`, runs `uv sync`, and reports the exact verification/rollback point. It keeps the per-user credential file and client configuration backups outside the repository. Do not automatically track an unpinned development branch in production.

## Uninstall

Remove only the `oxoxos-cocos-game-assets` MCP entry, restore the prior configuration backup if necessary, and delete the cloned repository. Revoking the OXOXOS token is recommended when the installation is no longer used.
