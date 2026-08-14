"""OXOXOS Cocos Game Assets MCP server backed by the OXOXOS API.

The server exposes live model discovery, image generation, vision analysis,
reference-image editing, local background tasks, and Pillow post-processing.
It is an independent community project and is not affiliated with Cocos.
"""
from __future__ import annotations

import json
import re
import sys
import threading
import uuid
from pathlib import Path

from fastmcp import FastMCP

try:
    from . import image_processor as ip
    from .oxoxos_client import (
        OxoxosApiError,
        TokenSetupRequired,
        token_setup_guide,
    )
    from .oxoxos_client import (
        describe_image as api_describe_image,
    )
    from .oxoxos_client import (
        generate_image as api_generate_image,
    )
    from .oxoxos_client import (
        list_models as api_list_models,
    )
except ImportError:  # Direct script execution from the repository.
    import image_processor as ip
    from oxoxos_client import (
        OxoxosApiError,
        TokenSetupRequired,
        token_setup_guide,
    )
    from oxoxos_client import (
        describe_image as api_describe_image,
    )
    from oxoxos_client import (
        generate_image as api_generate_image,
    )
    from oxoxos_client import (
        list_models as api_list_models,
    )

# Repository/plugin root for editable installs and local plugin execution.
PROJECT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_ASSETS_DIR = PROJECT_DIR / "assets"

mcp = FastMCP("oxoxos-cocos-game-assets-mcp")

# 后台任务注册表：task_id -> {status: running|done|error, ...}
_TASKS: dict[str, dict] = {}
_TASKS_LOCK = threading.Lock()


def _log(msg: str) -> None:
    print(f"[oxoxos-cocos-game-assets-mcp] {msg}", file=sys.stderr, flush=True)


def _resolve_dir(output_dir: str) -> Path:
    """output_dir 相对路径基于插件根目录解析，绝对路径直接用。"""
    d = Path(output_dir)
    if not d.is_absolute():
        d = PROJECT_DIR / d
    d.mkdir(parents=True, exist_ok=True)
    return d


def _unique_path(directory: Path, prefix: str, ext: str, idx: int = 0) -> Path:
    """生成不冲突的文件名：prefix[_i].ext"""
    while True:
        name = f"{prefix}{'' if idx == 0 else f'_{idx}'}.{ext}"
        p = directory / name
        if not p.exists():
            return p
        idx += 1


def _safe_prefix(name: str) -> str:
    """文件名前缀去掉非法字符，防止 AI 传入含路径分隔符/特殊字符的名字。"""
    return re.sub(r"[^\w\-]", "_", name).strip("_") or "img"


def _api_error(e: Exception) -> str:
    """把异常转成给 AI 的清晰错误信息（JSON 字符串）。"""
    payload = {"ok": False, "error": str(e)}
    if isinstance(e, TokenSetupRequired):
        payload["setup"] = token_setup_guide()
    return json.dumps(payload, ensure_ascii=False)


def _save_result(result, out_dir: Path, filename_prefix: str) -> list[str]:
    """把 GenerationResult 的图片落盘，返回绝对路径列表。"""
    saved = []
    for i, img_bytes in enumerate(result.images):
        p = _unique_path(out_dir, _safe_prefix(filename_prefix), "png", i)
        p.write_bytes(img_bytes)
        saved.append(str(p.resolve()))
    return saved


# ---------------------------------------------------------------- 生图组

@mcp.tool()
def list_models(force_refresh: bool = False) -> str:
    """查询 OXOXOS 模型广场的实时模型列表及能力提示。

    模型可能随模型广场变化。生成或识图前可调用本工具；capabilities 是根据
    服务端元数据推断的提示，不是永久能力保证。force_refresh=true 可跳过进程缓存。
    """
    try:
        models = api_list_models(force_refresh=force_refresh)
        if not models:
            return json.dumps({"ok": True, "models": [], "note": "模型广场当前未返回模型"}, ensure_ascii=False)
        lines = ["| id | type | capabilities |", "|---|---|---|"]
        lines += [f"| {m['id']} | {m['type']} | {', '.join(m['capabilities'])} |" for m in models]
        return json.dumps({"ok": True, "models": models, "table": "\n".join(lines)}, ensure_ascii=False)
    except OxoxosApiError as e:
        return _api_error(e)


@mcp.tool()
def generate_image(
    prompt: str,
    model: str = "",
    size: str = "1024x1024",
    quality: str = "auto",
    n: int = 1,
    input_image: str = "",
    wait: bool = True,
    output_dir: str = "assets",
    filename_prefix: str = "img",
) -> str:
    """通过 OXOXOS API 生成图片（支持参考图编辑与本地后台任务）。

    参数：
    - prompt: 图片描述。带 input_image 时描述"如何修改参考图"
    - model: 模型 id。留空时从实时模型列表自动选择；生产任务建议先 list_models 后显式选择
    - input_image: 参考图本地路径或 http(s) URL，传入后基于参考图生成/编辑
    - size/quality/n: OpenAI 兼容枚举；具体支持范围以当前模型为准
    - wait: true=同步等待返回文件路径；false=后台生成立即返回 task_id，
            之后用 check_task(task_id) 查询；可一次发多个任务实现批量并发
    - output_dir/filename_prefix: 保存位置与文件名前缀（相对路径基于插件根目录）

    注意：实际输出尺寸可能与 size 不同（如请求 1024x1024 返回 1254x1254），
    请先 get_image_info 确认尺寸，再 resize_image 处理。
    返回 JSON：wait=true 时 {ok, images:[绝对路径], notes}；wait=false 时 {ok, task_id, status:"running"}。
    """
    try:
        out_dir = _resolve_dir(output_dir)
        if not wait:
            task_id = uuid.uuid4().hex[:12]
            with _TASKS_LOCK:
                _TASKS[task_id] = {"status": "running"}
                if len(_TASKS) > 100:  # 防止任务无限累积
                    oldest = next(iter(_TASKS))
                    _TASKS.pop(oldest, None)
            args = (task_id, prompt, model, size, quality, n, input_image, str(out_dir), filename_prefix)
            threading.Thread(target=_run_gen_task, args=args, daemon=True).start()
            _log(f"generate_image 后台任务 {task_id} 已启动")
            return json.dumps(
                {
                    "ok": True,
                    "task_id": task_id,
                    "status": "running",
                    "note": "后台生成中，稍后用 check_task(task_id) 查询结果",
                },
                ensure_ascii=False,
            )
        result = api_generate_image(
            prompt=prompt, model=model, size=size, quality=quality, n=n, input_image=input_image
        )
        saved = _save_result(result, out_dir, filename_prefix)
        _log(f"generate_image: {len(saved)} 张 -> {saved}")
        return json.dumps(
            {"ok": True, "images": saved, "count": len(saved), "notes": result.notes},
            ensure_ascii=False,
        )
    except (OxoxosApiError, ValueError) as e:
        return _api_error(e)


def _run_gen_task(
    task_id: str, prompt: str, model: str, size: str, quality: str, n: int,
    input_image: str, out_dir: str, filename_prefix: str,
) -> None:
    """后台线程执行生图并落盘，结果写回 _TASKS。"""
    try:
        result = api_generate_image(
            prompt=prompt, model=model, size=size, quality=quality, n=n, input_image=input_image
        )
        saved = _save_result(result, Path(out_dir), filename_prefix)
        with _TASKS_LOCK:
            _TASKS[task_id] = {"status": "done", "images": saved, "count": len(saved), "notes": result.notes}
        _log(f"后台任务 {task_id} 完成: {saved}")
    except Exception as e:  # noqa: BLE001 —— 后台任务必须捕获所有异常
        with _TASKS_LOCK:
            _TASKS[task_id] = {"status": "error", "error": str(e)}
        _log(f"后台任务 {task_id} 失败: {e}")


@mcp.tool()
def check_task(task_id: str) -> str:
    """查询后台生图任务状态：{status: running|done|error, images?, error?}。

    配合 generate_image(wait=false) 使用；done 后 images 为文件绝对路径列表。
    """
    with _TASKS_LOCK:
        t = _TASKS.get(task_id)
    if t is None:
        return _api_error(ValueError(f"任务不存在: {task_id}（任务表重启后清空，注意服务器进程重启会丢失任务）"))
    return json.dumps({"ok": True, "task_id": task_id, **t}, ensure_ascii=False)


# ---------------------------------------------------------------- 识图组

@mcp.tool()
def describe_image(
    image_path: str,
    question: str = "请详细描述这张图片的内容、风格和构图。",
    model: str = "",
) -> str:
    """用 OXOXOS 模型广场中的视觉模型识别图片并返回文本。

    model 留空时动态发现候选模型；生产任务建议先调用 list_models 并显式选择。

    用途：
    - 给无视觉能力的模型（如 DeepSeek）补充"眼睛"——多模态在 MCP 内部完成
    - 素材质检：让视觉模型审视生成结果，判断是否符合要求
    - 编辑依据：先 describe_image 了解图片现状，再 generate_image(input_image=...) 编辑
    注意：若主模型本身支持看图（如 Claude/Gemini），可直接读图文件，无需本工具。
    """
    try:
        answer = api_describe_image(image_path, question, model=model)
        return json.dumps({"ok": True, "answer": answer}, ensure_ascii=False)
    except OxoxosApiError as e:
        return _api_error(e)


# ---------------------------------------------------------------- 后处理组

@mcp.tool()
def get_image_info(image_path: str) -> str:
    """查询图片信息（格式/尺寸/颜色模式/文件大小），生成后先查尺寸再规划裁剪。"""
    try:
        return json.dumps({"ok": True, **ip.get_image_info(image_path)}, ensure_ascii=False)
    except (ValueError, FileNotFoundError) as e:
        return _api_error(e)


@mcp.tool()
def crop_image(image_path: str, box: list[int], output_path: str = "") -> str:
    """按 box=[left, top, right, bottom] 裁剪图片，返回新文件绝对路径。
    box 必须严格在图片范围内。output_path 留空则自动命名（不覆盖原图）。"""
    try:
        p = ip.crop_image(image_path, box, output_path or None)
        return json.dumps({"ok": True, "output_path": p, "box": box}, ensure_ascii=False)
    except (ValueError, FileNotFoundError) as e:
        return _api_error(e)


@mcp.tool()
def resize_image(
    image_path: str,
    width: int,
    height: int,
    mode: str = "stretch",
    output_path: str = "",
) -> str:
    """缩放到 width×height。mode:
    - stretch: 拉伸（可能变形）
    - contain: 完整放入画布居中，透明补透明/否则补黑
    - cover: 填满并居中裁剪（不变形，可能裁边缘，适合游戏素材标准化）"""
    try:
        p = ip.resize_image(image_path, width, height, mode, output_path or None)
        return json.dumps(
            {"ok": True, "output_path": p, "size": f"{width}x{height}", "mode": mode},
            ensure_ascii=False,
        )
    except (ValueError, FileNotFoundError) as e:
        return _api_error(e)


@mcp.tool()
def convert_image(
    image_path: str,
    output_format: str = "png",
    background: str = "",
    output_path: str = "",
) -> str:
    """格式转换（png/jpeg/webp/bmp/gif）。透明图转 jpeg 必须提供 background 颜色
    （如 'white'/'#ff0000'/'255,0,0'）。"""
    try:
        p = ip.convert_image(image_path, output_format, background or None, output_path or None)
        return json.dumps(
            {"ok": True, "output_path": p, "format": output_format}, ensure_ascii=False
        )
    except (ValueError, FileNotFoundError) as e:
        return _api_error(e)


@mcp.tool()
def slice_sprite_sheet(
    image_path: str,
    cols: int,
    rows: int,
    output_dir: str = "",
) -> str:
    """把精灵图按 cols×rows 均匀切成单帧 PNG（文件命名 {源名}_r{行}c{列}.png）。
    图片尺寸必须能被 cols×rows 整除；不能整除时先 resize_image 调整。"""
    try:
        d = _resolve_dir(output_dir) if output_dir else None
        saved = ip.slice_sprite_sheet(image_path, cols, rows, str(d) if d else None)
        return json.dumps(
            {"ok": True, "frames": saved, "count": len(saved), "grid": f"{cols}x{rows}"},
            ensure_ascii=False,
        )
    except (ValueError, FileNotFoundError) as e:
        return _api_error(e)


# ---------------------------------------------------------------- 资源

@mcp.resource("assets://list")
def asset_list() -> str:
    """列出默认素材目录（assets/）下的所有图片文件，供 AI 跟踪已生成的素材。"""
    if not DEFAULT_ASSETS_DIR.exists():
        return "assets/ 目录为空（尚无素材）"
    files = [p for p in sorted(DEFAULT_ASSETS_DIR.rglob("*")) if p.is_file()]
    if not files:
        return "assets/ 目录为空（尚无素材）"
    lines = ["| 文件 | 相对路径 | 大小 |", "|---|---|---|"]
    for p in files:
        rel = p.relative_to(PROJECT_DIR).as_posix()
        lines.append(f"| {p.name} | {rel} | {p.stat().st_size} B |")
    return "\n".join(lines)


def main() -> None:
    """Run the stdio MCP server without writing protocol-breaking stdout logs."""
    _log(f"服务器启动，插件根目录: {PROJECT_DIR}，assets: {DEFAULT_ASSETS_DIR}")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
