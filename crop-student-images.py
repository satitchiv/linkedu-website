#!/usr/bin/env python3
"""
Auto-crop transparent margins from PNG cutouts.
Produces tighter bounding boxes so images display large without empty space.
"""
from PIL import Image
from pathlib import Path

SRC_DIR  = Path(__file__).parent / "images" / "students" / "approved"
CROP_DIR = Path(__file__).parent / "images" / "students" / "cropped"
CROP_DIR.mkdir(parents=True, exist_ok=True)

files = sorted(SRC_DIR.glob("img-*.png"))

for src in files:
    img  = Image.open(src).convert("RGBA")
    bbox = img.getbbox()          # tight bounding box around non-transparent pixels
    if bbox:
        cropped = img.crop(bbox)
        dest = CROP_DIR / src.name
        cropped.save(dest, "PNG")
        w, h = cropped.size
        ratio = f"{w/h:.2f}"
        print(f"  {src.name:45s}  {img.size[0]}x{img.size[1]} → {w}x{h}  ratio {ratio}")
    else:
        print(f"  {src.name} — empty?")

print(f"\nCropped {len(files)} images → {CROP_DIR}")
