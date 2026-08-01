from __future__ import annotations

import struct
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
MASTER = ASSETS / "dlforge-icon-master.png"
CANVAS = 1024
ICO_SIZES = (16, 20, 24, 32, 40, 48, 64, 128, 256)


def _linear_gradient(size: int) -> Image.Image:
    """Create a navy panel that matches DLForge's dark application shell."""
    top = (13, 22, 39, 255)
    bottom = (7, 12, 25, 255)
    image = Image.new("RGBA", (size, size))
    pixels = image.load()
    for y in range(size):
        blend = y / max(1, size - 1)
        color = tuple(round(top[i] * (1 - blend) + bottom[i] * blend) for i in range(4))
        for x in range(size):
            pixels[x, y] = color
    return image


def build_icon() -> Image.Image:
    if not MASTER.exists():
        raise FileNotFoundError(f"Missing icon master: {MASTER}")

    icon = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    panel_mask = Image.new("L", icon.size, 0)
    mask_draw = ImageDraw.Draw(panel_mask)
    mask_draw.rounded_rectangle((42, 42, 982, 982), radius=224, fill=255)
    icon.paste(_linear_gradient(CANVAS), (0, 0), panel_mask)

    # A restrained violet-to-cyan rim keeps the mark distinct on both light and
    # dark desktops without adding visual noise at taskbar sizes.
    rim = Image.new("RGBA", icon.size, (0, 0, 0, 0))
    rim_draw = ImageDraw.Draw(rim)
    rim_draw.rounded_rectangle((43, 43, 981, 981), radius=223, outline=(124, 92, 255, 210), width=15)
    rim_draw.arc((52, 52, 972, 972), 190, 350, fill=(34, 211, 197, 190), width=8)
    icon.alpha_composite(rim)

    mark = Image.open(MASTER).convert("RGBA")
    bbox = mark.getbbox()
    if bbox is None:
        raise ValueError("Icon master is fully transparent")
    mark = mark.crop(bbox)
    mark.thumbnail((858, 858), Image.Resampling.LANCZOS)
    # Raise the anvil slightly so the composition remains optically centered.
    position = ((CANVAS - mark.width) // 2, (CANVAS - mark.height) // 2 - 8)
    icon.alpha_composite(mark, position)
    return icon


def _render_size(icon: Image.Image, size: int) -> Image.Image:
    rendered = icon.resize((size, size), Image.Resampling.LANCZOS)
    if size <= 32:
        rendered = ImageEnhance.Contrast(rendered).enhance(1.12)
        rendered = rendered.filter(ImageFilter.UnsharpMask(radius=0.55, percent=145, threshold=2))
    elif size <= 64:
        rendered = rendered.filter(ImageFilter.UnsharpMask(radius=0.7, percent=115, threshold=2))
    return rendered


def _dib_frame(icon: Image.Image, size: int) -> bytes:
    resized = _render_size(icon, size)
    rgba = resized.load()
    pixels = bytearray()
    for y in range(size - 1, -1, -1):
        for x in range(size):
            red, green, blue, alpha = rgba[x, y]
            pixels.extend((blue, green, red, alpha))
    mask_stride = ((size + 31) // 32) * 4
    and_mask = bytes(mask_stride * size)
    header = struct.pack(
        "<IIIHHIIIIII", 40, size, size * 2, 1, 32, 0,
        len(pixels), 0, 0, 0, 0,
    )
    return header + pixels + and_mask


def write_windows_ico(icon: Image.Image, path: Path, sizes: tuple[int, ...] = ICO_SIZES) -> None:
    frames = [_dib_frame(icon, size) for size in sizes]
    offset = 6 + 16 * len(frames)
    directory = bytearray(struct.pack("<HHH", 0, 1, len(frames)))
    for size, frame in zip(sizes, frames):
        encoded_size = 0 if size == 256 else size
        directory.extend(
            struct.pack("<BBBBHHII", encoded_size, encoded_size, 0, 0, 1, 32, len(frame), offset)
        )
        offset += len(frame)
    path.write_bytes(bytes(directory) + b"".join(frames))


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    icon = build_icon()
    png_path = ASSETS / "dlforge-icon.png"
    ico_path = ASSETS / "dlforge.ico"
    icon.save(png_path, optimize=True)
    write_windows_ico(icon, ico_path)
    print(f"Wrote {png_path}")
    print(f"Wrote {ico_path} with {len(ICO_SIZES)} sizes")


if __name__ == "__main__":
    main()
