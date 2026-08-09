"""直连探测脚本：验证 qweapi 生图接口的行为。

目的：确认 gpt-image-2 的返回格式（同步/异步、base64/URL）、
参数支持范围，据此固化 qweapi_client.py 的逻辑。
"""
import os
import base64
import json
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("QWAPI_BASE_URL", "https://qweapi.com/v1").rstrip("/")
API_KEY = os.getenv("QWAPI_API_KEY", "")
PROXY = os.getenv("QWAPI_PROXY", "") or None

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
ASSETS_DIR.mkdir(exist_ok=True)


def client() -> httpx.Client:
    return httpx.Client(
        base_url=BASE_URL,
        headers={"Authorization": f"Bearer {API_KEY}"},
        proxy=PROXY,
        timeout=180.0,
    )


def probe_models() -> list[str]:
    with client() as c:
        r = c.get("/models")
        r.raise_for_status()
        data = r.json()
        models = [
            m.get("id", "")
            for m in data.get("data", [])
            if "image" in str(m.get("id", "")).lower()
            or "image" in str(m.get("type", "")).lower()
        ]
        print(f"[models] 图像相关模型: {models}")
        return models


def probe_generate() -> dict:
    """用最小成本参数真实生成一张图，返回原始响应结构。"""
    payload = {
        "model": "gpt-image-2",
        "prompt": "a tiny red gem icon, flat pixel art style, simple, centered, isolated on plain background",
        "size": "1024x1024",
        "quality": "low",
        "n": 1,
    }
    print(f"[generate] 请求: {json.dumps(payload, ensure_ascii=False)}")
    with client() as c:
        r = c.post("/images/generations", json=payload)
        print(f"[generate] HTTP {r.status_code}")
        if r.status_code != 200:
            print(f"[generate] 错误响应: {r.text[:1500]}")
            sys.exit(1)
        data = r.json()
        # 打印结构摘要（截断，避免刷屏）
        summary = json.dumps(data, ensure_ascii=False)[:1500]
        print(f"[generate] 响应: {summary}")
        return data


def save_result(data: dict) -> None:
    """尝试从各种返回格式中取出图片并落盘。"""
    item = data.get("data", [{}])[0]
    saved = []
    # 形式 1: b64_json（OpenAI 标准）
    b64 = item.get("b64_json")
    if b64:
        raw = base64.b64decode(b64)
        p = ASSETS_DIR / "probe_b64.png"
        p.write_bytes(raw)
        saved.append(str(p))
    # 形式 2: url（OpenAI 标准）
    url = item.get("url")
    if url:
        with client() as c:
            img = c.get(url)
            p = ASSETS_DIR / "probe_url.png"
            p.write_bytes(img.content)
            saved.append(f"{p} (from url)")
    # 形式 3: 异步任务（常见于中转代理）
    poll_url = data.get("poll_url") or data.get("task_url") or data.get("status_url")
    task_id = data.get("task_id") or data.get("id")
    if poll_url or task_id:
        print("[generate] ⚠ 疑似异步返回: ", poll_url or task_id)
    if saved:
        print(f"[save] 已保存: {saved}")
    else:
        print("[save] ⚠ 未识别到可保存的图片数据，见上方响应结构")


if __name__ == "__main__":
    print("=== 1) 模型列表 ===")
    probe_models()
    print("=== 2) 真实生图探测 ===")
    resp = probe_generate()
    print("=== 3) 保存结果 ===")
    save_result(resp)
