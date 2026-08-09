# image-gen-mcp — 游戏开发专属素材 MCP（ZCode 插件）

把 qweapi.com 的 OpenAI 兼容接口封装成 MCP 插件：**生图 + 识图 + 参考图编辑 + 本地后处理**，供 AI 全自主开发游戏时生成与管理素材。

## 能力一览（9 工具 + 1 资源）

### 生图组（调用 qweapi API）
| 工具 | 说明 |
|---|---|
| `list_models` | 列出可用的图像生成模型 |
| `generate_image` | 生图（`gpt-image-2`），支持：`input_image` 参考图编辑、`wait=false` 后台异步 |
| `check_task` | 查询后台异步任务（配合 `wait=false`，支持批量并发） |

### 识图组（视觉，给无视觉模型补"眼睛"）
| 工具 | 说明 |
|---|---|
| `describe_image` | 用视觉模型（默认 `gpt-5.6-sol`）识别图片并回答问题，返回文本 |

> **设计原则**：若主模型本身支持看图（Claude/Gemini），直接用读图能力，无需本工具；
> 若主模型无视觉（DeepSeek 等），由 MCP 内部完成多模态，返回文本给模型。

### 后处理组（Pillow 本地执行，零 API 成本）
| 工具 | 说明 |
|---|---|
| `get_image_info` | 查询格式/尺寸/颜色模式/文件大小 |
| `crop_image` | `box=[left, top, right, bottom]` 裁剪 |
| `resize_image` | 缩放，`mode`: `stretch` / `contain` 补边 / `cover` 填满居中裁剪（推荐） |
| `convert_image` | 格式转换 png/jpeg/webp/bmp/gif；透明转 JPEG 需 `background` 颜色 |
| `slice_sprite_sheet` | 精灵图按 `cols×rows` 均匀切帧 |

### 资源
- `assets://list` — 素材目录清单（AI 跟踪已有素材，避免重复生成）

### 异步工作流（解决"同步等待浪费时间"）
```
generate_image(prompt, wait=false)  → 立即返回 {task_id}，后台线程生图
主智能体继续开发，不等待
generate_image(...) 再次批量提交   → 多个任务并发（qweapi 支持）
check_task(task_id)                 → 需要素材时查询，done 后返回文件路径
```

## qweapi 探测结论（2026-08-09 实测）

- `gpt-image-2` 支持 `model/prompt/size/quality/n` + `input_image`（参考图，实测可用）
- ❌ `style`、`background: transparent` 被服务端拒绝；`output_format` 导致服务端断连
- `gpt-5.6-sol` 视觉识图实测可用（chat/completions + image_url）
- 请求 `1024x1024` 实际返回 **1254x1254**（size 是提示性的），生成后先 `get_image_info` 确认
- 服务端偶发断连 → 客户端内置 3 次重试

## 安装（作为 ZCode 插件）

已注册进 ZCode 插件系统（市场 `game-dev`，插件 `image-gen-mcp@game-dev`），
重启 ZCode 后自动生效。可在 **Settings → 插件管理** 看到，**Settings → MCP** 查看服务器状态（显示为插件内置）。

若注册未生效，手动添加：**Settings → 插件管理 → Discover → `+` → 本地目录 → `D:\VSAI\MCP\image-gen-mcp`**。

### 密钥配置（二选一）
1. **插件设置**：插件详情页 → Advanced → 填 `api_key`（qweapi API Key）
2. **.env 文件**：插件根目录 `.env`（已配置，见下）

### .env 配置项
| 变量 | 说明 | 默认 |
|---|---|---|
| `QWAPI_BASE_URL` | API 基地址 | `https://qweapi.com/v1` |
| `QWAPI_API_KEY` | 密钥（插件 userConfig 优先，空则读 .env） | 必填 |
| `QWAPI_PROXY` | 可选代理（如 Clash 7890），留空直连 | 空 |
| `QWAPI_VISION_MODEL` | 识图模型 | `gpt-5.6-sol` |

## 开发与测试

```bash
cd D:\VSAI\MCP\image-gen-mcp
uv sync                                   # 首次安装依赖
uv run python mcp/test_api.py             # API 直连探测（消耗 1 次额度）
uv run python mcp/test_mcp.py             # MCP 全链路测试（识图/参考图/异步/后处理）
```

## 项目结构（对齐官方插件模板）

```
image-gen-mcp/                  ← 插件根目录
├── .zcode-plugin/plugin.json   # 插件清单（name/userConfig）
├── .mcp.json                   # MCP 服务声明（${ZCODE_PLUGIN_ROOT} 相对路径）
├── mcp/
│   ├── server.py               # FastMCP 入口（9 工具 + 1 资源）
│   ├── qweapi_client.py        # 生图/识图客户端
│   ├── image_processor.py      # Pillow 后处理
│   ├── test_api.py / test_mcp.py
│   └── assets/                 # 素材输出（实际在插件根目录 assets/）
├── .venv/                      # 虚拟环境（隔离依赖，uv 管理）
├── assets/                     # 默认素材输出目录
├── .env / .env.example         # 密钥配置
└── README.md
```

## 给 AI 的素材工作流建议

```
生成:    generate_image(描述, quality, filename_prefix)     （批量可用 wait=false + check_task 并发）
质检:    describe_image(图, "这张素材质量如何？风格是否统一？")
编辑:    describe_image 发现问题 → generate_image(修改要求, input_image=原图)
标准化:  get_image_info → resize_image(cover) → slice_sprite_sheet / crop_image
跟踪:    assets://list
```
