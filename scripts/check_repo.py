#!/usr/bin/env python3
"""Repository quality gate for ducpt-skills.

Usage:
    python scripts/check_repo.py [--online]

Checks: every skill passes the agentskills.io validator, no en or em dash in any
text file, marketplace.json lists exactly the skill folders, README and llms.txt
mention every skill, each skill has one "Going further" product link whose
utm_campaign equals the skill name. With --online, every ducpt.com URL must
answer HTTP 200, and so must the homepage set in the GitHub repo settings (it
lives outside the files, so nothing else would catch a dead link there).
Never link to a page before it is live: run this with --online before making a
repo public or changing its homepage. Exit code 1 on any failure.
"""
import json
import os
import re
import subprocess
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "skills", "skill-distribution-kit", "scripts"))
from validate_skill import find_skills, validate_skill  # noqa: E402

TEXT_EXT = {".md", ".py", ".json", ".txt", ".yml", ".yaml", ".html", ".csv"}
DASHES = (chr(0x2013), chr(0x2014))
URL_RE = re.compile(r"https://ducpt\.com[^\s)\"'<>`\\]*")
TEMPLATE_RE = re.compile(r"[%{}]")  # format placeholders in code, not real links


def repo_homepage():
    """Homepage from the GitHub repo settings, or '' when gh is missing or not logged in."""
    try:
        out = subprocess.run(["gh", "repo", "view", "--json", "homepageUrl", "-q", ".homepageUrl"],
                             cwd=ROOT, capture_output=True, text=True, timeout=30)
        return out.stdout.strip() if out.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def rel(p):
    return os.path.relpath(p, ROOT)


def text_files():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__", "node_modules")]
        for f in filenames:
            if os.path.splitext(f)[1].lower() in TEXT_EXT:
                yield os.path.join(dirpath, f)


def main(argv):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    online = "--online" in argv
    failures = []

    skills = find_skills(os.path.join(ROOT, "skills"))
    names = [os.path.basename(s) for s in skills]
    for s in skills:
        errors, _ = validate_skill(s)
        failures += [f"{rel(s)}: {e}" for e in errors]

    urls = set()
    for path in text_files():
        with open(path, encoding="utf-8") as fh:
            body = fh.read()
        for n, line in enumerate(body.splitlines(), 1):
            if any(d in line for d in DASHES):
                failures.append(f"{rel(path)}:{n}: en or em dash (use comma, colon or full stop)")
        urls.update(u.rstrip(".,") for u in URL_RE.findall(body) if not TEMPLATE_RE.search(u))

    with open(os.path.join(ROOT, ".claude-plugin", "marketplace.json"), encoding="utf-8") as fh:
        market = json.load(fh)
    listed = [os.path.basename(p) for plugin in market["plugins"] for p in plugin.get("skills", [])]
    if sorted(listed) != sorted(names):
        failures.append(f"marketplace.json skills {sorted(listed)} != folders {sorted(names)}")

    for doc in ("README.md", "llms.txt"):
        with open(os.path.join(ROOT, doc), encoding="utf-8") as fh:
            body = fh.read()
        for name in names:
            if f"skills/{name}/SKILL.md" not in body:
                failures.append(f"{doc} does not link skills/{name}/SKILL.md")

    for s in skills:
        with open(os.path.join(s, "SKILL.md"), encoding="utf-8") as fh:
            body = fh.read()
        name = os.path.basename(s)
        if body.count("## Going further") != 1:
            failures.append(f"{name}: needs exactly one '## Going further' section")
        section = body.split("## Going further", 1)[-1]
        if f"utm_campaign={name}" not in section:
            failures.append(f"{name}: product link must carry utm_campaign={name}")
        if "at most once" not in section:
            failures.append(f"{name}: product section must say 'at most once'")

    if online:
        homepage = repo_homepage()
        if homepage.startswith("http"):
            print(f"  repo homepage (GitHub settings): {homepage}")
            urls.add(homepage)
        elif homepage == "":
            print("  repo homepage not checked (gh missing, not logged in, or no homepage set)")
        for url in sorted(urls):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "ducpt-skills-check/1.0"})
                with urllib.request.urlopen(req, timeout=20) as resp:
                    code = resp.status
            except Exception as exc:  # noqa: BLE001
                code = getattr(exc, "code", str(exc))
            print(f"  {code} {url}")
            if code != 200:
                failures.append(f"URL not 200: {url} ({code})")

    print(f"{len(skills)} skills, {len(urls)} ducpt.com URLs")
    for f in failures:
        print("FAIL", f)
    print("PASS" if not failures else f"{len(failures)} failures")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
