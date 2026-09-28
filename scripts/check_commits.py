#!/usr/bin/env python3
"""Refuse empty commits and messages with a literal backslash-n in a commit range.

Usage:
    python scripts/check_commits.py BASE..HEAD

An empty commit changes no file. Merge commits are skipped. Old history is not
checked, only the range given (CI passes the pushed range or the PR range).
"""
import subprocess
import sys


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8", check=True).stdout


def problems(sha, message, files, parents):
    out = []
    if parents < 2 and not files.strip():
        out.append("empty commit (changes no file)")
    if "\\n" in message:
        out.append("message contains a literal \\n, write real line breaks")
    return out


def main(argv):
    if len(argv) != 1:
        sys.exit(__doc__)
    bad = 0
    for sha in git("rev-list", "--reverse", argv[0]).split():
        message = git("log", "-1", "--format=%B", sha)
        parents = len(git("log", "-1", "--format=%P", sha).split())
        files = git("diff-tree", "--no-commit-id", "--name-only", "-r", "--root", sha)
        for issue in problems(sha, message, files, parents):
            bad += 1
            print(f"FAIL {sha[:7]} {message.splitlines()[0][:60] if message else ''}: {issue}")
    print("PASS" if not bad else f"{bad} problem(s)")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
