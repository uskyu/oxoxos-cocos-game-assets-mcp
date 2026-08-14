"""本地图片后处理（Pillow）：裁剪 / 缩放 / 格式转换 / 精灵图切帧 / 信息查询。

全部本地执行，零 API 成本。函数抛 ValueError/FileNotFoundError 时，
MCP 层会把错误信息原样返回给 AI，便于它调整参数。
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

SUPPORTED_OUTPUT_FORMATS = {"png", "jpeg", "webp", "bmp", "gif"}


def _open_image(path: str | Path) -> Image.Image:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"图片不存在: {p}")
    try:
        return Image.open(p)
    except Exception as e:
        raise ValueError(f"无法打开图片（不是有效的图片文件）: {p} —— {e}") from e


def _resolve_output_path(source: Path, name_suffix: str, output_path: str | None) -> Path:
    """output_path 为空时，在源图同目录自动命名（源名+suffix+源扩展名），避免覆盖原图。"""
    if output_path:
        p = Path(output_path)
        if not p.is_absolute():
            p = source.parent / p
        p.parent.mkdir(parents=True, exist_ok=True)
        return p
    stem, ext = source.stem, source.suffix
    p = source.with_name(f"{stem}{name_suffix}{ext}")
    i = 1
    while p.exists():
        p = source.with_name(f"{stem}{name_suffix}_{i}{ext}")
        i += 1
    return p


def get_image_info(image_path: str) -> dict:
    """返回图片的基本信息：格式、尺寸、颜色模式、文件大小。"""
    p = Path(image_path)
    img = _open_image(p)
    return {
        "path": str(p.resolve()),
        "format": (img.format or "").lower(),
        "width": img.width,
        "height": img.height,
        "mode": img.mode,
        "has_alpha": img.mode in ("RGBA", "LA", "P"),
        "file_size_bytes": p.stat().st_size,
    }


def crop_image(image_path: str, box: list[int], output_path: str | None = None) -> str:
    """按 box=[left, top, right, bottom] 裁剪，返回新文件绝对路径。"""
    if len(box) != 4:
        raise ValueError(f"box 必须是 4 个整数 [left, top, right, bottom]，实际 {box}")
    left, top, right, bottom = box
    src = Path(image_path)
    img = _open_image(src)
    if not (0 <= left < right <= img.width and 0 <= top < bottom <= img.height):
        raise ValueError(
            f"裁剪区域超出图片范围: 图片 {img.width}x{img.height}，box {box}"
        )
    cropped = img.crop((left, top, right, bottom))
    out = _resolve_output_path(src, f"_crop_{left}_{top}_{right}_{bottom}", output_path)
    cropped.save(out)
    return str(out.resolve())


def resize_image(
    image_path: str,
    width: int,
    height: int,
    mode: str = "stretch",
    output_path: str | None = None,
) -> str:
    """缩放到指定尺寸。

    mode:
      - stretch: 拉伸到 width×height（可能变形）
      - contain: 完整放入 width×height 画布，居中，透明图补透明、否则补黑
      - cover:   缩放填满 width×height 并居中裁剪（不变形，可能裁掉边缘）
    """
    if width <= 0 or height <= 0:
        raise ValueError(f"width/height 必须为正整数，实际 {width}x{height}")
    if mode not in ("stretch", "contain", "cover"):
        raise ValueError(f"mode 必须是 stretch/contain/cover 之一，实际 {mode!r}")

    src = Path(image_path)
    img = _open_image(src)

    if mode == "stretch":
        out_img = img.resize((width, height), Image.LANCZOS)
    else:
        scale = min(width / img.width, height / img.height) if mode == "contain" else max(
            width / img.width, height / img.height
        )
        new_w, new_h = max(1, round(img.width * scale)), max(1, round(img.height * scale))
        resized = img.resize((new_w, new_h), Image.LANCZOS)
        if mode == "cover":
            # 居中裁剪到目标尺寸
            left = (new_w - width) // 2
            top = (new_h - height) // 2
            out_img = resized.crop((left, top, left + width, top + height))
        else:  # contain：居中放在目标画布上
            has_alpha = img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info)
            canvas = Image.new("RGBA" if has_alpha else "RGB", (width, height), (0, 0, 0, 0) if has_alpha else (0, 0, 0))
            canvas.paste(resized, ((width - new_w) // 2, (height - new_h) // 2), resized if has_alpha else None)
            out_img = canvas

    out = _resolve_output_path(src, f"_{width}x{height}_{mode}", output_path)
    out_img.save(out)
    return str(out.resolve())


def convert_image(
    image_path: str,
    output_format: str = "png",
    background: str | None = None,
    output_path: str | None = None,
) -> str:
    """格式转换；transparent 背景（RGBA）转 jpeg 时必须提供 background 颜色。

    background: 如 "white" / "#ff0000" / "255,0,0"，仅对带透明通道且目标格式不支持透明时生效。
    """
    fmt = output_format.lower()
    if fmt not in SUPPORTED_OUTPUT_FORMATS:
        raise ValueError(f"output_format 必须是 {sorted(SUPPORTED_OUTPUT_FORMATS)} 之一，实际 {fmt!r}")

    src = Path(image_path)
    img = _open_image(src)
    has_alpha = img_has_alpha(img)

    if fmt == "jpeg" and has_alpha:
        if background is None:
            raise ValueError("透明图转 JPEG 需要提供 background 颜色（如 'white'），否则无法合并背景")
        img = img.convert("RGBA")
        bg = Image.new("RGBA", img.size, _parse_color(background))
        bg.alpha_composite(img)
        img = bg.convert("RGB")
    elif has_alpha:
        img = img.convert("RGBA")  # png/webp/gif 保留透明通道
    elif img.mode != "RGB" and fmt in ("jpeg", "bmp"):
        img = img.convert("RGB")

    if output_path:
        out = _resolve_output_path(src, f".{fmt}", output_path)
    else:
        out = src.with_suffix(f".{fmt}")
        if out == src:  # 同格式转换（如 png->png）：改名避免覆盖源图
            out = src.with_name(f"{src.stem}_converted.{fmt}")
    kwargs = {"quality": 92} if fmt in ("jpeg", "webp") else {}
    img.save(out, format=fmt.upper(), **kwargs)
    return str(out.resolve())


def img_has_alpha(img: Image.Image) -> bool:
    return img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info)


def _parse_color(color: str) -> tuple[int, int, int, int]:
    c = color.strip().lower()
    named = {"white": (255, 255, 255), "black": (0, 0, 0), "transparent": (0, 0, 0, 0)}
    if c in named:
        return named[c]
    if c.startswith("#") and len(c) == 7:
        return tuple(int(c[i : i + 2], 16) for i in (1, 3, 5)) + (255,)
    if "," in c:
        parts = [int(x) for x in c.split(",")]
        if len(parts) == 3:
            return tuple(parts) + (255,)
        if len(parts) == 4:
            return tuple(parts)
    raise ValueError(f"无法解析颜色 {color!r}，支持 'white'/'black'/hex '#rrggbb'/rgb 'r,g,b'/'r,g,b,a'")


def slice_sprite_sheet(
    image_path: str,
    cols: int,
    rows: int,
    output_dir: str | None = None,
) -> list[str]:
    """把精灵图（sprite sheet）按 cols×rows 均匀切成单帧，输出 PNG 列表。

    图片尺寸必须能被 cols/rows 整除；不能整除时先 resize 再切。
    """
    if cols <= 0 or rows <= 0:
        raise ValueError(f"cols/rows 必须为正整数，实际 {cols}x{rows}")
    src = Path(image_path)
    img = _open_image(src)
    fw, fh = img.width // cols, img.height // rows
    if fw * cols != img.width or fh * rows != img.height:
        raise ValueError(
            f"图片 {img.width}x{img.height} 不能被 {cols}x{rows} 整除，"
            f"请先用 resize_image 调整到合适尺寸（如 {cols * fw}x{rows * fh}）"
        )
    out_dir = Path(output_dir) if output_dir else src.parent / f"{src.stem}_sheet"
    out_dir.mkdir(parents=True, exist_ok=True)
    saved: list[str] = []
    for r in range(rows):
        for c in range(cols):
            frame = img.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh))
            p = out_dir / f"{src.stem}_r{r}c{c}.png"
            frame.save(p)
            saved.append(str(p.resolve()))
    return saved
