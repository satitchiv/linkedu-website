#!/usr/bin/env python3
"""
Apply approved student cutout images to the LINKEDU website.
Run this after you've reviewed the Telegram images and decided which to keep.

Usage:
  python3 apply-approved-images.py --reject 3 7 12 20
  (Leave out --reject to use all images)
"""

import os
import sys
import json
import shutil
import argparse
from pathlib import Path

BASE_DIR  = Path(__file__).parent
INDEX_PATH = BASE_DIR / "images" / "students" / "index.json"
CUT_DIR   = BASE_DIR / "images" / "students" / "cutout"
SITE_IMG  = BASE_DIR / "images" / "students" / "approved"

# 18 placement spots mapped across the site
# Format: (page_file, css_selector_hint, slot_description)
PLACEMENTS = [
    # index.html
    ("index.html",           "hero-student-1",       "Hero section — student left"),
    ("index.html",           "hero-student-2",       "Hero section — student right"),
    ("index.html",           "testimonial-photo-1",  "Testimonial card 1"),
    ("index.html",           "testimonial-photo-2",  "Testimonial card 2"),
    ("index.html",           "testimonial-photo-3",  "Testimonial card 3"),
    # about.html
    ("about.html",           "team-student-1",       "About — student photo 1"),
    ("about.html",           "team-student-2",       "About — student photo 2"),
    # schools.html
    ("schools.html",         "schools-hero-student", "Schools listing — hero student"),
    # summer-camps.html
    ("summer-camps.html",    "camps-hero-student",   "Summer camps — hero student"),
    ("summer-camps.html",    "camps-activity-1",     "Summer camps — activity 1"),
    ("summer-camps.html",    "camps-activity-2",     "Summer camps — activity 2"),
    # find-your-school.html
    ("find-your-school.html","quiz-hero-student",    "Quiz page — hero student"),
    # tools/sports-pathway.html
    ("tools/sports-pathway.html", "sports-student-1", "Sports pathway — student 1"),
    ("tools/sports-pathway.html", "sports-student-2", "Sports pathway — student 2"),
    # guides.html
    ("guides.html",          "guides-hero-student",  "Guides — hero student"),
    # contact.html
    ("contact.html",         "contact-student",      "Contact — decorative student"),
    # pricing.html
    ("pricing.html",         "pricing-student",      "Pricing — decorative student"),
    # fees.html
    ("fees.html",            "fees-student",         "Fees — decorative student"),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reject", nargs="*", type=int, default=[], help="Image numbers to reject")
    args = parser.parse_args()

    rejected = set(args.reject)
    print(f"Rejected image numbers: {sorted(rejected) if rejected else 'none'}")

    # Load index
    if not INDEX_PATH.exists():
        print("ERROR: index.json not found. Run fetch-student-images.py first.")
        sys.exit(1)

    index = json.loads(INDEX_PATH.read_text())
    approved = [item for item in index if item["num"] not in rejected]

    print(f"\nApproved: {len(approved)} images (from {len(index)} total)")
    print(f"Placement spots: {len(PLACEMENTS)}")

    if len(approved) < len(PLACEMENTS):
        print(f"WARNING: only {len(approved)} approved but {len(PLACEMENTS)} spots. Some spots will be empty.")

    # Copy approved images to /approved/ folder with clean names
    SITE_IMG.mkdir(parents=True, exist_ok=True)

    # Remove rejected files
    for item in index:
        if item["num"] in rejected:
            cut_path = Path(item["cutout"])
            if cut_path.exists():
                cut_path.unlink()
                print(f"  Deleted rejected: {cut_path.name}")

    # Assign approved images to placements
    assignments = []
    for i, (page, slot_id, description) in enumerate(PLACEMENTS):
        if i >= len(approved):
            break
        item = approved[i]
        src  = Path(item["cutout"])
        dest_name = f"student-{slot_id}.png"
        dest = SITE_IMG / dest_name
        if src.exists():
            shutil.copy2(src, dest)
            assignments.append({
                "page":        page,
                "slot":        slot_id,
                "description": description,
                "file":        f"images/students/approved/{dest_name}",
                "source_desc": item["desc"],
            })
            print(f"  [{i+1:02d}] {dest_name} → {description}")

    # Save assignment map
    map_path = BASE_DIR / "images" / "students" / "assignments.json"
    map_path.write_text(json.dumps(assignments, indent=2))
    print(f"\nAssignment map saved: {map_path}")
    print("\nNext step: run inject-student-images.py to embed images into HTML pages.")


if __name__ == "__main__":
    main()
