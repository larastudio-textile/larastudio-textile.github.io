#!/usr/bin/env python3
"""Produce VK-safe, uncropped square pictures and a separate import feed.

Only reads original product photographs; never changes the originals.
Run from the GitHub Pages repository root:
    python -m pip install Pillow
    python scripts/build_vk_square_feed.py
"""
from __future__ import annotations

import re
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
FEED_SOURCE = ROOT / "feeds/vk-new-8-2026-11-03.yml"
FEED_DEST = ROOT / "feeds/vk-new-8-square.yml"
IMAGE_PREFIX = "https://larastudio-textile.github.io/images/"
IMAGE_DEST = ROOT / "images/vk-square"
SIDE = 1200
MARGIN = 36
BACKGROUND = "#F6F3EE"


def square_copy(source: Path, target: Path) -> tuple[int, int]:
    with Image.open(source) as image:
        image = ImageOps.exif_transpose(image)
        original_size = image.size
        if image.mode != "RGB":
            # Retain original transparent areas against the same warm ivory ground.
            if "A" in image.getbands():
                transparent = image.convert("RGBA")
                ground = Image.new("RGBA", image.size, BACKGROUND)
                image = Image.alpha_composite(ground, transparent).convert("RGB")
            else:
                image = image.convert("RGB")

        box_side = SIDE - 2 * MARGIN
        image.thumbnail((box_side, box_side), Image.Resampling.LANCZOS)
        result = Image.new("RGB", (SIDE, SIDE), BACKGROUND)
        result.paste(image, ((SIDE - image.width) // 2, (SIDE - image.height) // 2))
        target.parent.mkdir(parents=True, exist_ok=True)
        result.save(target, "JPEG", quality=91, optimize=True, subsampling=0)
        return original_size


def main() -> None:
    yml = FEED_SOURCE.read_text(encoding="utf-8")
    urls = re.findall(r"<picture>(" + re.escape(IMAGE_PREFIX) + r"[^<]+)</picture>", yml)
    if len(urls) != 38:
        raise ValueError(f"Expected 38 photograph references, found {len(urls)}")
    found = set()
    ratios = []
    for url in urls:
        if url in found:
            continue
        found.add(url)
        relative = url.removeprefix(IMAGE_PREFIX)
        original = ROOT / "images" / relative
        if not original.is_file():
            raise FileNotFoundError(original)
        target = IMAGE_DEST / Path(relative).with_suffix(".jpg")
        w, h = square_copy(original, target)
        ratios.append((relative, w, h))
        yml = yml.replace(
            f"<picture>{url}</picture>",
            f"<picture>{IMAGE_PREFIX}vk-square/{Path(relative).with_suffix('.jpg').as_posix()}</picture>",
        )
    if re.search(r"<picture>" + re.escape(IMAGE_PREFIX) + r"(?!vk-square/)", yml):
        raise AssertionError("Original image reference remains in revised feed")
    if yml.count("<offer id=") != 8 or yml.count("<picture>") != 38:
        raise AssertionError("Expected 8 products and 38 photos")
    FEED_DEST.write_text(yml, encoding="utf-8")
    print(f"Created {len(ratios)} uncropped 1200x1200 JPEG photos and {FEED_DEST}")
    for path, w, h in ratios:
        print(f"  {path}: {w}x{h} -> 1200x1200")


if __name__ == "__main__":
    main()
