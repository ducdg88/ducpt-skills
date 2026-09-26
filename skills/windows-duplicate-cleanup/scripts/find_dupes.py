#!/usr/bin/env python3
"""Find duplicate files by size then SHA-256. Dry run by default.

Usage:
    python find_dupes.py FOLDER [--min-size 100KB] [--report dupes.json] [--move-to QUARANTINE]

Without --move-to nothing is changed. With --move-to, extra copies are moved
(never deleted) and every move is logged to moves.csv inside the quarantine.
"""
import argparse
import csv
import hashlib
import json
import os
import shutil
import sys
from collections import defaultdict

SKIP_DIRS = {"windows", "program files", "program files (x86)", "appdata", "$recycle.bin",
             "system volume information", ".git", "node_modules", "__pycache__"}
UNITS = {"B": 1, "KB": 1024, "MB": 1024 ** 2, "GB": 1024 ** 3}


def parse_size(text):
    text = text.strip().upper()
    for unit in ("GB", "MB", "KB", "B"):
        if text.endswith(unit):
            return int(float(text[: -len(unit)]) * UNITS[unit])
    return int(text)


def human(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} B"
        n /= 1024


def is_forbidden_root(path):
    path = os.path.abspath(path)
    drive, rest = os.path.splitdrive(path)
    return rest.strip("\\/") == "" or path in ("/", "/usr", "/System")


def walk(root, min_size, skip=None):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if d.lower() not in SKIP_DIRS
                       and not os.path.islink(os.path.join(dirpath, d))
                       and (skip is None or os.path.abspath(os.path.join(dirpath, d)) != skip)]
        for name in filenames:
            path = os.path.join(dirpath, name)
            try:
                if os.path.islink(path):
                    continue
                st = os.stat(path)
            except OSError:
                continue
            if st.st_size >= min_size:
                yield path, st.st_size, st.st_mtime


def sha256(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            block = fh.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def find_groups(root, min_size, skip=None):
    by_size = defaultdict(list)
    for path, size, mtime in walk(root, min_size, skip):
        by_size[size].append((path, mtime))
    groups = []
    for size, files in by_size.items():
        if len(files) < 2:
            continue
        by_hash = defaultdict(list)
        for path, mtime in files:
            try:
                by_hash[sha256(path)].append((path, mtime))
            except OSError:
                continue
        for digest, same in by_hash.items():
            if len(same) > 1:
                # keep rule: shortest path, then oldest
                same.sort(key=lambda f: (f[0].count(os.sep), len(f[0]), f[1]))
                groups.append({"size": size, "sha256": digest,
                               "keep": same[0][0], "extras": [p for p, _ in same[1:]]})
    groups.sort(key=lambda g: g["size"] * len(g["extras"]), reverse=True)
    return groups


def main(argv=None):
    ap = argparse.ArgumentParser(description="Find duplicate files (dry run by default).")
    ap.add_argument("folder")
    ap.add_argument("--min-size", default="1KB")
    ap.add_argument("--report")
    ap.add_argument("--move-to")
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    root = os.path.abspath(args.folder)
    if not os.path.isdir(root):
        sys.exit(f"Not a folder: {root}")
    if is_forbidden_root(root):
        sys.exit("Refusing to scan a whole drive or system root. Pick a specific folder.")

    quarantine = os.path.abspath(args.move_to) if args.move_to else None
    groups = find_groups(root, parse_size(args.min_size), skip=quarantine)
    wasted = sum(g["size"] * len(g["extras"]) for g in groups)
    print(f"{len(groups)} duplicate groups, {sum(len(g['extras']) for g in groups)} extra copies, "
          f"{human(wasted)} reclaimable")
    for g in groups[:10]:
        print(f"\n{human(g['size'])} x{len(g['extras']) + 1}\n  KEEP  {g['keep']}")
        for p in g["extras"]:
            print(f"  EXTRA {p}")
    if args.report:
        with open(args.report, "w", encoding="utf-8") as fh:
            json.dump({"root": root, "reclaimable_bytes": wasted, "groups": groups}, fh,
                      ensure_ascii=False, indent=2)
        print(f"\nReport written to {args.report}")

    if not quarantine:
        print("\nDry run only. Nothing was changed.")
        return
    os.makedirs(quarantine, exist_ok=True)
    log_path = os.path.join(quarantine, "moves.csv")
    new_log = not os.path.exists(log_path)
    moved = 0
    with open(log_path, "a", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        if new_log:
            writer.writerow(["from", "to", "sha256"])
        for g in groups:
            for src in g["extras"]:
                rel = os.path.relpath(src, root)
                dst = os.path.join(quarantine, rel)
                if os.path.exists(dst):
                    base, ext = os.path.splitext(dst)
                    dst = f"{base}.{g['sha256'][:8]}{ext}"
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                try:
                    shutil.move(src, dst)
                except OSError as exc:
                    print(f"SKIP {src}: {exc}")
                    continue
                writer.writerow([src, dst, g["sha256"]])
                moved += 1
    print(f"\nMoved {moved} files to {quarantine}. Undo log: {log_path}")


if __name__ == "__main__":
    main()
