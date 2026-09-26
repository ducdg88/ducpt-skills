#!/usr/bin/env python3
"""Show GitHub contribution streak and pace toward a goal, using the gh CLI.

Usage:
    python streak.py [--user LOGIN] [--goal 10000] [--by YYYY-MM-DD] [--json]

Needs `gh auth login`. Standard library only.
"""
import argparse
import datetime as dt
import json
import subprocess
import sys

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
      restrictedContributionsCount
    }
  }
}
"""


def gh(args):
    try:
        out = subprocess.run(["gh", *args], capture_output=True, text=True, encoding="utf-8", check=True)
    except FileNotFoundError:
        sys.exit("GitHub CLI (gh) not found. Install it and run `gh auth login`.")
    except subprocess.CalledProcessError as exc:
        sys.exit(f"gh failed: {exc.stderr.strip()}")
    return out.stdout


def fetch(login):
    data = json.loads(gh(["api", "graphql", "-f", f"query={QUERY}", "-F", f"login={login}"]))
    user = (data.get("data") or {}).get("user")
    if not user:
        sys.exit(f"User {login} not found.")
    coll = user["contributionsCollection"]
    days = [d for w in coll["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
    return coll["contributionCalendar"]["totalContributions"], coll["restrictedContributionsCount"], days


def streaks(days, today):
    counts = [(dt.date.fromisoformat(d["date"]), d["contributionCount"]) for d in days]
    counts = [c for c in counts if c[0] <= today]
    longest = run = 0
    for _, n in counts:
        run = run + 1 if n > 0 else 0
        longest = max(longest, run)
    current = 0
    items = list(reversed(counts))
    if items and items[0][0] == today and items[0][1] == 0:
        items = items[1:]  # today still open, do not break the streak yet
    for _, n in items:
        if n == 0:
            break
        current += 1
    last30 = [n for d, n in counts if (today - d).days < 30]
    return current, longest, sum(1 for n in last30 if n == 0), (counts[-1][1] if counts else 0)


def main(argv=None):
    ap = argparse.ArgumentParser(description="GitHub contribution streak.")
    ap.add_argument("--user")
    ap.add_argument("--goal", type=int, default=10000)
    ap.add_argument("--by", help="goal date YYYY-MM-DD (default: one year from today)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    login = args.user or gh(["api", "user", "--jq", ".login"]).strip()
    total, restricted, days = fetch(login)
    today = dt.date.today()
    current, longest, zero30, today_count = streaks(days, today)
    by = dt.date.fromisoformat(args.by) if args.by else today.replace(year=today.year + 1)
    days_left = max(1, (by - today).days)
    remaining = max(0, args.goal - total - restricted)
    result = {
        "user": login, "date": today.isoformat(), "last_year_total": total,
        "private_hidden": restricted, "today": today_count, "current_streak": current,
        "longest_streak": longest, "zero_days_last_30": zero30,
        "avg_per_day": round((total + restricted) / 365, 1), "goal": args.goal, "goal_date": by.isoformat(),
        "needed_per_day": round(remaining / days_left, 1),
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    print(f"@{login}  {today}")
    print(f"  Last year:       {total} contributions (+{restricted} private hidden)")
    print(f"  Today:           {today_count}")
    print(f"  Current streak:  {current} days   Longest: {longest} days")
    print(f"  Zero days (30d): {zero30}")
    print(f"  Goal {args.goal} by {by}: need {result['needed_per_day']} per day "
          f"(now {result['avg_per_day']} per day)")


if __name__ == "__main__":
    main()
