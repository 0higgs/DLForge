from __future__ import annotations

import struct
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
CANVAS = 1024
BLUE = (36, 112, 255)
CYAN = (0, 198, 255)


def build_icon() -> Image.Image:
    mask = Image.new("L", (CANVAS, CANVAS), 0)
    mask_draw = ImageDraw.Draw(mask)
    inset = 72
    mask_draw.rounded_rectangle(
        (inset, inset, CANVAS - inset, CANVAS - inset),
        radius=260,
        fill=255,
    )
    # Shift the counter to the right so the mark reads as a geometric "D"
    # even at 16 px, while retaining the compact rounded-frame silhouette.
    mask_draw.rectangle((344, 286, 570, 738), fill=0)
    mask_draw.ellipse((344, 286, 794, 738), fill=0)

    gradient = Image.new("RGBA", (CANVAS, CANVAS))
    pixels = gradient.load()
    for y in range(CANVAS):
        for x in range(CANVAS):
            blend = min(1.0, max(0.0, (x + y) / (2 * (CANVAS - 1))))
            color = tuple(
                round(CYAN[channel] * (1 - blend) + BLUE[channel] * blend)
                for channel in range(3)
            )
            pixels[x, y] = (*color, 255)

    icon = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    icon.paste(gradient, (0, 0), mask)
    return icon


def _dib_frame(icon: Image.Image, size: int) -> bytes:
    resized = icon.resize((size, size), Image.Resampling.LANCZOS)
    rgba = resized.load()
    pixels = bytearray()
    for y in range(size - 1, -1, -1):
        for x in range(size):
            red, green, blue, alpha = rgba[x, y]
            pixels.extend((blue, green, red, alpha))
    mask_stride = ((size + 31) // 32) * 4
    and_mask = bytes(mask_stride * size)
    header = struct.pack(
        "<IIIHHIIIIII",
        40,
        size,
        size * 2,
        1,
        32,
        0,
        len(pixels),
        0,
        0,
        0,
        0,
    )
    return header + pixels + and_mask


def write_windows_ico(icon: Image.Image, path: Path) -> None:
    sizes = (16, 32, 48, 64, 256)
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
    print(f"Wrote {ico_path}")


if __name__ == "__main__":
    main()
