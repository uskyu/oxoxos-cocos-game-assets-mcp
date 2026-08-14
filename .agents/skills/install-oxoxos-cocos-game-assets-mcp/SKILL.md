---
name: install-oxoxos-cocos-game-assets-mcp
description: Install, configure, verify, update, or troubleshoot the OXOXOS Cocos Game Assets MCP for Claude Code, Codex, ZCode, and other MCP clients. Use whenever the user clones this repository, asks to install the game image/vision MCP, mentions OXOXOS tokens, Cocos Creator asset generation, MCP setup, or wants an AI to complete setup automatically—even if they do not explicitly ask for this skill.
---

# Install OXOXOS Cocos Game Assets MCP

Install this repository as a local stdio MCP server. Treat repository files as the source of truth and explain every persistent change before making it.

## Automation contract

The user should not need to understand `.env`, JSON, TOML, virtual environments, or client-specific MCP syntax. The agent owns the complete flow: inspect, plan, receive one authorization, store the token, install, configure, start, and verify.

Use the bundled installer instead of asking the user to edit files:

```bash
python .agents/skills/install-oxoxos-cocos-game-assets-mcp/scripts/install.py --plan --client auto
```

For an existing installation, use the updater:

```bash
python .agents/skills/install-oxoxos-cocos-game-assets-mcp/scripts/update.py --plan
```

The updater refuses to overwrite a dirty worktree, creates a local backup tag, uses fast-forward Git updates, syncs the locked environment, and leaves credentials outside the repository. It never prints or migrates token values.

After the user approves the reported persistent changes, finish the MCP/client installation first with `--apply --defer-token --client auto`. Then ask the user to say “初始化 OXOXOS API 配置”. If the token is missing, show the portal onboarding steps. After the user intentionally provides it, supply it to the installer through standard input with `--apply --token-stdin --client auto`, then run `verify.py --live-models`. Do not place the token in command arguments. If the harness cannot safely pass a secret without recording it, use a secret-aware file API or the client's secret UI—do not fall back to manual `.env` instructions.

## Safety boundary

- Accept the token once when the user intentionally provides it for installation, then configure it automatically.
- Never echo, log, commit, or place the token in a command-line argument or generated report.
- Store it in the installer-managed per-user credential file with user-only permissions, outside the repository.
- Never read an existing secret value merely to prove it exists. Check only whether the credential is configured.
- Back up an existing client configuration before editing it.
- Do not install dependencies or edit user-level configuration until the user approves the installer plan.
- Keep stdio stdout reserved for MCP JSON-RPC. Diagnostics belong on stderr.

## Workflow

### 0. Separate installation from token onboarding

Install the MCP and client entry first. A missing token must not block dependency installation or client configuration: use `--defer-token`. Before the first remote tool call, check whether a token is configured with the read-only doctor; never read an existing secret value.

- Token already configured: run live model verification.
- Token missing after installation: do not ask the user to edit files. Explain the onboarding flow instead:
  1. 前往 OXOXOS 门户注册或登录（默认 https://api.oxoxos.com）；
  2. 登录后，在左侧导航栏进入「令牌管理」；
  3. 创建一个访问令牌；
  4. 把令牌直接发给当前 AI 助手。
- After the user hands over the token, the AI automatically saves it, configures the client, and verifies the MCP — the user does not edit `.env`, JSON, or TOML.

The default portal is the official service. A fork of this repository can override the brand name and portal/token URLs (for example `OXOXOS_BRAND_NAME`, `OXOXOS_PORTAL_URL`, `OXOXOS_TOKEN_URL` in the fork's `.env`); the onboarding guide shown to the user adapts to those values automatically.

### 1. Read and inspect

Read these files before proposing installation:

- `README.md`
- `pyproject.toml`
- `.env.example`
- `.mcp.json`
- the reference file for the detected client

Run `python .agents/skills/install-oxoxos-cocos-game-assets-mcp/scripts/doctor.py --json` when Python is available. It is read-only and reports paths and readiness without revealing secret values.

### 2. Identify the client and scope

Determine whether the user is using Claude Code, Codex, ZCode, or another MCP client. If more than one is installed, ask which clients to configure and whether the scope is project or user.

Read one of:

- `references/claude-code.md`
- `references/codex.md`
- `references/zcode.md`
- `references/generic-mcp.md`

Do not assume one client's configuration syntax works in another.

### 3. Present a concrete plan

Show:

- dependency command and target environment;
- exact config file or client command to be used;
- server name: `oxoxos-cocos-game-assets`;
- command and arguments that will start `mcp/server.py`;
- how `OXOXOS_API_KEY` will be supplied;
- backup and rollback steps;
- which steps need network access.

Wait for approval before installation or persistent configuration changes.

### 4. Install dependencies

Prefer the repository's locked uv environment:

```bash
uv sync
```

If uv is unavailable, explain how to install uv from its official documentation or offer an isolated virtual environment plus `python -m pip install -e .`. Do not silently install uv or use administrator privileges.

### 5. Configure the token safely

If the user has not provided a token yet, guide them once through the onboarding flow from step 0: register or log in at the portal (default https://api.oxoxos.com), open 「令牌管理」 in the left sidebar, create a token, and send it to the AI. Then the agent runs the installer automatically to save the token, configure the client, and verify — the user never edits configuration files by hand.

Preferred methods for receiving the token, in order:

1. the client's secret/user configuration UI;
2. an environment variable already supplied by the user outside chat;
3. a local ignored `.env` file created by the user on a trusted machine.

Use `OXOXOS_API_KEY`. `QWAPI_API_KEY` is a deprecated compatibility alias only.

Do not hardcode image or vision model ids. The model marketplace changes. Leave `OXOXOS_IMAGE_MODEL` and `OXOXOS_VISION_MODEL` empty unless the user chooses explicit ids from the live `list_models` result.

### 6. Configure the client

Use the selected client's reference. Prefer an absolute repository path and the environment's Python executable. Preserve unrelated config entries and formatting as far as the client format permits.

### 7. Verify without spending generation credit

First verify only:

1. server process starts;
2. MCP initialization succeeds;
3. tool list contains `list_models`, `generate_image`, `describe_image`, and local processing tools;
4. `list_models` succeeds and returns the current marketplace list;
5. no secret appears in stdout, stderr, or returned JSON.

Ask separately before a paid image or vision request. If approved, use one minimal request, save it in a temporary or user-selected project directory, and report any charge-producing action.

### 8. Report and rollback

Report:

- files changed;
- config scope;
- verification results;
- unverified paid capabilities;
- how to remove the MCP entry and restore the backup.

If any step fails, stop that path, preserve the exact non-secret error, and use `references/troubleshooting.md`. Do not improvise repeated destructive edits.

## Completion criteria

Installation is complete only when the selected client can initialize the server and enumerate tools. A valid config file alone is not proof of success.

## Disclaimer

This is an independent community project oriented toward Cocos Creator workflows. It is not affiliated with or endorsed by Cocos.
