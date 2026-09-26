#!/usr/bin/env python3
"""Merge SRT or VTT caption cues into timestamped paragraphs.

Usage:
    python clean_subs.py input.srt [--gap 2.0] [--max-chars 600]

Prints paragraphs like "[00:01:05] text ..." to stdout. Standard library only.
"""
import argparse
import re
import sys

TIME_RE = re.compile(
    r"(?:(\d+):)?(\d{1,2}):(\d{2})[.,](\d{1,3})\s*-->\s*(?:(\d+):)?(\d{1,2}):(\d{2})[.,](\d{1,3})"
)
TAG_RE = re.compile(r"<[^>]+>|\{\\[^}]*\}")


def to_seconds(h, m, s, ms):
    return int(h or 0) * 3600 + int(m) * 60 + int(s) + int(ms.ljust(3, "0")) / 1000


def fmt(seconds):
    seconds = int(seconds)
    return f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}"


def parse_cues(text):
    """Return a list of (start, end, text) tuples."""
    cues = []
    blocks = re.split(r"\r?\n\s*\r?\n", text.replace("﻿", ""))
    for block in blocks:
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        for i, line in enumerate(lines):
            m = TIME_RE.search(line)
            if not m:
                continue
            g = m.groups()
            start = to_seconds(g[0], g[1], g[2], g[3])
            end = to_seconds(g[4], g[5], g[6], g[7])
            body = " ".join(TAG_RE.sub("", ln) for ln in lines[i + 1:])
            body = re.sub(r"\s+", " ", body).strip()
            if body:
                cues.append((start, end, body))
            break
    return cues


def dedupe_rolling(cues):
    """YouTube auto captions repeat the previous line; drop exact repeats and prefixes."""
    out = []
    for start, end, body in cues:
        if out:
            prev = out[-1][2]
            if body == prev or prev.endswith(body):
                continue
            if body.startswith(prev):
                body = body[len(prev):].strip()
                if not body:
                    continue
        out.append((start, end, body))
    return out


def merge(cues, gap, max_chars):
    paragraphs = []
    cur_start, cur_text, last_end = None, [], None
    for start, end, body in cues:
        new_para = (
            cur_start is None
            or (last_end is not None and start - last_end > gap)
            or sum(len(t) + 1 for t in cur_text) + len(body) > max_chars
        )
        if new_para and cur_text:
            paragraphs.append((cur_start, " ".join(cur_text)))
            cur_text = []
        if new_para:
            cur_start = start
        cur_text.append(body)
        last_end = end
    if cur_text:
        paragraphs.append((cur_start, " ".join(cur_text)))
    return paragraphs


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("file")
    ap.add_argument("--gap", type=float, default=2.0, help="silence in seconds that starts a new paragraph")
    ap.add_argument("--max-chars", type=int, default=600, help="soft maximum paragraph length")
    args = ap.parse_args(argv)
    try:
        with open(args.file, encoding="utf-8-sig", errors="replace") as fh:
            text = fh.read()
    except OSError as exc:
        sys.exit(f"Cannot read {args.file}: {exc}")
    cues = dedupe_rolling(parse_cues(text))
    if not cues:
        sys.exit("No caption cues found. Is this an SRT or VTT file?")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    for start, para in merge(cues, args.gap, args.max_chars):
        print(f"[{fmt(start)}] {para}\n")


if __name__ == "__main__":
    main()
