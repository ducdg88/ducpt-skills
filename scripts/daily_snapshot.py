#!/usr/bin/env python3
"""Daily measured snapshot: GitHub traffic + contribution streak, then commit.

Usage:
    python scripts/daily_snapshot.py [--dry-run] [--push] [--ref REF]
    python scripts/daily_snapshot.py --provisional [--warn-below 60]

What it does, in order:
1. Fetches origin and checks out REF (default origin/main) in a throwaway worktree,
   so it never touches the shared checkout or whatever branch is open there.
2. Reads traffic (views, clones, referrers) for every repo in data/tracked_repos.txt.
   GitHub keeps only 14 days, so each day is merged into data/traffic/<repo>.json.
3. Reads the contribution streak and the daily target report into data/streak.json.
4. Rewrites STATS.md from the saved data.
5. Runs scripts/check_repo.py. Only if it passes and something changed, commits
   data/ and STATS.md (nothing else) as "stats: snapshot YYYY-MM-DD".
6. With --push: pushes HEAD:main, rebasing once on origin/main if main moved.
   Push is only allowed from origin/main, never from a feature branch.
Every commit therefore holds real measured data, never an empty change.

--provisional only reads today's open GitHub day and warns when it is below the
threshold. It writes and commits nothing. Any failure exits non-zero.

Run it at 07:15 Vietnam time: the GitHub day (UTC) closed at 07:00, so the
report holds final numbers for yesterday.
"""
import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import tempfile

HOME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DAILY_TARGET = 100
STREAK = os.path.join("skills", "github-commit-streak", "scripts", "streak.py")


def run(cmd, cwd, check=True):
    out = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    if check and out.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} failed: {out.stderr.strip() or out.stdout.strip()}")
    return out


def gh_json(path, cwd):
    out = run(["gh", "api", path], cwd, check=False)
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


def snapshot_repo(root, full_name, today):
    path = os.path.join(root, "data", "traffic", full_name.replace("/", "__") + ".json")
    saved = load(path, {"repo": full_name, "days": {}, "referrers": {}})
    views = gh_json(f"repos/{full_name}/traffic/views", root)
    clones = gh_json(f"repos/{full_name}/traffic/clones", root)
    refs = gh_json(f"repos/{full_name}/traffic/popular/referrers", root)
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


def read_streak(root):
    out = run([sys.executable, os.path.join(root, STREAK), "--json", "--goal", "10000",
               "--per-day", str(DAILY_TARGET)], root, check=False)
    if out.returncode != 0:
        return None, out.stderr.strip()[:200]
    return json.loads(out.stdout), ""


def kpi_lines(daily):
    lines = [
        f"## Daily target: {daily['target']} contributions",
        "",
        "Closed GitHub days (UTC). A day is final after 07:00 Vietnam time.",
        "",
        "| Day | Contributions | Target met |",
        "|---|---|---|",
    ]
    for d in daily["last_7"]:
        lines.append(f"| {d['date']} | {d['count']} | {'yes' if d['count'] >= daily['target'] else 'no'} |")
    lines += [
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Average, last 7 days | {daily['avg_7']} |",
        f"| Average, last 30 days | {daily['avg_30']} |",
        f"| Days at target, last 30 | {daily['days_at_target_30']} |",
        f"| Zero days, last 7 / 30 | {daily['zero_days_7']} / {daily['zero_days_30']} |",
    ]
    types = daily.get("by_type_30")
    if types:
        lines.append("| By type, last 30 days | " + ", ".join(f"{k} {v}" for k, v in types.items()) + " |")
    return lines + [""]


def write_stats(root, repos, streak, today):
    lines = [
        "# Stats",
        "",
        f"Updated {today} by `scripts/daily_snapshot.py`. Numbers come from the GitHub API.",
        "",
    ]
    if streak and streak.get("per_day"):
        lines += kpi_lines(streak["per_day"])
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
    with open(os.path.join(root, "STATS.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")


def measure(root, today):
    with open(os.path.join(root, "data", "tracked_repos.txt"), encoding="utf-8") as fh:
        repos = [ln.strip() for ln in fh if ln.strip() and not ln.startswith("#")]
    snapshots = []
    for full in repos:
        data, ok = snapshot_repo(root, full, today)
        print(f"{'ok  ' if ok else 'skip'} traffic {full}")
        snapshots.append(data)

    streak, err = read_streak(root)
    if streak:
        path = os.path.join(root, "data", "streak.json")
        history = load(path, {})
        history[today] = streak
        save(path, history)
        daily = streak.get("per_day") or {}
        print(f"ok   streak {streak['current_streak']} days, {streak['last_year_total']} last year, "
              f"avg 7d {daily.get('avg_7')} (target {DAILY_TARGET})")
    else:
        print("skip streak:", err)
    write_stats(root, snapshots, streak, today)


def push(root):
    for attempt in (1, 2):
        out = run(["git", "push", "--quiet", "origin", "HEAD:main"], root, check=False)
        if out.returncode == 0:
            print("pushed to main")
            return
        if attempt == 2:
            raise RuntimeError(f"push failed: {out.stderr.strip()}")
        print("push rejected, rebasing on origin/main once")
        run(["git", "fetch", "--quiet", "origin", "main"], root)
        rebase = run(["git", "rebase", "origin/main"], root, check=False)
        if rebase.returncode != 0:
            run(["git", "rebase", "--abort"], root, check=False)
            raise RuntimeError("rebase on origin/main failed, not pushing")


def snapshot(args):
    today = dt.date.today().isoformat()
    if args.push and args.ref != "origin/main":
        sys.exit("--push only runs from origin/main.")
    run(["git", "fetch", "--quiet", "origin"], HOME)
    work = tempfile.mkdtemp(prefix="ducpt-snapshot-")
    try:
        run(["git", "worktree", "add", "--quiet", "--detach", work, args.ref], HOME)
        print(f"worktree {work} at {run(['git', 'rev-parse', '--short', 'HEAD'], work).stdout.strip()} ({args.ref})")
        measure(work, today)
        gate = run([sys.executable, os.path.join(work, "scripts", "check_repo.py")], work, check=False)
        if gate.returncode != 0:
            print(gate.stdout)
            raise RuntimeError("Quality gate failed, not committing.")
        status = run(["git", "status", "--porcelain", "--", "data", "STATS.md"], work).stdout.strip()
        if not status:
            print("No change today, nothing to commit.")
            return
        if args.dry_run:
            print("Dry run, would commit:\n" + status)
            print(run(["git", "diff", "--stat", "--", "data", "STATS.md"], work).stdout)
            return
        run(["git", "add", "--", "data", "STATS.md"], work)
        run(["git", "commit", "--quiet", "-m", f"stats: snapshot {today}", "--", "data", "STATS.md"], work)
        sha = run(["git", "rev-parse", "--short", "HEAD"], work).stdout.strip()
        print(f"committed {sha} stats: snapshot {today}")
        if args.push:
            push(work)
    finally:
        run(["git", "worktree", "remove", "--force", work], HOME, check=False)
        shutil.rmtree(work, ignore_errors=True)
        run(["git", "worktree", "prune"], HOME, check=False)


def provisional(args):
    streak, err = read_streak(HOME)
    if not streak:
        raise RuntimeError(f"streak failed: {err}")
    daily = streak["per_day"]
    count = daily["today_provisional"]
    print(f"GitHub day {streak['date']} (UTC, still open): {count} contributions, "
          f"target {daily['target']}, avg 7d {daily['avg_7']}")
    if count < args.warn_below:
        print(f"WARNING: below {args.warn_below}. Push finished work (real tickets) before 07:00 Vietnam time.")


def main(argv):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Daily GitHub stats snapshot.")
    ap.add_argument("--push", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--ref", default="origin/main", help="what to measure on (dry runs can use a branch)")
    ap.add_argument("--provisional", action="store_true", help="read today's open day only, write nothing")
    ap.add_argument("--warn-below", type=int, default=60)
    args = ap.parse_args(argv)
    print(f"--- {dt.datetime.now().isoformat(timespec='seconds')} daily_snapshot {' '.join(argv)}")
    try:
        provisional(args) if args.provisional else snapshot(args)
    except RuntimeError as exc:
        sys.exit(f"FAILED: {exc}")


if __name__ == "__main__":
    main(sys.argv[1:])
