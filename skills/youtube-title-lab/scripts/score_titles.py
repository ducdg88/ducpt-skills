#!/usr/bin/env python3
"""Score YouTube title candidates with a transparent 0 to 100 rubric.

Usage:
    python score_titles.py titles.txt [--keyword "main phrase"] [--lang en|vi]

Prints titles sorted by score with the reasons. Standard library only.
"""
import argparse
import re
import sys

CURIOSITY = {
    "en": ["why", "how", "secret", "mistake", "never", "nobody", "actually", "vs", "before", "after",
           "finally", "truth", "without", "only", "stop", "instead"],
    "vi": ["tại sao", "vì sao", "bí mật", "sai lầm", "không ai", "sự thật", "thật ra", "trước", "sau",
           "cuối cùng", "chỉ", "đừng", "thay vì", "không cần", "cách"],
}
VAGUE = {
    "en": ["amazing", "awesome", "incredible", "best video", "must watch", "you won't believe"],
    "vi": ["tuyệt vời", "đỉnh cao", "không thể tin", "hay nhất", "phải xem"],
}


def score(title, keyword, lang):
    points, notes = 0, []
    n = len(title)
    if 35 <= n <= 60:
        points += 25
        notes.append("length ideal")
    elif 25 <= n <= 70:
        points += 15
        notes.append("length ok")
    else:
        notes.append(f"length {n} weak" + (" (cut off on mobile)" if n > 70 else ""))

    low = title.lower()
    if keyword:
        pos = low.find(keyword.lower())
        if pos == -1:
            notes.append("keyword missing")
        elif pos <= n / 2:
            points += 20
            notes.append("keyword early")
        else:
            points += 10
            notes.append("keyword late")
    else:
        points += 10

    if re.search(r"\d", title):
        points += 15
        notes.append("has number")

    if any(re.search(r"(?<!\w)" + re.escape(w) + r"(?!\w)", low) for w in CURIOSITY[lang]):
        points += 15
        notes.append("curiosity or contrast")

    words = re.findall(r"\w+", title)
    caps = [w for w in words if len(w) > 3 and w.isupper()]
    if len(caps) <= 1:
        points += 10
    else:
        notes.append("too many CAPS words")

    if title.count("!") <= 1:
        points += 5
    else:
        notes.append("too many !")

    if any(v in low for v in VAGUE[lang]):
        points -= 10
        notes.append("vague hype word")

    if chr(0x2013) in title or chr(0x2014) in title:
        points -= 5
        notes.append("long dash, use colon or comma")

    points += 10 if 5 <= len(words) <= 12 else 0
    return max(0, min(100, points)), notes


def main(argv=None):
    ap = argparse.ArgumentParser(description="Score YouTube titles.")
    ap.add_argument("file")
    ap.add_argument("--keyword", default="")
    ap.add_argument("--lang", default="en", choices=["en", "vi"])
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        with open(args.file, encoding="utf-8-sig") as fh:
            titles = [ln.strip() for ln in fh if ln.strip()]
    except OSError as exc:
        sys.exit(f"Cannot read {args.file}: {exc}")
    if not titles:
        sys.exit("No titles found (one per line).")
    rows = sorted(((score(t, args.keyword, args.lang), t) for t in titles), key=lambda r: -r[0][0])
    for (pts, notes), title in rows:
        print(f"{pts:3d}  {title}\n     {', '.join(notes)}")


if __name__ == "__main__":
    main()
