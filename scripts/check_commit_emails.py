#!/usr/bin/env python3
"""Find local repos whose recent commits will not show on the GitHub contribution graph.

Usage:
    python scripts/check_commit_emails.py PATH [PATH ...] [--days 30]

A commit counts only when its author email is verified on the GitHub account
(or is the account's noreply address). Read only: it never changes config or history.
"""
import argparse
import json
import os
import subprocess
import sys


def run(cmd, cwd=None):
    out = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    return out.stdout if out.returncode == 0 else None


def account_emails():
    user = json.loads(run(["gh", "api", "user"]) or "{}")
    if not user:
        sys.exit("gh api user failed. Run `gh auth login`.")
    login, uid = user["login"], user["id"]
    emails = {f"{uid}+{login}@users.noreply.github.com".lower(), f"{login}@users.noreply.github.com".lower()}
    listed = run(["gh", "api", "user/emails"])  # needs the user:email scope
    if listed:
        emails |= {e["email"].lower() for e in json.loads(listed) if e.get("verified")}
    elif user.get("email"):
        emails.add(user["email"].lower())
    return login, emails, bool(listed)


def authors(path, days):
    out = run(["git", "log", "--all", f"--since={days}.days", "--format=%ae"], cwd=path)
    if out is None:
        return None
    counts = {}
    for email in out.split():
        counts[email.lower()] = counts.get(email.lower(), 0) + 1
    return counts


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--days", type=int, default=30)
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    login, ok, full = account_emails()
    print(f"@{login}: {len(ok)} counted emails" + ("" if full else " (noreply only, gh lacks user:email scope)"))
    bad = 0
    for path in args.paths:
        name = os.path.basename(os.path.normpath(path))
        if not os.path.isdir(os.path.join(path, ".git")) and run(["git", "rev-parse", "--git-dir"], cwd=path) is None:
            print(f"skip {name}: not a git repo")
            continue
        counts = authors(path, args.days) or {}
        lost = {e: n for e, n in counts.items() if e not in ok and "[bot]@" not in e}
        if lost:
            bad += 1
            detail = ", ".join(f"{e} ({n})" for e, n in sorted(lost.items(), key=lambda kv: -kv[1]))
            print(f"LOST {name}: {sum(lost.values())}/{sum(counts.values())} commits not counted: {detail}")
        else:
            print(f"ok   {name}: {sum(counts.values())} commits in {args.days} days")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
