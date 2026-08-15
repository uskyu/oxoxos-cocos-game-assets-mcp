<p align="center">
  <img src="docs/images/readme-hero.webp" alt="OXOXOS Cocos Game Assets MCP" width="100%">
</p>

<h1 align="center" id="top">OXOXOS Cocos Game Assets MCP</h1>

<p align="center">
  <strong>让编码智能体完成游戏素材生成、视觉质检、参考图编辑与精灵图处理，为 Cocos Creator 提供完整的 AI 素材工作流。</strong>
</p>

<p align="center">
  <a href="README.md"><strong>简体中文</strong></a> · <a href="README.en.md">English</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/license-Apache--2.0-30d5ff" alt="Apache-2.0 License">
  <img src="https://img.shields.io/badge/Python-3.13%2B-3776ab" alt="Python 3.13+">
  <img src="https://img.shields.io/badge/MCP-compatible-ff324f" alt="MCP compatible">
</p>

> [!NOTE]
> 本项目是独立社区项目，与 Cocos 无隶属或背书关系。“Cocos”“Cocos Creator”为其各自所有者的商标。

## 先看效果

<p align="center">
  <img src="docs/images/gameplay-demo.webp" alt="AI 自动化游戏开发真实运行演示" width="800">
</p>

真实录屏经过裁剪和压缩：素材由 AI 生成，游戏代码由编码智能体编写，最终直接在 Cocos Creator 中运行。本 MCP 负责其中的**素材生成、视觉理解、参考图编辑和本地图片处理**。

<p align="center">
  <img src="docs/images/gameplay-showcase.webp" alt="四个可运行关卡的真实画面" width="100%">
</p>

## 它解决什么问题

编码型 AI 做游戏时，通常不止需要“生成一张图”。它还要发现当前可用模型、检查生成结果、根据参考图继续编辑、统一尺寸、裁切精灵图，并把文件送进游戏工程。

本项目把这条闭环封装为一组 MCP 工具，供 Claude Code、Codex、ZCode 及其他 MCP 客户端调用，并基于 [OXOXOS API](https://api.oxoxos.com) 提供生成与视觉能力。

- **实时模型发现**：运行时查询 OXOXOS 模型广场，模型 id 不写死。
- **图像生成与编辑**：使用 OpenAI 兼容图像接口，支持本地参考图。
- **视觉分析**：给不具备视觉能力的智能体补充“眼睛”，也可用于素材质检。
- **本地素材处理**：读取信息、裁剪、缩放、格式转换、精灵图切帧。
- **并发本地任务**：`wait=false` 时可并行发起多个生成任务。
- **AI 引导安装**：自动识别客户端、备份配置、保存令牌并完成验证。

<p align="center">
  <img src="docs/images/workflow.svg" alt="OXOXOS Cocos Game Assets MCP 工作流" width="100%">
</p>

## AI 全自动安装

把下面这段提示词交给 AI 即可。安装、客户端识别、配置备份、令牌初始化和验证规则都已经写在仓库内。

```text
请安装并配置这个项目：
https://github.com/uskyu/oxoxos-cocos-game-assets-mcp

请先阅读仓库中的 AGENTS.md 和安装 Skill，然后自主完成安装与初始化。
```

> [!TIP]
> AI 修改配置前会先展示计划并请求授权；获批后会自动完成配置和验证，不需要你手动编辑 JSON、TOML 或 `.env`。

### 初始化 OXOXOS API

安装完成后，对 AI 说：

> **“初始化 OXOXOS API 配置”**

AI 会自动完成：

1. 只检查令牌是否存在，不读取或回显令牌值。
2. 若缺失，引导你前往 [OXOXOS](https://api.oxoxos.com) 注册，并在[令牌管理](https://api.oxoxos.com/console/token)中创建令牌。
3. 将令牌保存到仓库外的用户私有凭据文件或客户端安全存储。
4. 启动 MCP 服务、枚举工具并调用 `list_models` 验证连通性。
5. 报告配置范围、验证结果和回滚位置。

## MCP 工具

| 工具 | 用途 |
|---|---|
| `list_models` | 获取当前模型广场列表及推断的能力提示 |
| `generate_image` | 生成或编辑图片；支持本地后台任务 |
| `check_task` | 查询后台任务状态：`running` / `done` / `error` |
| `describe_image` | 分析本地图片并返回文本 |
| `get_image_info` | 读取格式、尺寸、颜色模式、文件大小 |
| `crop_image` | 按 `[left, top, right, bottom]` 裁剪 |
| `resize_image` | 拉伸、完整放入或裁剪填充式缩放 |
| `convert_image` | 转换 PNG、JPEG、WebP、BMP、GIF |
| `slice_sprite_sheet` | 把均匀精灵图切成 PNG 单帧 |

资源 `assets://list` 可列出默认本地素材目录中的文件。

## 支持的客户端

内置安装 Skill 会先备份现有配置，再配置以下客户端：

- Claude Code
- OpenAI Codex
- ZCode（内置 `.zcode-plugin/plugin.json`）
- 通用 MCP 客户端（`.mcp.json`）

### 环境变量

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
> 已弃用的 `QWAPI_*` 变量仅在一个迁移周期内保留兼容。

## 动态模型

模型广场会持续变化。可复现的生产流程建议：

1. 调用 `list_models(force_refresh=true)`。
2. 根据当前模型文档确认所需能力。
3. 将模型 id 显式传给 `generate_image` 或 `describe_image`。

若 `model` 留空，MCP 会自动选择第一个推断候选；能力提示来自模型元数据，并非永久保证。

## 手动安装

自动安装通常已足够；如需手动配置，请查看 [`docs/installation.md`](docs/installation.md)：

- [Claude Code](docs/clients/claude-code.md)
- [OpenAI Codex](docs/clients/codex.md)
- [ZCode](docs/clients/zcode.md)
- [通用 MCP 客户端](docs/clients/generic.md)

## 更新与卸载

**更新：** 让 AI 执行：

```bash
python .agents/skills/install-oxoxos-cocos-game-assets-mcp/scripts/update.py --plan
```

更新器会拒绝覆盖未提交的改动、创建本地备份标签、使用 `--ff-only` 拉取并运行 `uv sync`，且不会触碰仓库外的私有凭据。

**卸载：** 从客户端配置中移除 `oxoxos-cocos-game-assets` 服务条目，恢复备份，并按需删除仓库外的私有凭据文件。

## 开发

```bash
uv sync --group dev
uv run pytest
uv run ruff check .
python .agents/skills/install-oxoxos-cocos-game-assets-mcp/scripts/doctor.py --json
```

> [!WARNING]
> 自动测试不会调用付费接口。`mcp/test_api.py` 与 `mcp/test_mcp.py` 是手工集成探针，可能消耗 API 额度，请先审查再运行。

## 贡献与安全

- 欢迎提交 PR，请先阅读 [`CONTRIBUTING.md`](CONTRIBUTING.md)。
- 核心代码位于 `src/oxoxos_cocos_game_assets_mcp/`。
- 不要重命名现有 MCP 工具，也不要改变其 JSON 成功 / 失败结构。
- 不要把令牌发布到公开 Issue、公共聊天、日志、源码或 Git。
- 漏洞请私下报告，详见 [`SECURITY.md`](SECURITY.md)。

## 许可证

Apache-2.0，详见 [`LICENSE`](LICENSE)。

[返回顶部](#top)
