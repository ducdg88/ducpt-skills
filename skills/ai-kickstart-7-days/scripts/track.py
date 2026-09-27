#!/usr/bin/env python3
"""Track a solo/small business owner's 7-day AI kickstart plan. Standard library only.

    python track.py init plan.json --business "quán cà phê nhỏ" --pain "trả lời tin nhắn khách"
    python track.py done plan.json 1 --note "Đã dùng AI trả lời 5 câu hỏi khách hay hỏi"
    python track.py status plan.json [--json]

This script only tracks progress; SKILL.md tells the agent how to write the day-by-day
tasks themselves (tailored per interview), because that needs judgement a script cannot do.
"""
import argparse
import datetime as dt
import json
import sys
from pathlib import Path

DAYS = 7


def new_plan(business, pain):
    return {
        "business": business, "pain": pain,
        "started": dt.date.today().isoformat(),
        "days": {str(d): {"done": False, "note": "", "date": None} for d in range(1, DAYS + 1)},
    }


def load(path):
    p = Path(path)
    if not p.exists():
        raise SystemExit(f"{path}: not found. Run 'init' first.")
    return json.loads(p.read_text(encoding="utf-8-sig"))


def save(path, plan):
    Path(path).write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def cmd_init(a):
    p = Path(a.path)
    if p.exists() and not a.force:
        raise SystemExit(f"{a.path}: already exists. Use --force to overwrite.")
    save(a.path, new_plan(a.business, a.pain))
    print(f"Created {a.path} for \"{a.business}\": 7 days, 0 done.")


def cmd_done(a):
    if not 1 <= a.day <= DAYS:
        raise SystemExit(f"day must be 1 to {DAYS}, got {a.day}")
    plan = load(a.path)
    plan["days"][str(a.day)] = {"done": True, "note": a.note or "", "date": dt.date.today().isoformat()}
    save(a.path, plan)
    print(f"Day {a.day} marked done.")


def status_data(plan):
    done_days = [int(d) for d, v in plan["days"].items() if v["done"]]
    next_day = next((d for d in range(1, DAYS + 1) if d not in done_days), None)
    return {"business": plan["business"], "pain": plan["pain"], "started": plan["started"],
            "done_count": len(done_days), "total": DAYS, "done_days": sorted(done_days),
            "next_day": next_day, "finished": next_day is None}


def cmd_status(a):
    plan = load(a.path)
    s = status_data(plan)
    if a.json:
        print(json.dumps(s, ensure_ascii=False, indent=2))
        return
    print(f"{s['business']}: {s['done_count']}/{s['total']} ngày xong, bắt đầu {s['started']}")
    for d in range(1, DAYS + 1):
        v = plan["days"][str(d)]
        mark = "x" if v["done"] else " "
        note = f" - {v['note']}" if v["note"] else ""
        print(f"  [{mark}] ngày {d}{note}")
    print("Xong hết rồi!" if s["finished"] else f"Ngày tiếp theo: {s['next_day']}")


def main():
    for s in (sys.stdout, sys.stderr):
        if hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    i = sub.add_parser("init")
    i.add_argument("path")
    i.add_argument("--business", required=True)
    i.add_argument("--pain", required=True)
    i.add_argument("--force", action="store_true")
    i.set_defaults(func=cmd_init)

    d = sub.add_parser("done")
    d.add_argument("path")
    d.add_argument("day", type=int)
    d.add_argument("--note", default="")
    d.set_defaults(func=cmd_done)

    st = sub.add_parser("status")
    st.add_argument("path")
    st.add_argument("--json", action="store_true")
    st.set_defaults(func=cmd_status)

    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
