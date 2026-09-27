#!/usr/bin/env python3
"""SEO checklist for a GitHub repo before/after it goes public. Read-only, standard library
only, uses the `gh` CLI already logged in. Never prints secret values.

    python repo_seo_check.py <repo>                  # ducdg88/<repo>
    python repo_seo_check.py <owner>/<repo>
    python repo_seo_check.py --all                   # every public, non-fork repo of ducdg88
    python repo_seo_check.py --all --skip repo1,repo2

Checks (from dg-deploy-checklist SKILL.md step 6, learned from a real gap on 27/09/2026:
13 public repos were missing these):
  1. Homepage is set in repo settings AND the URL answers HTTP 200 (no dead link in "About").
  2. Topics are set (warn only if none carry the brand, e.g. "ducpt").
  3. README exists and links back to ducpt.com with utm_source=github (skip via --skip-readme
     for policy/update-channel repos that are not meant to promote a product).
  4. Description is set (warn if very short).
Never invents a homepage URL: it only checks what is already set, and only calls it live.
"""
import argparse
import json
import subprocess
import sys
import urllib.request

DEFAULT_OWNER = "ducdg88"
RELEASE_CHANNEL_RE_SRC = r"(-releases?$|-updates?$|admin-updates$)"
import re as _re
RELEASE_CHANNEL_RE = _re.compile(RELEASE_CHANNEL_RE_SRC, _re.IGNORECASE)


def gh_json(*args):
    p = subprocess.run(["gh", "api"] + list(args), capture_output=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.decode("utf-8", "replace").strip())
    return json.loads(p.stdout.decode("utf-8"))


def url_status(url, timeout=15):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "dg-deploy-checklist/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status
    except urllib.error.HTTPError as ex:
        return ex.code
    except Exception as ex:  # noqa: BLE001
        return str(ex)


def check_repo(owner, repo, skip_readme=False):
    findings = []
    meta = gh_json(f"repos/{owner}/{repo}")
    full = f"{owner}/{repo}"

    homepage = (meta.get("homepage") or "").strip()
    if not homepage:
        findings.append(("FAIL", "homepage", "not set in repo settings"))
    else:
        status = url_status(homepage)
        if status == 200:
            findings.append(("PASS", "homepage", f"{homepage} -> 200"))
        else:
            findings.append(("FAIL", "homepage", f"{homepage} -> {status} (dead link in About box)"))

    topics = meta.get("topics") or []
    if not topics:
        findings.append(("FAIL", "topics", "none set"))
    elif "ducpt" not in [t.lower() for t in topics]:
        findings.append(("FAIL", "topics", f"{len(topics)} set, missing the required brand topic 'ducpt'"))
    else:
        findings.append(("PASS", "topics", f"{len(topics)} set, includes brand topic"))

    desc = (meta.get("description") or "").strip()
    if not desc:
        findings.append(("WARN", "description", "empty"))
    elif len(desc) < 20:
        findings.append(("WARN", "description", f"very short ({len(desc)} chars)"))
    else:
        findings.append(("PASS", "description", f"{len(desc)} chars"))

    private = bool(meta.get("private"))
    is_release_channel = bool(RELEASE_CHANNEL_RE.search(repo))
    is_profile = repo.lower() == owner.lower()
    license_exempt = (private or is_release_channel or is_profile
                      or repo in SKIP_README_DEFAULT or is_coursework(repo))
    if meta.get("license"):
        findings.append(("PASS", "license", meta["license"].get("spdx_id", "set")))
    elif license_exempt:
        why = ("private repo" if private else "release/update-channel repo" if is_release_channel
              else "profile repo" if is_profile else "policy/coursework repo, not distributable code")
        findings.append(("WARN", "license", f"not set ({why}, optional)"))
    else:
        findings.append(("FAIL", "license", "not set (public repo needs one, e.g. MIT)"))

    try:
        wf = gh_json(f"repos/{full}/contents/.github/workflows")
        yml = [f for f in wf if f["name"].endswith((".yml", ".yaml"))] if isinstance(wf, list) else []
        if yml:
            findings.append(("PASS", "ci", f"{len(yml)} workflow file(s)"))
        else:
            findings.append(("WARN", "ci", ".github/workflows exists but has no .yml file"))
    except RuntimeError:
        findings.append(("WARN", "ci", "no .github/workflows (optional, but real code repos usually have one)"))

    if skip_readme:
        findings.append(("SKIP", "readme", "policy/update-channel repo, --skip-readme"))
    else:
        try:
            import base64
            rd = gh_json(f"repos/{full}/contents/README.md")
            body = base64.b64decode(rd["content"]).decode("utf-8", "replace")
            has_link = "ducpt.com" in body
            has_utm = "utm_source=github" in body
            if has_link and has_utm:
                findings.append(("PASS", "readme", "links back to ducpt.com with utm_source=github"))
            elif has_link:
                findings.append(("WARN", "readme", "links to ducpt.com but no utm_source=github"))
            else:
                findings.append(("FAIL", "readme", "no ducpt.com link"))
        except RuntimeError as ex:
            msg = str(ex)
            if "Not Found" in msg or "repository is empty" in msg:
                findings.append(("FAIL", "readme", "missing (repo has no README.md)"))
            else:
                findings.append(("WARN", "readme", f"could not read ({msg[:80]})"))

    return findings


SECRET_PATTERNS = [
    r"sk-[A-Za-z0-9]{20,}", r"sb_secret_[A-Za-z0-9_-]{10,}", r"AKIA[0-9A-Z]{16}",
    r"ghp_[A-Za-z0-9]{20,}", r"github_pat_[A-Za-z0-9_]{20,}", r"xox[baprs]-[A-Za-z0-9-]{10,}",
    r"AIza[0-9A-Za-z_-]{20,}", r"-----BEGIN[ A-Z]*PRIVATE KEY-----",
]
TEXT_EXT = {".py", ".js", ".ts", ".json", ".md", ".txt", ".yml", ".yaml", ".env", ".sh", ".ps1"}


def scan_secrets(owner, repo, max_files=200, max_bytes=200_000):
    """Best-effort scan of the default branch's text files. Read-only, prints only file:line,
    never the matched value. For a real audit before making a repo public, prefer the full
    bto-secrets flow (checks git history too, not just the current tree)."""
    import base64
    import re
    tree = gh_json(f"repos/{owner}/{repo}/git/trees/HEAD?recursive=1")
    hits = []
    files = [f for f in tree.get("tree", []) if f["type"] == "blob"
            and any(f["path"].lower().endswith(e) for e in TEXT_EXT)][:max_files]
    for f in files:
        if f.get("size", 0) > max_bytes:
            continue
        try:
            blob = gh_json(f"repos/{owner}/{repo}/git/blobs/{f['sha']}")
            body = base64.b64decode(blob["content"]).decode("utf-8", "replace")
        except Exception:  # noqa: BLE001
            continue
        for pat in SECRET_PATTERNS:
            for m in re.finditer(pat, body):
                line = body.count("\n", 0, m.start()) + 1
                hits.append(f"{f['path']}:{line}")
    return hits


SKIP_README_DEFAULT = {
    "chinh-sach", "tab-cong-dong-ai-privacy", "youtube-hq-policy",
    "dg-image-tools-admin-updates", "dg-image-tools-updates",
}


def is_coursework(name):
    # Build to Own homework submissions (bto-01, bto-06-..., ...): real deliverables, not a
    # DUCPT product page. Homepage/topics still apply; do not force a promo footer into README.
    import re
    return bool(re.match(r"^bto-\d", name, re.IGNORECASE))


def list_public_repos(owner):
    repos = gh_json(f"users/{owner}/repos?per_page=100&type=public")
    return [r["name"] for r in repos if not r["fork"]]


def main():
    for s in (sys.stdout, sys.stderr):
        if hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repo", nargs="?", help="<repo> or <owner>/<repo>")
    ap.add_argument("--all", action="store_true", help=f"check every public repo of {DEFAULT_OWNER}")
    ap.add_argument("--skip", default="", help="comma-separated repo names to skip entirely")
    ap.add_argument("--skip-readme", default=",".join(sorted(SKIP_README_DEFAULT)),
                    help="comma-separated repo names where the README ducpt.com check is skipped")
    ap.add_argument("--scan-secrets", action="store_true",
                    help="also scan the default branch's text files for secret-shaped strings (slower, opt-in)")
    a = ap.parse_args()
    skip = {s for s in a.skip.split(",") if s}
    skip_readme = {s for s in a.skip_readme.split(",") if s}

    if a.all:
        targets = [(DEFAULT_OWNER, r) for r in list_public_repos(DEFAULT_OWNER) if r not in skip]
        skip_readme |= {r for _, r in targets if is_coursework(r)}
    elif a.repo:
        owner, _, name = a.repo.partition("/")
        targets = [(owner, name) if name else (DEFAULT_OWNER, owner)]
    else:
        sys.exit(__doc__)

    total_fail = 0
    for owner, repo in targets:
        print(f"=== {owner}/{repo} ===")
        try:
            findings = check_repo(owner, repo, skip_readme=repo in skip_readme)
        except RuntimeError as ex:
            print(f"  ERROR could not read repo: {ex}")
            total_fail += 1
            continue
        if a.scan_secrets:
            hits = scan_secrets(owner, repo)
            findings.append(("FAIL" if hits else "PASS", "secrets",
                            f"{len(hits)} possible match(es): {', '.join(hits[:5])}" if hits
                            else "no secret-shaped string in tracked text files"))
        for level, item, detail in findings:
            print(f"  {level:<4} {item:<12} {detail}")
            if level == "FAIL":
                total_fail += 1
    print(f"\n{len(targets)} repo(s) checked, {total_fail} FAIL")
    sys.exit(1 if total_fail else 0)


if __name__ == "__main__":
    main()
