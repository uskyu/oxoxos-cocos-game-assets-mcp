# OXOXOS Cocos Game Assets MCP

**AI game asset generation, vision analysis, reference editing, and sprite processing for Cocos Creator workflows.** Powered by the [OXOXOS API](https://api.oxoxos.com) and exposed through the Model Context Protocol (MCP).

> Independent community project. Not affiliated with or endorsed by Cocos. “Cocos” and “Cocos Creator” are trademarks of their respective owners.

[中文](#中文快速开始) · [Installation](docs/installation.md) · [Security](SECURITY.md) · [Contributing](CONTRIBUTING.md)

## Why this project

A coding agent building a game often needs more than image generation. It must discover current models, inspect the result, edit from a reference, normalize dimensions, crop sprites, and deliver files into the game project. This MCP exposes that loop as tools that Claude Code, Codex, ZCode, and other MCP clients can call.

## Features

- **Live model discovery** — queries the OXOXOS model marketplace at runtime; model ids are not permanently hardcoded.
- **Image generation** — OpenAI-compatible image endpoint with optional reference-image editing.
- **Vision analysis** — lets a non-visual agent inspect a local image through a current vision-capable model.
- **Local asset processing** — image info, crop, resize, convert, and sprite-sheet slicing through Pillow.
- **Concurrent local tasks** — `wait=false` runs synchronous API calls in local background threads.
- **Agent-guided installation** — a repository Skill can inspect Claude Code, Codex, ZCode, and generic MCP environments before configuring them.

## Tools

| Tool | Purpose |
|---|---|
| `list_models` | Fetch current marketplace models and inferred capability hints |
| `generate_image` | Generate or edit images; supports local background tasks |
| `check_task` | Read local task status: `running`, `done`, or `error` |
| `describe_image` | Analyze a local image and return text |
| `get_image_info` | Read format, dimensions, color mode, and file size |
| `crop_image` | Crop by `[left, top, right, bottom]` |
| `resize_image` | Stretch, contain, or cover-resize |
| `convert_image` | Convert PNG, JPEG, WebP, BMP, or GIF |
| `slice_sprite_sheet` | Split a uniform sprite sheet into PNG frames |

Resource: `assets://list` lists files in the default local asset directory.

## 中文快速开始

### 1. 克隆并安装依赖

```bash
git clone https://github.com/uskyu/oxoxos-cocos-game-assets-mcp.git
cd oxoxos-cocos-game-assets-mcp
uv sync
```

仓库地址：<https://github.com/uskyu/oxoxos-cocos-game-assets-mcp>

### 2. 创建 API 令牌

- API 基础地址：`https://api.oxoxos.com`
- 数据看板：`https://api.oxoxos.com/console`
- 令牌管理：`https://api.oxoxos.com/console/token`

令牌应通过客户端的安全配置或环境变量 `OXOXOS_API_KEY` 传递。不要把令牌发到聊天、写入源码或提交到 Git。

### 3. 让 AI 全自动安装

克隆仓库后，把以下提示词交给支持仓库 Skill 的 AI 编码客户端。用户只需提供一次令牌并批准安装计划，AI 应完成依赖、私有凭据、客户端配置和连通验证；不应要求用户手工编辑 `.env`、JSON 或 TOML：

> 阅读 `AGENTS.md` 和 `.agents/skills/install-oxoxos-cocos-game-assets-mcp/SKILL.md`，运行安装器 `--plan --client auto` 并向我展示一次计划。经我确认并提供 OXOXOS 令牌后，通过标准输入把令牌交给安装器，自动保存到仓库外的用户私有凭据文件、安装依赖、备份并配置检测到的客户端、启动 MCP，并用工具列表和 `list_models` 完成验证。不要回显令牌，不要让我手工编辑配置，不要在未经确认时调用付费生图或识图。

AI 自主安装不是静默破坏：修改用户配置前展示一次计划并获得授权；获批后应自动完成，不再把配置工作退回给用户。

### 4. 手动安装

详见 [`docs/installation.md`](docs/installation.md)：

- [Claude Code](docs/clients/claude-code.md)
- [OpenAI Codex](docs/clients/codex.md)
- [ZCode](docs/clients/zcode.md)
- [通用 MCP 客户端](docs/clients/generic.md)

## Configuration

| Variable | Purpose | Default |
|---|---|---|
| `OXOXOS_BASE_URL` | OpenAI-compatible API base URL | `https://api.oxoxos.com/v1` |
| `OXOXOS_API_KEY` | Access token | required |
| `OXOXOS_IMAGE_MODEL` | Optional image model override | dynamically discovered |
| `OXOXOS_VISION_MODEL` | Optional vision model override | dynamically discovered |
| `OXOXOS_PROXY` | Optional HTTP proxy | empty |

Deprecated `QWAPI_API_KEY`, `QWAPI_IMAGE_MODEL`, `QWAPI_VISION_MODEL`, and `QWAPI_PROXY` variables remain for one migration cycle. The old service base URL is not retained; use `OXOXOS_BASE_URL` for an explicit development override.

### Dynamic model behavior

The marketplace may change. `list_models` returns the current list and capability hints inferred from model metadata. Those hints are not a permanent guarantee. For a reproducible production workflow:

1. call `list_models(force_refresh=true)`;
2. select a model whose current documentation confirms the needed capability;
3. pass its id explicitly to `generate_image` or `describe_image`.

If `model` is left empty, the MCP chooses the first inferred candidate. You can also set local model overrides without committing them.

## Update behavior

Existing users can ask the repository Skill to run:

```bash
python .agents/skills/install-oxoxos-cocos-game-assets-mcp/scripts/update.py --plan
```

After approval, the updater refuses to overwrite uncommitted work, creates a local backup tag, pulls with `--ff-only`, runs `uv sync`, and leaves the per-user OXOXOS credential file untouched. It does not silently reset or roll back a failed update; it reports the backup tag for review.

## Local task behavior

`wait=false` does **not** create a server-side async OXOXOS job. It starts a local daemon thread, returns a task id, and stores status in memory. Tasks are lost when the MCP process restarts. Use it for concurrent requests within one client session, not durable job processing.

## Development

```bash
uv sync --group dev
uv run pytest
uv run ruff check .
python .agents/skills/install-oxoxos-cocos-game-assets-mcp/scripts/doctor.py --json
```

Tests do not call paid generation endpoints. The legacy `mcp/test_api.py` and `mcp/test_mcp.py` are manual integration probes and can consume API credit; run them only after reviewing their behavior.

## Repository layout

```text
.
├── src/oxoxos_cocos_game_assets_mcp/       # publishable Python package
├── mcp/                              # compatibility launchers and manual probes
├── tests/                            # offline unit tests
├── .agents/skills/                   # cross-agent installation Skill
├── docs/clients/                     # client-specific installation guides
├── .zcode-plugin/plugin.json         # ZCode plugin manifest
├── .mcp.json                         # bundled ZCode MCP declaration
├── AGENTS.md / CLAUDE.md             # repository agent instructions
└── pyproject.toml
```

## Search and discovery

Recommended repository name: `oxoxos-cocos-game-assets-mcp`. Recommended GitHub topics:

`cocos`, `cocos-creator`, `game-assets`, `mcp`, `model-context-protocol`, `image-generation`, `vision`, `ai-game-development`, `python`, `fastmcp`, `claude-code`, `codex`, `zcode`, `oxoxos`.

Use relevant topics only. This repository does not claim an official Cocos relationship.

## License

Apache-2.0. See [`LICENSE`](LICENSE).
