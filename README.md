<h1 align="center" id="top">OXOXOS Cocos Game Assets MCP</h1>

<p align="center"><strong>AI 游戏素材生成 · 视觉分析 · 参考图编辑 · 精灵图处理，为 Cocos Creator 工作流打造</strong><br>
AI game asset generation, vision analysis, reference editing and sprite processing for Cocos Creator workflows.</p>

<p align="center">
  <a href="#中文"><strong>中文</strong></a> · <a href="#english"><strong>English</strong></a>
</p>

> [!NOTE]
> 独立社区项目，与 Cocos 无隶属或背书关系。“Cocos”“Cocos Creator”为其各自所有者的商标。
> Independent community project, not affiliated with or endorsed by Cocos. “Cocos” and “Cocos Creator” are trademarks of their respective owners.

---

## 中文

### AI 全自动安装（推荐，最快 5 分钟）

仓库地址：<https://github.com/uskyu/oxoxos-cocos-game-assets-mcp>

把下面整段提示词直接复制给任意支持仓库 Skill 的 AI 编码客户端（Claude Code、Codex、ZCode 等）。AI 会先展示一次计划，你批准并提供令牌后，其余全部自动完成——安装依赖、检测客户端、配置、验证，全程不需要你手工编辑任何文件。

```text
请帮我全自动安装并配置 OXOXOS Cocos Game Assets MCP：

1. 克隆仓库：git clone https://github.com/uskyu/oxoxos-cocos-game-assets-mcp.git
2. 阅读仓库内的 AGENTS.md 与 .agents/skills/install-oxoxos-cocos-game-assets-mcp/SKILL.md
3. 先运行 python .agents/skills/install-oxoxos-cocos-game-assets-mcp/scripts/install.py --plan --client auto，
   向我展示一次完整计划，等待我批准
4. 获批后先运行 install.py --apply --defer-token --client auto，自动完成依赖安装、MCP 客户端检测、
   配置备份和服务配置；令牌缺失不能阻塞插件安装
5. 安装完成后提示我对你说“初始化 OXOXOS API 配置”；届时再检查令牌、引导我创建并提供令牌，
   由你自动保存并用工具列表和 list_models 完成验证
6. 全程不要让我手工编辑 .env、JSON 或 TOML 配置文件，也不要回显或记录令牌
```

> [!TIP]
> AI 自主安装不是静默改动：修改你的配置前会先展示一次计划并获得授权；获批后则全自动完成，不再把配置工作退回给你。

### 令牌初始化对话（安装后）

安装完成后，你只需要对 AI 说一句话：

> **“初始化 OXOXOS API 配置”**

AI 会按以下流程处理：

1. 检查令牌是否已配置（只做存在性检查，不读取令牌值）。
2. 若缺失，引导你前往 <https://api.oxoxos.com> 注册 / 登录，点击左侧「令牌管理」（<https://api.oxoxos.com/console/token>），创建令牌。
3. 你在受信任的本地安装会话中把令牌交给 AI 后，它会自动保存到仓库外的用户私有凭据文件或客户端安全存储中——不回显，不写入命令行参数、日志、源码或 Git。
4. 保存后自动验证：启动 MCP 服务、枚举工具列表、调用 `list_models` 确认 API 连通。
5. 最后向你报告配置范围与验证结果。

**示例对话：**

> 你：初始化 OXOXOS API 配置
> AI：好的。目前未检测到令牌。请前往 https://api.oxoxos.com 注册/登录，点击左侧「令牌管理」，创建一个令牌后发给我。
> 你：（粘贴令牌）
> AI：已安全保存并验证通过——服务启动成功，工具列表正常，`list_models` 返回当前模型广场列表。可以直接开始生成素材了。

### 项目介绍

编码型 AI 做游戏时，通常不止需要生图：它还要发现当前可用模型、审视生成结果、基于参考图编辑、统一尺寸、裁剪精灵图，并把文件送进游戏工程。本项目把这个闭环封装成一组 MCP 工具，供 Claude Code、Codex、ZCode 及其他 MCP 客户端调用，基于 [OXOXOS API](https://api.oxoxos.com) 提供能力。

### 能力

- **实时模型发现** —— 运行时查询 OXOXOS 模型广场，模型 id 不写死。
- **图像生成** —— OpenAI 兼容图像接口，支持参考图编辑。
- **视觉分析** —— 无视觉能力的智能体可通过当前视觉模型审视本地图片。
- **本地素材处理** —— 图片信息、裁剪、缩放、格式转换、精灵图切帧（基于 Pillow）。
- **并发本地任务** —— `wait=false` 时以本地后台线程并发执行同步 API 调用。
- **智能体引导安装** —— 仓库内置 Skill 可先探测 Claude Code、Codex、ZCode 及通用 MCP 环境，再自动配置。

### 工具

| 工具 | 用途 |
|---|---|
| `list_models` | 获取当前模型广场列表及推断的能力提示 |
| `generate_image` | 生成或编辑图片；支持本地后台任务 |
| `check_task` | 查询本地任务状态：`running` / `done` / `error` |
| `describe_image` | 分析本地图片并返回文本 |
| `get_image_info` | 读取格式、尺寸、颜色模式、文件大小 |
| `crop_image` | 按 `[left, top, right, bottom]` 裁剪 |
| `resize_image` | 拉伸 / 完整放入 / 裁剪填充式缩放 |
| `convert_image` | PNG、JPEG、WebP、BMP、GIF 格式转换 |
| `slice_sprite_sheet` | 把均匀精灵图切成 PNG 单帧 |

资源：`assets://list` 列出默认本地素材目录下的文件。

### 支持客户端

内置安装 Skill 支持以下客户端，并在配置前先备份现有配置：

- Claude Code
- OpenAI Codex
- ZCode（内置插件清单 `.zcode-plugin/plugin.json`）
- 通用 MCP 客户端（`.mcp.json`）

**环境变量：**

| 变量 | 用途 | 默认值 |
|---|---|---|
| `OXOXOS_BASE_URL` | OpenAI 兼容 API 基地址 | `https://api.oxoxos.com/v1` |
| `OXOXOS_API_KEY` | 访问令牌 | 必填 |
| `OXOXOS_IMAGE_MODEL` | 可选图像模型覆盖 | 动态发现 |
| `OXOXOS_VISION_MODEL` | 可选视觉模型覆盖 | 动态发现 |
| `OXOXOS_PROXY` | 可选 HTTP 代理 | 空 |
| `OXOXOS_BRAND_NAME` | Fork 的品牌名称 | `OXOXOS` |
| `OXOXOS_PORTAL_URL` | 注册 / 登录入口 | `https://api.oxoxos.com` |
| `OXOXOS_TOKEN_URL` | 令牌管理入口 | `https://api.oxoxos.com/console/token` |

> [!NOTE]
> 已弃用的 `QWAPI_API_KEY` / `QWAPI_IMAGE_MODEL` / `QWAPI_VISION_MODEL` / `QWAPI_PROXY` 仅在一个迁移周期内保留兼容。

### 动态模型

模型广场随时可能变化。`list_models` 返回当前列表及由模型元数据推断的能力提示，这些提示并非永久保证。可复现的生产流程建议：

1. 调用 `list_models(force_refresh=true)`；
2. 按当前文档确认所选模型具备所需能力；
3. 把该模型 id 显式传给 `generate_image` 或 `describe_image`。

若 `model` 留空，MCP 自动选择第一个推断候选；你也可以本地覆盖模型而不提交到仓库。

### 手动安装（次要）

自动安装通常已足够；需要手动操作时，见 [`docs/installation.md`](docs/installation.md)：

- [Claude Code](docs/clients/claude-code.md)
- [OpenAI Codex](docs/clients/codex.md)
- [ZCode](docs/clients/zcode.md)
- [通用 MCP 客户端](docs/clients/generic.md)

### 更新与卸载

**更新：** 让 AI 执行 `python .agents/skills/install-oxoxos-cocos-game-assets-mcp/scripts/update.py --plan`。获批后，更新器会拒绝覆盖未提交的改动、创建本地备份标签、以 `--ff-only` 拉取并 `uv sync`，且不触碰仓库外的私有凭据文件。

**卸载：** 从客户端配置中移除 `oxoxos-cocos-game-assets` 服务条目，恢复更新前的备份，并按需删除仓库外的私有凭据文件。

### 开发

```bash
uv sync --group dev
uv run pytest
uv run ruff check .
python .agents/skills/install-oxoxos-cocos-game-assets-mcp/scripts/doctor.py --json
```

> [!WARNING]
> 测试不会调用付费生成接口。`mcp/test_api.py` 与 `mcp/test_mcp.py` 是手工集成探针，可能消耗 API 额度，请先审查再运行。

### 贡献

欢迎提交 PR。请先阅读 [`CONTRIBUTING.md`](CONTRIBUTING.md)。核心代码位于 `src/oxoxos_cocos_game_assets_mcp/`；不要重命名现有 MCP 工具，也不要改变其 JSON 成功/失败结构。

### 安全

- 令牌只在受信任的本地 AI 安装会话中提供一次；不要发布到公开 Issue、公共聊天、日志、源码或 Git。
- 发现漏洞请私信报告，详见 [`SECURITY.md`](SECURITY.md)。

### 许可证

Apache-2.0，详见 [`LICENSE`](LICENSE)。

[返回顶部](#top)

---

## English

### AI Auto-Install (Recommended)

Repository: <https://github.com/uskyu/oxoxos-cocos-game-assets-mcp>

Copy the whole prompt below to any MCP-capable AI coding client that supports repository skills (Claude Code, Codex, ZCode, ...). The AI shows a plan first; after you approve and provide a token, everything else is automated — dependencies, client detection, configuration, and verification. No manual file editing.

```text
Please fully auto-install and configure the OXOXOS Cocos Game Assets MCP:

1. Clone https://github.com/uskyu/oxoxos-cocos-game-assets-mcp.git
2. Read AGENTS.md and .agents/skills/install-oxoxos-cocos-game-assets-mcp/SKILL.md
3. Run python .agents/skills/install-oxoxos-cocos-game-assets-mcp/scripts/install.py --plan --client auto,
   show me the full plan and wait for my approval
4. After approval, run install.py --apply --defer-token --client auto first. Install dependencies, detect MCP clients,
   back up and configure them; a missing token must not block MCP installation
5. After installation, ask me to say “Initialize OXOXOS API configuration.” Then guide token creation if needed,
   save the token automatically, and verify with the tool list plus list_models
6. Never ask me to edit .env, JSON or TOML by hand, and never echo or log the token
```

> [!TIP]
> AI-driven install is not silent: it shows a plan and waits for approval before touching your configuration; once approved, it finishes the job without handing config work back to you.

### Token Onboarding (after install)

Once installed, just tell the AI:

> **"Initialize OXOXOS API configuration."**

The AI will:

1. Check whether a token is configured (existence check only — never reads the value).
2. If missing, walk you through <https://api.oxoxos.com>: register/login, open "Token Management" in the left sidebar (<https://api.oxoxos.com/console/token>), create a token.
3. Save it automatically to a per-user credential file outside the repository or the client's secret storage — never in command arguments, chat logs, or Git.
4. Verify: start the MCP server, enumerate tools, call `list_models`.
5. Report the config scope and verification result.

### About

A coding agent building a game needs more than image generation: it must discover current models, inspect results, edit from a reference, normalize dimensions, crop sprites, and deliver files into the project. This MCP exposes that loop as tools for Claude Code, Codex, ZCode, and other MCP clients, powered by the [OXOXOS API](https://api.oxoxos.com).

### Features

- **Live model discovery** — queries the OXOXOS model marketplace at runtime; ids are not hardcoded.
- **Image generation** — OpenAI-compatible endpoint with reference-image editing.
- **Vision analysis** — non-visual agents can inspect local images via a current vision model.
- **Local asset processing** — info, crop, resize, convert, sprite-sheet slicing (Pillow).
- **Concurrent local tasks** — `wait=false` runs synchronous calls in local background threads.
- **Agent-guided installation** — a repository Skill inspects Claude Code, Codex, ZCode, and generic MCP environments before configuring them.

### Tools

| Tool | Purpose |
|---|---|
| `list_models` | Current marketplace models and inferred capability hints |
| `generate_image` | Generate or edit images; local background tasks supported |
| `check_task` | Read local task status: `running`, `done`, `error` |
| `describe_image` | Analyze a local image, return text |
| `get_image_info` | Format, dimensions, color mode, file size |
| `crop_image` | Crop by `[left, top, right, bottom]` |
| `resize_image` | Stretch, contain, or cover resize |
| `convert_image` | Convert PNG / JPEG / WebP / BMP / GIF |
| `slice_sprite_sheet` | Split a uniform sprite sheet into PNG frames |

Resource: `assets://list` lists files in the default local asset directory.

### Supported Clients

- Claude Code
- OpenAI Codex
- ZCode (bundled `.zcode-plugin/plugin.json`)
- Generic MCP clients (`.mcp.json`)

**Environment variables:**

| Variable | Purpose | Default |
|---|---|---|
| `OXOXOS_BASE_URL` | OpenAI-compatible API base URL | `https://api.oxoxos.com/v1` |
| `OXOXOS_API_KEY` | Access token | required |
| `OXOXOS_IMAGE_MODEL` | Optional image model override | dynamic |
| `OXOXOS_VISION_MODEL` | Optional vision model override | dynamic |
| `OXOXOS_PROXY` | Optional HTTP proxy | empty |
| `OXOXOS_BRAND_NAME` | Fork brand name | `OXOXOS` |
| `OXOXOS_PORTAL_URL` | Registration / login portal | `https://api.oxoxos.com` |
| `OXOXOS_TOKEN_URL` | Token management URL | `https://api.oxoxos.com/console/token` |

> [!NOTE]
> Deprecated `QWAPI_*` variables remain for one migration cycle only.

### Dynamic Models

The marketplace changes. `list_models` returns the current list with capability hints inferred from metadata — not a permanent guarantee. For a reproducible production workflow:

1. call `list_models(force_refresh=true)`;
2. confirm the model's capability against current docs;
3. pass its id explicitly to `generate_image` / `describe_image`.

An empty `model` picks the first inferred candidate; local overrides are supported.

### Manual Install (secondary)

Auto-install is usually enough. For manual steps see [`docs/installation.md`](docs/installation.md): [Claude Code](docs/clients/claude-code.md) · [OpenAI Codex](docs/clients/codex.md) · [ZCode](docs/clients/zcode.md) · [Generic MCP](docs/clients/generic.md).

### Update & Uninstall

**Update:** ask the AI to run `python .agents/skills/install-oxoxos-cocos-game-assets-mcp/scripts/update.py --plan`. After approval, it refuses to overwrite uncommitted work, creates a backup tag, pulls with `--ff-only`, runs `uv sync`, and leaves per-user credentials untouched.

**Uninstall:** remove the `oxoxos-cocos-game-assets` entry from your client config, restore the backup, and delete the per-user credential file if desired.

### Development

```bash
uv sync --group dev
uv run pytest
uv run ruff check .
python .agents/skills/install-oxoxos-cocos-game-assets-mcp/scripts/doctor.py --json
```

> [!WARNING]
> Tests never call paid endpoints. `mcp/test_api.py` and `mcp/test_mcp.py` are manual integration probes that may consume API credit.

### Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). Core code lives in `src/oxoxos_cocos_game_assets_mcp/`. Do not rename existing MCP tools or change their JSON success/error shapes.

### Security

Provide the token once only in a trusted local AI installation session. Never publish it in public issues, shared chats, logs, source, or Git. Report vulnerabilities privately; see [`SECURITY.md`](SECURITY.md).

### License

Apache-2.0. See [`LICENSE`](LICENSE).

[Back to top](#top)
