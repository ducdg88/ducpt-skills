#!/usr/bin/env python3
"""Lint Vietnamese copy: dashes, long sentences, missing diacritics, CTA, length.

Usage:
    python check_copy.py FILE [--platform facebook]

Exit code 1 when a hard error (dash characters) is found. Standard library only.
"""
import argparse
import re
import sys
import unicodedata
from collections import Counter

TARGETS = {
    "facebook": (400, 1500), "tiktok": (80, 300), "youtube-title": (40, 70),
    "youtube-description": (300, 1500), "zalo": (150, 600), "email": (500, 2000), "web": (800, 10 ** 9),
}
DASHES = {chr(0x2013): "en dash", chr(0x2014): "em dash"}
CTA_HINTS = ["comment", "còm", "bình luận", "inbox", "nhắn", "đăng ký", "click", "bấm", "liên hệ",
             "gọi", "tải", "xem thêm", "link", "reply", "trả lời", "để lại", "đặt", "mua", "nhận"]
STOP = {"và", "là", "của", "có", "cho", "một", "những", "các", "được", "không", "này", "với", "thì",
        "mình", "bạn", "đã", "để", "trong", "khi", "người", "the", "a", "to", "of", "and"}
VN_LETTERS = set("ăâđêôơưĂÂĐÊÔƠƯ")


def has_diacritic(word):
    if any(ch in VN_LETTERS for ch in word):
        return True
    decomposed = unicodedata.normalize("NFD", word)
    return any(unicodedata.category(ch) == "Mn" for ch in decomposed)


def lint(text, platform):
    errors, warnings, info = [], [], []
    for ch, name in DASHES.items():
        for m in re.finditer(ch, text):
            line = text.count("\n", 0, m.start()) + 1
            errors.append(f"line {line}: {name} found, replace with comma, colon or full stop")

    sentences = [s.strip() for s in re.split(r"(?<=[.!?…])\s+|\n+", text) if s.strip()]
    for s in sentences:
        n = len(s.split())
        if n > 35:
            warnings.append(f"long sentence ({n} words): {s[:60]}...")

    words = re.findall(r"[^\W\d_]+", text)
    if words:
        plain = [w for w in words if w.isascii() and len(w) > 1]
        ratio = len([w for w in plain if not has_diacritic(w)]) / len(words)
        info.append(f"words without diacritics: {ratio:.0%}")
        if ratio > 0.45:
            warnings.append("many words have no diacritics; text may be missing dấu or be mostly English")
        counts = Counter(w.lower() for w in words if w.lower() not in STOP and len(w) > 2)
        for word, n in counts.most_common(3):
            if n >= 5 and n / len(words) > 0.03:
                warnings.append(f"'{word}' repeated {n} times")

    lower = text.lower()
    if platform not in ("youtube-title",) and not any(h in lower for h in CTA_HINTS):
        warnings.append("no clear call to action found")

    lo, hi = TARGETS[platform]
    length = len(text.strip())
    info.append(f"length: {length} chars (target {lo} to {hi if hi < 10 ** 9 else 'any'})")
    if length < lo or length > hi:
        warnings.append(f"length {length} outside {platform} target")
    return errors, warnings, info


def main(argv=None):
    ap = argparse.ArgumentParser(description="Lint Vietnamese copy.")
    ap.add_argument("file")
    ap.add_argument("--platform", default="facebook", choices=sorted(TARGETS))
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        with open(args.file, encoding="utf-8-sig") as fh:
            text = fh.read()
    except OSError as exc:
        sys.exit(f"Cannot read {args.file}: {exc}")
    errors, warnings, info = lint(text, args.platform)
    for line in info:
        print("INFO ", line)
    for line in warnings:
        print("WARN ", line)
    for line in errors:
        print("ERROR", line)
    print(f"\n{len(errors)} errors, {len(warnings)} warnings")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
