"""OXOXOS OpenAI-compatible API client for image generation and vision."""
from __future__ import annotations

import base64
import mimetypes
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx
from dotenv import dotenv_values, load_dotenv

PROJECT_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_DIR / ".env"


def default_credential_file() -> Path:
    """Return the per-user credential file used by the automated installer."""
    override = os.getenv("OXOXOS_CREDENTIAL_FILE", "").strip()
    if override:
        return Path(override).expanduser()
    if os.name == "nt":
        base = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "OXOXOS" / "oxoxos-cocos-game-assets-mcp.env"


CREDENTIAL_FILE = default_credential_file()
load_dotenv(CREDENTIAL_FILE)
load_dotenv(ENV_FILE)
_user_env = dotenv_values(CREDENTIAL_FILE)
_repo_env = dotenv_values(ENV_FILE)


def _configured(*keys: str, default: str = "") -> str:
    """Read the first non-empty environment or .env value."""
    for key in keys:
        value = os.getenv(key)
        if value is not None and value.strip():
            return value.strip()
    for values in (_user_env, _repo_env):
        for key in keys:
            value = values.get(key, "")
            if value and value.strip():
                return value.strip()
    return default


BASE_URL = _configured(
    "OXOXOS_BASE_URL",
    default="https://api.oxoxos.com/v1",
).rstrip("/")
API_KEY = _configured("OXOXOS_API_KEY", "QWAPI_API_KEY")
PROXY = _configured("OXOXOS_PROXY", "QWAPI_PROXY")
IMAGE_MODEL = _configured("OXOXOS_IMAGE_MODEL", "QWAPI_IMAGE_MODEL")
VISION_MODEL = _configured("OXOXOS_VISION_MODEL", "QWAPI_VISION_MODEL")

SUPPORTED_QUALITY = {"low", "medium", "high", "auto"}
SUPPORTED_SIZES = {"1024x1024", "1536x1024", "1024x1536", "auto"}
MAX_INPUT_IMAGE_MB = 8
_RETRIES = 3
_RETRY_BACKOFF = (1.0, 2.0)
_MODEL_CACHE: list[dict[str, Any]] | None = None


class OxoxosApiError(RuntimeError):
    """A safe, user-facing OXOXOS API error."""


@dataclass
class GenerationResult:
    images: list[bytes]
    notes: list[str] = field(default_factory=list)


def _make_client() -> httpx.Client:
    if not API_KEY:
        raise OxoxosApiError(
            "未配置 OXOXOS_API_KEY。请前往 https://api.oxoxos.com/console/token 创建令牌，"
            "再通过客户端安全配置或插件设置添加；不要把令牌提交到 Git。"
        )
    return httpx.Client(
        base_url=BASE_URL,
        headers={"Authorization": f"Bearer {API_KEY}"},
        proxy=PROXY or None,
        timeout=180.0,
    )


def _post_with_retry(path: str, payload: dict[str, Any]) -> httpx.Response:
    last_exc: Exception | None = None
    for attempt in range(_RETRIES):
        try:
            with _make_client() as client:
                return client.post(path, json=payload)
        except (httpx.RemoteProtocolError, httpx.ConnectError, httpx.ReadError) as exc:
            last_exc = exc
            if attempt < _RETRIES - 1:
                time.sleep(_RETRY_BACKOFF[attempt])
    proxy_state = "已配置代理" if PROXY else "直连"
    raise OxoxosApiError(
        f"连接 OXOXOS API 失败（已重试 {_RETRIES} 次，{proxy_state}）：{last_exc}"
    )


def _raise_for_status(response: httpx.Response, action: str) -> None:
    if response.status_code == 200:
        return
    try:
        body = response.json()
    except ValueError:
        message = response.text[:500]
    else:
        if isinstance(body, dict):
            error = body.get("error", {})
            message = error.get("message", error) if isinstance(error, dict) else error
        else:
            message = str(body)[:500]
    raise OxoxosApiError(f"{action}失败 HTTP {response.status_code}: {message}")


def _infer_capabilities(model: dict[str, Any]) -> list[str]:
    """Infer broad capabilities without treating changing marketplace ids as a contract."""
    text = " ".join(
        str(model.get(key, ""))
        for key in ("id", "type", "object", "owned_by", "capabilities", "description")
    ).lower()
    capabilities: set[str] = set()
    if any(token in text for token in ("image", "flux", "dall", "stable-diffusion", "wan")):
        capabilities.add("image_generation")
    if any(token in text for token in ("vision", "multimodal", "vl", "image-understanding")):
        capabilities.add("vision")
    if any(token in text for token in ("chat", "gpt", "gemini", "claude", "qwen", "deepseek")):
        capabilities.add("chat")
    if "chat" in capabilities and "image_generation" not in capabilities and "vision" not in capabilities:
        capabilities.add("vision_candidate")
    return sorted(capabilities)


def list_models(force_refresh: bool = False) -> list[dict[str, Any]]:
    """Return current marketplace models with inferred capability hints."""
    global _MODEL_CACHE
    if _MODEL_CACHE is not None and not force_refresh:
        return [dict(model) for model in _MODEL_CACHE]
    try:
        with _make_client() as client:
            response = client.get("models")
    except (httpx.RemoteProtocolError, httpx.ConnectError, httpx.ReadError) as exc:
        raise OxoxosApiError(f"获取模型列表失败（网络错误）：{exc}") from exc
    _raise_for_status(response, "获取模型列表")
    raw_models = response.json().get("data", [])
    models: list[dict[str, Any]] = []
    for raw in raw_models:
        if not isinstance(raw, dict) or not raw.get("id"):
            continue
        models.append(
            {
                "id": str(raw["id"]),
                "type": str(raw.get("type", raw.get("object", ""))),
                "capabilities": _infer_capabilities(raw),
            }
        )
    _MODEL_CACHE = models
    return [dict(model) for model in models]


def _select_model(kind: str, explicit: str = "") -> str:
    if explicit.strip():
        return explicit.strip()
    configured = IMAGE_MODEL if kind == "image_generation" else VISION_MODEL
    if configured:
        return configured
    models = list_models()
    candidates = [model["id"] for model in models if kind in model["capabilities"]]
    if kind == "vision" and not candidates:
        candidates = [model["id"] for model in models if "vision_candidate" in model["capabilities"]]
    if candidates:
        return candidates[0]
    raise OxoxosApiError(
        f"无法从当前模型广场自动判断可用的{('生图' if kind == 'image_generation' else '视觉')}模型。"
        "请先调用 list_models 查看实时列表，再显式传入 model；也可配置 "
        f"{'OXOXOS_IMAGE_MODEL' if kind == 'image_generation' else 'OXOXOS_VISION_MODEL'}。"
    )


def _resolve_input_image(input_image: str) -> str:
    value = input_image.strip()
    if not value:
        raise OxoxosApiError("input_image 为空")
    if value.startswith(("http://", "https://")):
        return value
    path = Path(value)
    if not path.is_absolute():
        path = (PROJECT_DIR / path).resolve()
    if not path.exists() or not path.is_file():
        raise OxoxosApiError(f"参考图不存在: {path}")
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > MAX_INPUT_IMAGE_MB:
        raise OxoxosApiError(
            f"参考图 {size_mb:.1f}MB 超过上限 {MAX_INPUT_IMAGE_MB}MB，请先压缩"
        )
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode()
    return f"data:{mime};base64,{encoded}"


def generate_image(
    prompt: str,
    model: str = "",
    size: str = "1024x1024",
    quality: str = "auto",
    n: int = 1,
    input_image: str = "",
) -> GenerationResult:
    if not prompt.strip():
        raise OxoxosApiError("prompt 不能为空")
    if not 1 <= n <= 4:
        raise OxoxosApiError("n 必须在 1~4 之间")
    if size not in SUPPORTED_SIZES:
        raise OxoxosApiError(f"size 必须是 {sorted(SUPPORTED_SIZES)} 之一，实际传入 {size!r}")
    if quality not in SUPPORTED_QUALITY:
        raise OxoxosApiError(
            f"quality 必须是 {sorted(SUPPORTED_QUALITY)} 之一，实际传入 {quality!r}"
        )

    selected_model = _select_model("image_generation", model)
    payload: dict[str, Any] = {
        "model": selected_model,
        "prompt": prompt,
        "size": size,
        "quality": quality,
        "n": n,
    }
    notes = [f"使用模型: {selected_model}"]
    if input_image:
        payload["input_image"] = _resolve_input_image(input_image)
        notes.append("已带参考图（input_image）生成")

    response = _post_with_retry("images/generations", payload)
    _raise_for_status(response, "生图")
    data = response.json().get("data", [])
    if not data:
        raise OxoxosApiError("生图成功但响应中没有 data")

    images: list[bytes] = []
    for item in data:
        encoded = item.get("b64_json")
        if encoded:
            try:
                images.append(base64.b64decode(encoded, validate=True))
            except ValueError as exc:
                raise OxoxosApiError("生图响应包含无效的 base64 图片数据") from exc
            continue
        url = item.get("url")
        if url:
            with _make_client() as client:
                image_response = client.get(url)
            if image_response.status_code != 200:
                raise OxoxosApiError(f"下载生成图片失败 HTTP {image_response.status_code}")
            images.append(image_response.content)
            notes.append("图片由服务端 URL 下载")
            continue
        raise OxoxosApiError("生图响应项既无 b64_json 也无 url")
    return GenerationResult(images=images, notes=notes)


def describe_image(
    image_path: str,
    question: str = "请详细描述这张图片的内容、风格和构图。",
    model: str = "",
) -> str:
    if not question.strip():
        raise OxoxosApiError("question 不能为空")
    path = Path(image_path)
    if not path.is_absolute():
        path = (PROJECT_DIR / path).resolve()
    if not path.exists() or not path.is_file():
        raise OxoxosApiError(f"图片不存在: {path}")
    if path.stat().st_size > MAX_INPUT_IMAGE_MB * 1024 * 1024:
        raise OxoxosApiError(f"图片超过 {MAX_INPUT_IMAGE_MB}MB，请先压缩")

    selected_model = _select_model("vision", model)
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode()
    payload = {
        "model": selected_model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": question},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{encoded}"},
                    },
                ],
            }
        ],
        "max_tokens": 1000,
    }
    response = _post_with_retry("chat/completions", payload)
    _raise_for_status(response, "识图")
    try:
        content = response.json()["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise OxoxosApiError("识图响应格式异常") from exc
    if not isinstance(content, str) or not content.strip():
        raise OxoxosApiError("识图响应没有文本内容")
    return content.strip()
