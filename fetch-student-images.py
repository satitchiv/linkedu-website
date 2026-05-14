#!/usr/bin/env python3
"""
Pexels → rembg → Telegram approval pipeline
Fetches UK school student images, removes backgrounds, sends to Telegram for approval.
"""

import os
import sys
import time
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path.home() / ".openclaw" / ".env")

PEXELS_KEY = os.getenv("PEXELS_API_KEY")
BOT_TOKEN  = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID    = os.getenv("TELEGRAM_CHAT_ID")

BASE_DIR   = Path(__file__).parent
RAW_DIR    = BASE_DIR / "images" / "students" / "raw"
CUT_DIR    = BASE_DIR / "images" / "students" / "cutout"

RAW_DIR.mkdir(parents=True, exist_ok=True)
CUT_DIR.mkdir(parents=True, exist_ok=True)

SEARCH_TERMS = [
    "british school students uniform",
    "uk boarding school teenagers",
    "english private school children sports",
    "uk school students studying library",
    "british teenagers school uniform outdoor",
]

TARGET_COUNT = 30  # aim for this many raw downloads


def pexels_search(query, per_page=10, page=1):
    headers = {"Authorization": PEXELS_KEY}
    params  = {"query": query, "per_page": per_page, "page": page, "orientation": "portrait"}
    r = requests.get("https://api.pexels.com/v1/search", headers=headers, params=params)
    r.raise_for_status()
    return r.json().get("photos", [])


def download_image(url, dest_path):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    dest_path.write_bytes(r.content)


def remove_background(raw_path, cut_path):
    from rembg import remove
    from PIL import Image
    import io
    data = raw_path.read_bytes()
    result = remove(data)
    img = Image.open(io.BytesIO(result)).convert("RGBA")
    img.save(cut_path, "PNG")


def send_to_telegram(image_path, caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    with open(image_path, "rb") as f:
        r = requests.post(url, data={"chat_id": CHAT_ID, "caption": caption}, files={"photo": f})
    if not r.ok:
        # Try sendDocument for large PNGs
        url2 = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
        with open(image_path, "rb") as f:
            r = requests.post(url2, data={"chat_id": CHAT_ID, "caption": caption}, files={"document": f})
    return r.ok


def main():
    print(f"Pexels key: {'OK' if PEXELS_KEY else 'MISSING'}")
    print(f"Telegram:   {'OK' if BOT_TOKEN and CHAT_ID else 'MISSING'}")
    print()

    # --- Step 1: Collect photo URLs ---
    seen_ids = set()
    photos   = []

    for term in SEARCH_TERMS:
        if len(photos) >= TARGET_COUNT:
            break
        print(f"Searching: {term}")
        results = pexels_search(term, per_page=10)
        for p in results:
            if p["id"] not in seen_ids and len(photos) < TARGET_COUNT:
                seen_ids.add(p["id"])
                photos.append({
                    "id":    p["id"],
                    "url":   p["src"]["large"],      # ~1000px wide
                    "desc":  p.get("alt", term),
                    "term":  term,
                })
        time.sleep(0.3)

    print(f"\nCollected {len(photos)} unique photos.")

    # --- Step 2: Download raw ---
    print("\nDownloading raw images...")
    downloaded = []
    for i, p in enumerate(photos, 1):
        raw_path = RAW_DIR / f"student_{i:02d}_{p['id']}.jpg"
        if raw_path.exists():
            print(f"  [{i:02d}] already exists, skipping download")
        else:
            try:
                download_image(p["url"], raw_path)
                print(f"  [{i:02d}] downloaded — {p['desc'][:50]}")
            except Exception as e:
                print(f"  [{i:02d}] FAILED: {e}")
                continue
        downloaded.append((i, raw_path, p["desc"]))
        time.sleep(0.2)

    # --- Step 3: Remove backgrounds ---
    print(f"\nRemoving backgrounds ({len(downloaded)} images)...")
    cutouts = []
    for i, raw_path, desc in downloaded:
        cut_path = CUT_DIR / f"student_{i:02d}.png"
        if cut_path.exists():
            print(f"  [{i:02d}] cutout already exists")
        else:
            try:
                print(f"  [{i:02d}] removing background...", end=" ", flush=True)
                remove_background(raw_path, cut_path)
                print("done")
            except Exception as e:
                print(f"FAILED: {e}")
                continue
        cutouts.append((i, cut_path, desc))

    # --- Step 4: Send to Telegram ---
    print(f"\nSending {len(cutouts)} cutouts to Telegram...")
    send_to_telegram_text(
        f"LINKEDU Student Images — {len(cutouts)} cutouts ready for approval.\n"
        f"Reply with image numbers to REJECT (e.g. '3 7 12'). All others will be used."
    )

    for i, cut_path, desc in cutouts:
        caption = f"Image {i:02d} — {desc[:80]}"
        ok = send_to_telegram(cut_path, caption)
        status = "sent" if ok else "FAILED"
        print(f"  [{i:02d}] {status}")
        time.sleep(1.0)   # Telegram rate limit

    print("\nAll images sent. Awaiting your approval in Telegram.")
    print("Run apply-approved-images.py after you've reviewed them.")

    # Save index for apply script
    index = [{"num": i, "cutout": str(cut_path), "desc": desc} for i, cut_path, desc in cutouts]
    index_path = BASE_DIR / "images" / "students" / "index.json"
    index_path.write_text(json.dumps(index, indent=2))
    print(f"Index saved: {index_path}")


def send_to_telegram_text(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})


if __name__ == "__main__":
    main()
