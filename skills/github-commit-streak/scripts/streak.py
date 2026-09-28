#!/usr/bin/env python3
"""Show GitHub contribution streak and pace toward a goal, using the gh CLI.

Usage:
    python streak.py [--user LOGIN] [--goal 10000] [--by YYYY-MM-DD] [--per-day N] [--json]

A GitHub calendar day is a UTC day, so "today" here is the UTC date. In Vietnam
(UTC+7) a day closes at 07:00 local time; read yesterday's number after that.
With --per-day N it also reports the last 7 and 30 closed days against a daily
target, split by contribution type.

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
    createdAt
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

TYPES_QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      totalPullRequestReviewContributions
      totalRepositoryContributions
      restrictedContributionsCount
    }
  }
}
"""

TYPE_NAMES = {
    "totalCommitContributions": "commits",
    "totalPullRequestContributions": "pull_requests",
    "totalIssueContributions": "issues",
    "totalPullRequestReviewContributions": "reviews",
    "totalRepositoryContributions": "repositories",
    "restrictedContributionsCount": "private_hidden",
}


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
    created = dt.date.fromisoformat(user["createdAt"][:10])
    return coll["contributionCalendar"]["totalContributions"], coll["restrictedContributionsCount"], days, created


def fetch_types(login, start, end):
    """Contribution counts by type for the UTC days start..end inclusive."""
    data = json.loads(gh([
        "api", "graphql", "-f", f"query={TYPES_QUERY}", "-F", f"login={login}",
        "-F", f"from={start.isoformat()}T00:00:00Z", "-F", f"to={end.isoformat()}T23:59:59Z",
    ]))
    coll = data["data"]["user"]["contributionsCollection"]
    return {name: coll[key] for key, name in TYPE_NAMES.items()}


def github_today():
    return dt.datetime.now(dt.timezone.utc).date()


def as_counts(days, today):
    counts = [(dt.date.fromisoformat(d["date"]), d["contributionCount"]) for d in days]
    return sorted(c for c in counts if c[0] <= today)


def streaks(days, today):
    counts = as_counts(days, today)
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


def needed_per_day(days, today, goal, by):
    """Per day needed from tomorrow on so the 365 days ending on `by` hold `goal`.

    Only contributions still inside that window on `by` count; older ones slide out.
    """
    start = by - dt.timedelta(days=364)
    kept = sum(n for d, n in as_counts(days, today) if d >= start)
    return round(max(0, goal - kept) / max(1, (by - today).days), 1)


def avg_per_day(total, today, created):
    """Average over the calendar window, not counting days before the account existed."""
    start = max(created, today - dt.timedelta(days=364))
    return round(total / max(1, (today - start).days + 1), 1)


def per_day(days, today, target):
    """Closed days only: today (UTC) is still open and is reported as provisional."""
    counts = as_counts(days, today)
    closed = [(d, n) for d, n in counts if d < today]
    last7, last30 = closed[-7:], closed[-30:]
    return {
        "target": target,
        "today_provisional": counts[-1][1] if counts and counts[-1][0] == today else 0,
        "last_7": [{"date": d.isoformat(), "count": n} for d, n in last7],
        "avg_7": round(sum(n for _, n in last7) / max(1, len(last7)), 1),
        "avg_30": round(sum(n for _, n in last30) / max(1, len(last30)), 1),
        "days_at_target_30": sum(1 for _, n in last30 if n >= target),
        "zero_days_7": sum(1 for _, n in last7 if n == 0),
        "zero_days_30": sum(1 for _, n in last30 if n == 0),
        "window_30": [last30[0][0].isoformat(), last30[-1][0].isoformat()] if last30 else [],
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="GitHub contribution streak.")
    ap.add_argument("--user")
    ap.add_argument("--goal", type=int, default=10000)
    ap.add_argument("--by", help="goal date YYYY-MM-DD (default: one year from today)")
    ap.add_argument("--per-day", type=int, metavar="N", help="daily target, e.g. 100")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    login = args.user or gh(["api", "user", "--jq", ".login"]).strip()
    total, restricted, days, created = fetch(login)
    today = github_today()
    current, longest, zero30, today_count = streaks(days, today)
    by = dt.date.fromisoformat(args.by) if args.by else today.replace(year=today.year + 1)
    result = {
        "user": login, "date": today.isoformat(), "last_year_total": total,
        "private_hidden": restricted, "today": today_count, "current_streak": current,
        "longest_streak": longest, "zero_days_last_30": zero30,
        "avg_per_day": avg_per_day(total + restricted, today, created), "goal": args.goal,
        "goal_date": by.isoformat(), "needed_per_day": needed_per_day(days, today, args.goal, by),
    }
    if args.per_day:
        daily = per_day(days, today, args.per_day)
        if daily["window_30"]:
            start, end = (dt.date.fromisoformat(x) for x in daily["window_30"])
            daily["by_type_30"] = fetch_types(login, start, end)
        result["per_day"] = daily
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    print(f"@{login}  {today} (UTC day)")
    print(f"  Last year:       {total} contributions (+{restricted} private hidden)")
    print(f"  Today:           {today_count} (still open)")
    print(f"  Current streak:  {current} days   Longest: {longest} days")
    print(f"  Zero days (30d): {zero30}")
    print(f"  Goal {args.goal} by {by}: need {result['needed_per_day']} per day "
          f"(now {result['avg_per_day']} per day)")
    if args.per_day:
        d = result["per_day"]
        print(f"  Target {d['target']} per day, closed days:")
        print("    " + "  ".join(f"{x['date'][5:]}: {x['count']}" for x in d["last_7"]))
        print(f"    Avg 7d {d['avg_7']}, avg 30d {d['avg_30']}, days at target (30d) {d['days_at_target_30']}, "
              f"zero days 7d {d['zero_days_7']}, 30d {d['zero_days_30']}")
        if "by_type_30" in d:
            print("    30d by type: " + ", ".join(f"{k} {v}" for k, v in d["by_type_30"].items()))


if __name__ == "__main__":
    main()
