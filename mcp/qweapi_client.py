"""qweapi 客户端：生图 + 识图（OpenAI 兼容接口薄封装）。

探测结论（2026-08-09 实测）：
- 基地址 https://qweapi.com/v1，同步返回，格式为 OpenAI 标准 data[i].b64_json（PNG）
- gpt-image-2 支持 model/prompt/size/quality/n + input_image（参考图编辑，实测可用）；
  style、background(transparent) 被服务端拒绝；output_format 会导致服务端断连
- gpt-5.6-sol 支持视觉识图（chat/completions 带 image_url，实测可用）
- 请求 1024x1024 实际返回 1254x1254（size 是提示性的）
- 服务端偶发断连 → 内置 3 次指数退避重试
"""
from __future__ import annotations

import base64
import mimetypes
import os
import time
from dataclasses import dataclass, field
from pathlib import Path

import httpx
from dotenv import dotenv_values, load_dotenv

# 插件根目录（本文件位于 <root>/mcp/ 下）
PROJECT_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_DIR / ".env"
load_dotenv(ENV_FILE)
_env = dotenv_values(ENV_FILE)


def _env_or_file(key: str, default: str = "") -> str:
    """环境变量优先（ZCode 插件 userConfig 注入），空则回退 .env 文件。"""
    v = os.getenv(key)
    if v is None or not v.strip():
        v = _env.get(key, "")
    return v.strip() or default


BASE_URL = _env_or_file("QWAPI_BASE_URL", "https://qweapi.com/v1").rstrip("/")
API_KEY = _env_or_file("QWAPI_API_KEY")
PROXY = _env_or_file("QWAPI_PROXY")
VISION_MODEL = _env_or_file("QWAPI_VISION_MODEL", "gpt-5.6-sol")

# 官方文档枚举（用于本地校验）
SUPPORTED_QUALITY = {"low", "medium", "high", "auto"}
SUPPORTED_SIZES = {"1024x1024", "1536x1024", "1024x1536", "auto"}
MAX_INPUT_IMAGE_MB = 8  # 参考图大小上限

# 探测确认不支持的参数（本地区分，避免服务端报错/断连）
UNSUPPORTED_PARAMS = {
    "style": "qweapi 的 gpt-image-2 不支持 style 参数（Unknown parameter）",
    "background": "qweapi 的 gpt-image-2 不支持透明背景（Transparent background is not supported for this model），"
    "生成后可用 image_processor.convert_image 处理背景",
    "output_format": "qweapi 的 gpt-image-2 不支持 output_format 参数（服务端会断连），始终返回 PNG",
}

_RETRIES = 3
_RETRY_BACKOFF = (1.0, 2.0)


class QweApiError(RuntimeError):
    """带服务端原始错误信息的业务异常，透传给调用方（AI）。"""


@dataclass
class GenerationResult:
    """一次生图调用的结果。images: 已解码的图片字节；notes: 给 AI 的补充说明。"""

    images: list[bytes]
    notes: list[str] = field(default_factory=list)


def _make_client() -> httpx.Client:
    if not API_KEY:
        raise QweApiError("未配置 QWAPI_API_KEY：请在插件设置（userConfig）或 .env 中填写")
    return httpx.Client(
        base_url=BASE_URL,
        headers={"Authorization": f"Bearer {API_KEY}"},
        proxy=PROXY or None,
        timeout=180.0,
    )


def _post_with_retry(path: str, payload: dict) -> httpx.Response:
    """POST 请求，连接类错误（断连/连接失败）指数退避重试。"""
    last_exc: Exception | None = None
    for attempt in range(_RETRIES):
        try:
            with _make_client() as c:
                return c.post(path, json=payload)
        except (httpx.RemoteProtocolError, httpx.ConnectError, httpx.ReadError) as e:
            last_exc = e
            if attempt < _RETRIES - 1:
                time.sleep(_RETRY_BACKOFF[attempt])
    raise QweApiError(
        f"连接 qweapi 失败（已重试 {_RETRIES} 次）：{last_exc}。"
        f"可检查网络/代理（QWAPI_PROXY={PROXY or '直连'}）"
    )


def _raise_for_status(r: httpx.Response, action: str) -> None:
    if r.status_code == 200:
        return
    try:
        err = r.json().get("error", {}).get("message", r.text)
    except Exception:
        err = r.text
    raise QweApiError(f"{action}失败 HTTP {r.status_code}: {err}")


# ---------------------------------------------------------------- 模型列表

def list_models() -> list[dict]:
    """获取模型列表，过滤出图像生成模型。"""
    try:
        with _make_client() as c:
            r = c.get("/models")
    except (httpx.RemoteProtocolError, httpx.ConnectError, httpx.ReadError) as e:
        raise QweApiError(f"获取模型列表失败（网络错误）：{e}") from e
    _raise_for_status(r, "获取模型列表")
    data = r.json().get("data", [])
    images = []
    for m in data:
        id_, typ = str(m.get("id", "")), str(m.get("type", ""))
        if "image" in id_.lower() or "image" in typ.lower():
            images.append({"id": id_, "type": typ})
    return images


# ---------------------------------------------------------------- 生图

def _resolve_input_image(input_image: str) -> str:
    """参考图参数：本地路径 → base64 data URL；http(s) URL 原样透传。"""
    s = input_image.strip()
    if not s:
        raise QweApiError("input_image 为空")
    if s.startswith(("http://", "https://")):
        return s
    p = Path(s)
    if not p.is_absolute():
        p = (PROJECT_DIR / p).resolve()
    if not p.exists():
        raise QweApiError(f"参考图不存在: {p}")
    size_mb = p.stat().st_size / (1024 * 1024)
    if size_mb > MAX_INPUT_IMAGE_MB:
        raise QweApiError(f"参考图 {size_mb:.1f}MB 超过上限 {MAX_INPUT_IMAGE_MB}MB，请先压缩")
    mime = mimetypes.guess_type(p.name)[0] or "image/png"
    b64 = base64.b64encode(p.read_bytes()).decode()
    return f"data:{mime};base64,{b64}"


def generate_image(
    prompt: str,
    model: str = "gpt-image-2",
    size: str = "1024x1024",
    quality: str = "auto",
    n: int = 1,
    input_image: str = "",
    style: str | None = None,
    background: str | None = None,
    output_format: str | None = None,
) -> GenerationResult:
    """调用 qweapi 生图（支持参考图编辑）。

    input_image: 参考图，本地路径或 http(s) URL。传入后即变成"以参考图为基础编辑"。
    其余参数对齐 OpenAI 官方 images/generations，但 qweapi 仅支持子集（见 UNSUPPORTED_PARAMS）。
    """
    if not prompt.strip():
        raise QweApiError("prompt 不能为空")
    if n < 1 or n > 4:
        raise QweApiError("n 必须在 1~4 之间（qweapi 限制）")
    if size not in SUPPORTED_SIZES:
        raise QweApiError(
            f"size 必须是官方枚举之一 {sorted(SUPPORTED_SIZES)}，实际传入 {size!r}；"
            f"注意 qweapi 实际输出尺寸可能与请求值不同（如 1024x1024 请求返回 1254x1254）"
        )
    if quality not in SUPPORTED_QUALITY:
        raise QweApiError(f"quality 必须是官方枚举之一 {sorted(SUPPORTED_QUALITY)}，实际传入 {quality!r}")

    for param, msg in (("style", style), ("background", background), ("output_format", output_format)):
        if param == "background" and msg in (None, "opaque"):
            continue
        if msg is not None and msg != "auto":
            raise QweApiError(UNSUPPORTED_PARAMS[param])

    payload: dict = {"model": model, "prompt": prompt, "size": size, "quality": quality, "n": n}
    notes: list[str] = []
    if input_image:
        payload["input_image"] = _resolve_input_image(input_image)
        notes.append("已带参考图（input_image）生成")

    r = _post_with_retry("/images/generations", payload)
    _raise_for_status(r, "生图")

    data = r.json().get("data", [])
    if not data:
        raise QweApiError("生图成功但响应中没有 data（服务端格式异常），响应原文：%s" % r.text[:500])

    images: list[bytes] = []
    for item in data:
        b64 = item.get("b64_json")
        if b64:
            images.append(base64.b64decode(b64))
            continue
        url = item.get("url")
        if url:
            with _make_client() as c:
                img = c.get(url)
                if img.status_code != 200:
                    raise QweApiError(f"下载图片 URL 失败 HTTP {img.status_code}: {url}")
                images.append(img.content)
            notes.append(f"图片来自 URL 下载: {url}")
            continue
        raise QweApiError(f"响应项既无 b64_json 也无 url: {item}")

    if not notes:
        notes.append("图片以 PNG 形式返回（qweapi 不支持 output_format，始终为 PNG）")
    return GenerationResult(images=images, notes=notes)


# ---------------------------------------------------------------- 识图（视觉）

def describe_image(
    image_path: str,
    question: str = "请详细描述这张图片的内容、风格和构图。",
    model: str = "",
) -> str:
    """用视觉模型（默认 gpt-5.6-sol）识别图片，返回文本描述。

    给无视觉能力的模型（如 DeepSeek）补充"眼睛"：MCP 内部完成多模态，
    返回给调用方的永远是文本。
    """
    if not question.strip():
        raise QweApiError("question 不能为空")
    p = Path(image_path)
    if not p.is_absolute():
        p = (PROJECT_DIR / p).resolve()
    if not p.exists():
        raise QweApiError(f"图片不存在: {p}")
    mime = mimetypes.guess_type(p.name)[0] or "image/png"
    b64 = base64.b64encode(p.read_bytes()).decode()
    data_url = f"data:{mime};base64,{b64}"

    payload = {
        "model": model or VISION_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": question},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ],
        "max_tokens": 1000,
    }
    r = _post_with_retry("/chat/completions", payload)
    _raise_for_status(r, "识图")
    try:
        content = r.json()["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise QweApiError(f"识图响应格式异常: {r.text[:400]}") from e
    return content.strip()
