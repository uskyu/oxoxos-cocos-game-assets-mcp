"""端到端验证脚本：通过 stdio 拉起真实 MCP 服务器，跑完整链路。

链路：list_tools → list_models → generate_image(同步/异步/参考图)
      → describe_image(视觉识图) → check_task
      → get_image_info → resize_image → slice_sprite_sheet
      → crop_image → convert_image → 读资源 assets://list
"""
import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PROJECT = r"D:/VSAI/MCP/image-gen-mcp"
ASSETS = os.path.join(PROJECT, "assets")


def show(tag: str, text: str) -> None:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        print(f"--- {tag}: {text[:300]}")
        return
    if data.get("ok") is False:
        print(f"--- {tag}: ❌ {data.get('error', '未知错误')}")
        return
    print(f"--- {tag}: ✅ {json.dumps(data, ensure_ascii=False)[:400]}")


def ensure(session_result, tag: str) -> dict:
    """解包工具返回并断言 ok。"""
    d = json.loads(session_result.content[0].text)
    assert d.get("ok") is True, f"{tag} 失败: {d.get('error')}"
    return d


async def main() -> None:
    params = StdioServerParameters(
        command="uv",
        args=["run", "python", "mcp/server.py"],
        cwd=PROJECT,
        read_timeout_seconds=300,
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("== MCP 连接初始化成功 ==")

            tools = await session.list_tools()
            print(f"== 工具清单（{len(tools.tools)} 个）==")
            for t in tools.tools:
                print("   -", t.name)
            resources = await session.list_resources()
            print("== 资源 ==")
            for r in resources.resources:
                print("   -", r.uri)

            # 1. 模型列表
            r = await session.call_tool("list_models", {})
            show("list_models", r.content[0].text)

            # 2. 真实生图（消耗 1 次额度；若已有 e2e_tree.png 则复用）
            existing = os.path.join(ASSETS, "e2e_tree.png")
            if os.path.exists(existing):
                print("--- generate_image: ⏭ 复用已有素材 " + existing)
                tree = existing
            else:
                r = await session.call_tool(
                    "generate_image",
                    {
                        "prompt": "a cartoon tree sprite for a game, green canopy, brown trunk, flat color style, centered",
                        "quality": "low",
                        "filename_prefix": "e2e_tree",
                    },
                )
                show("generate_image", r.content[0].text)
                tree = ensure(r, "generate_image")["images"][0]

            # 3. 视觉识图（给无视觉模型补眼睛）
            r = await session.call_tool(
                "describe_image",
                {"image_path": tree, "question": "Describe this image in one short sentence."},
            )
            show("describe_image", r.content[0].text)

            # 4. 参考图编辑（消耗 1 次额度；已有产物则复用）
            ref_path = os.path.join(ASSETS, "e2e_tree_pink.png")
            if os.path.exists(ref_path):
                print("--- 参考图生图: ⏭ 复用已有产物 " + ref_path)
            else:
                r = await session.call_tool(
                    "generate_image",
                    {
                        "prompt": "Recolor this tree: pink leaves, purple trunk, keep composition identical",
                        "input_image": tree,
                        "quality": "low",
                        "filename_prefix": "e2e_tree_pink",
                    },
                )
                show("generate_image+input_image", r.content[0].text)
                pink = ensure(r, "参考图生图")["images"][0]
                assert os.path.exists(pink), "参考图产物不存在!"
                print(f"--- 参考图生图落盘验证: ✅ {pink}")

            # 5. 异步任务：wait=false → check_task 轮询
            r = await session.call_tool(
                "generate_image",
                {
                    "prompt": "a small coin icon, gold circle, game style, centered",
                    "quality": "low",
                    "wait": False,
                    "filename_prefix": "e2e_coin",
                },
            )
            show("generate_image(wait=false)", r.content[0].text)
            task_id = ensure(r, "异步提交")["task_id"]
            done = False
            for _ in range(60):  # 最多等 5 分钟
                await asyncio.sleep(5)
                r = await session.call_tool("check_task", {"task_id": task_id})
                d = json.loads(r.content[0].text)
                if d.get("status") == "done":
                    show("check_task(异步完成)", r.content[0].text)
                    assert os.path.exists(d["images"][0]), "异步产物不存在!"
                    done = True
                    break
                if d.get("status") == "error":
                    show("check_task(异步失败)", r.content[0].text)
                    break
            assert done, "异步任务 5 分钟内未完成!"

            # 6. 图片信息
            r = await session.call_tool("get_image_info", {"image_path": tree})
            show("get_image_info", r.content[0].text)
            info = ensure(r, "get_image_info")
            w, h = info["width"], info["height"]

            # 7. 缩放到 900x900（cover），便于均匀切帧
            r = await session.call_tool(
                "resize_image", {"image_path": tree, "width": 900, "height": 900, "mode": "cover"}
            )
            show("resize_image", r.content[0].text)
            resized = ensure(r, "resize_image")["output_path"]

            # 8. 精灵图切帧 3x3（900/3=300 整除）
            r = await session.call_tool(
                "slice_sprite_sheet", {"image_path": resized, "cols": 3, "rows": 3}
            )
            show("slice_sprite_sheet", r.content[0].text)

            # 9. 裁剪中心 400x400 区域
            cx, cy = w // 2, h // 2
            r = await session.call_tool(
                "crop_image",
                {"image_path": tree, "box": [cx - 200, cy - 200, cx + 200, cy + 200]},
            )
            show("crop_image", r.content[0].text)

            # 10. 转 webp
            r = await session.call_tool(
                "convert_image", {"image_path": resized, "output_format": "webp"}
            )
            show("convert_image", r.content[0].text)

            # 11. 读资源
            r = await session.read_resource("assets://list")
            content = r.contents[0].text if hasattr(r.contents[0], "text") else str(r.contents[0])
            print("--- assets://list ✅")
            print(content[:600])

            print("\n===== 全部链路通过 ✅ =====")


if __name__ == "__main__":
    asyncio.run(main())
