#!/usr/bin/env python3
"""Daily measured snapshot: GitHub traffic + contribution streak, then commit.

Usage:
    python scripts/daily_snapshot.py [--push] [--dry-run]

What it does, in order:
1. Reads traffic (views, clones, referrers) for every repo in data/tracked_repos.txt.
   GitHub keeps only 14 days, so each day is merged into data/traffic/<repo>.json.
2. Reads the contribution streak of the logged in gh user into data/streak.json.
3. Rewrites STATS.md from the saved data.
4. Runs scripts/check_repo.py. Only if it passes and something changed, commits
   "stats: snapshot YYYY-MM-DD" and (with --push) pushes.
Every commit therefore holds real measured data, never an empty change.
"""
import datetime as dt
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
TRAFFIC = os.path.join(DATA, "traffic")
STREAK_SCRIPT = os.path.join(ROOT, "skills", "github-commit-streak", "scripts", "streak.py")


def run(cmd, check=True):
    out = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    if check and out.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} failed: {out.stderr.strip() or out.stdout.strip()}")
    return out


def gh_json(path):
    out = run(["gh", "api", path], check=False)
    if out.returncode != 0:
        return None
    return json.loads(out.stdout)


def load(path, default):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return default


def save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")


def snapshot_repo(full_name, today):
    path = os.path.join(TRAFFIC, full_name.replace("/", "__") + ".json")
    saved = load(path, {"repo": full_name, "days": {}, "referrers": {}})
    views = gh_json(f"repos/{full_name}/traffic/views")
    clones = gh_json(f"repos/{full_name}/traffic/clones")
    refs = gh_json(f"repos/{full_name}/traffic/popular/referrers")
    if views is None and clones is None:
        return saved, False
    for item in (views or {}).get("views", []):
        day = saved["days"].setdefault(item["timestamp"][:10], {})
        day.update({"views": item["count"], "unique_views": item["uniques"]})
    for item in (clones or {}).get("clones", []):
        day = saved["days"].setdefault(item["timestamp"][:10], {})
        day.update({"clones": item["count"], "unique_clones": item["uniques"]})
    if refs is not None:
        saved["referrers"][today] = {r["referrer"]: r["count"] for r in refs}
    save(path, saved)
    return saved, True


def write_stats(repos, streak, today):
    lines = [
        "# Stats",
        "",
        f"Updated {today} by `scripts/daily_snapshot.py`. Numbers come from the GitHub API.",
        "",
    ]
    if streak:
        lines += [
            "## Contribution streak",
            "",
            "| Metric | Value |",
            "|---|---|",
            f"| Contributions, last 365 days | {streak['last_year_total']} (+{streak['private_hidden']} private hidden) |",
            f"| Current streak | {streak['current_streak']} days |",
            f"| Longest streak | {streak['longest_streak']} days |",
            f"| Zero days, last 30 | {streak['zero_days_last_30']} |",
            f"| Goal | {streak['goal']} by {streak['goal_date']}, needs {streak['needed_per_day']} per day |",
            "",
        ]
    lines += ["## Repository traffic, last 30 days", "",
              "| Repo | Views | Unique | Clones | Top referrers |", "|---|---|---|---|---|"]
    cutoff = (dt.date.fromisoformat(today) - dt.timedelta(days=30)).isoformat()
    for data in repos:
        days = {d: v for d, v in data["days"].items() if d >= cutoff}
        views = sum(v.get("views", 0) for v in days.values())
        uniq = sum(v.get("unique_views", 0) for v in days.values())
        clones = sum(v.get("clones", 0) for v in days.values())
        latest = data["referrers"][max(data["referrers"])] if data["referrers"] else {}
        top = ", ".join(f"{k} {v}" for k, v in sorted(latest.items(), key=lambda kv: -kv[1])[:3]) or "none yet"
        lines.append(f"| {data['repo']} | {views} | {uniq} | {clones} | {top} |")
    with open(os.path.join(ROOT, "STATS.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")


def main(argv):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    push, dry = "--push" in argv, "--dry-run" in argv
    today = dt.date.today().isoformat()

    tracked = os.path.join(DATA, "tracked_repos.txt")
    with open(tracked, encoding="utf-8") as fh:
        repos = [ln.strip() for ln in fh if ln.strip() and not ln.startswith("#")]
    snapshots = []
    for full in repos:
        data, ok = snapshot_repo(full, today)
        print(f"{'ok  ' if ok else 'skip'} traffic {full}")
        snapshots.append(data)

    streak = None
    out = run([sys.executable, STREAK_SCRIPT, "--json", "--goal", "10000"], check=False)
    if out.returncode == 0:
        streak = json.loads(out.stdout)
        history = load(os.path.join(DATA, "streak.json"), {})
        history[today] = streak
        save(os.path.join(DATA, "streak.json"), history)
        print(f"ok   streak {streak['current_streak']} days, {streak['last_year_total']} last year")
    else:
        print("skip streak:", out.stderr.strip()[:200])

    write_stats(snapshots, streak, today)

    gate = run([sys.executable, os.path.join(ROOT, "scripts", "check_repo.py")], check=False)
    if gate.returncode != 0:
        print(gate.stdout)
        sys.exit("Quality gate failed, not committing.")
    status = run(["git", "status", "--porcelain", "--", "data", "STATS.md"]).stdout.strip()
    if not status:
        print("No change today, nothing to commit.")
        return
    if dry:
        print("Dry run, would commit:\n" + status)
        return
    run(["git", "add", "data", "STATS.md"])
    run(["git", "commit", "-m", f"stats: snapshot {today}"])
    print(f"committed stats: snapshot {today}")
    if push:
        run(["git", "push", "--quiet", "origin", "HEAD"])
        print("pushed")


if __name__ == "__main__":
    main(sys.argv[1:])
