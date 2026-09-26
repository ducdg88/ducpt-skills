#!/usr/bin/env python3
"""Validate pins JSON against Pinterest limits and write a bulk upload CSV.

Usage:
    python make_pin_csv.py pins.json pins.csv

Exit code 1 if any pin breaks a hard limit. Standard library only.
"""
import csv
import json
import sys
from urllib.parse import urlparse

LIMITS = {"title": 100, "description": 500, "alt_text": 500}
COLUMNS = ["Title", "Media URL", "Pinterest board", "Thumbnail", "Description", "Link", "Publish date", "Keywords"]


def is_url(value):
    parts = urlparse(value or "")
    return parts.scheme in ("http", "https") and bool(parts.netloc)


def check(pin, index):
    errors, warnings = [], []
    for field, limit in LIMITS.items():
        value = pin.get(field, "") or ""
        if len(value) > limit:
            errors.append(f"pin {index}: {field} is {len(value)} chars (max {limit})")
    if not pin.get("title"):
        errors.append(f"pin {index}: title is empty")
    if not pin.get("board"):
        errors.append(f"pin {index}: board is empty")
    if not is_url(pin.get("media_url")):
        errors.append(f"pin {index}: media_url is not a valid http(s) URL")
    if not is_url(pin.get("link")):
        errors.append(f"pin {index}: link is not a valid http(s) URL")
    desc = pin.get("description", "") or ""
    if 0 < len(desc) < 150:
        warnings.append(f"pin {index}: description is short ({len(desc)} chars), aim for 150+")
    if desc.count("#") > 3:
        warnings.append(f"pin {index}: {desc.count('#')} hashtags, keep 3 or fewer")
    if "utm_" not in (pin.get("link") or ""):
        warnings.append(f"pin {index}: link has no UTM tags, traffic will not be attributable")
    return errors, warnings


def main(argv):
    if len(argv) != 3:
        sys.exit(__doc__)
    try:
        with open(argv[1], encoding="utf-8") as fh:
            pins = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        sys.exit(f"Cannot read pins JSON: {exc}")
    if not isinstance(pins, list) or not pins:
        sys.exit("pins JSON must be a non-empty list of objects")
    all_errors = []
    for i, pin in enumerate(pins, 1):
        errors, warnings = check(pin, i)
        all_errors += errors
        for w in warnings:
            print("WARN ", w)
    for e in all_errors:
        print("ERROR", e)
    if all_errors:
        sys.exit(1)
    with open(argv[2], "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(COLUMNS)
        for pin in pins:
            keywords = pin.get("keywords", "")
            if isinstance(keywords, list):
                keywords = ", ".join(keywords)
            writer.writerow([
                pin["title"], pin["media_url"], pin["board"], pin.get("thumbnail", ""),
                pin.get("description", ""), pin["link"], pin.get("publish_date", ""), keywords,
            ])
    print(f"OK wrote {len(pins)} pins to {argv[2]}")


if __name__ == "__main__":
    main(sys.argv)
