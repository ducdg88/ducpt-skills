#!/usr/bin/env python3
"""Validate Agent Skills (SKILL.md) against the agentskills.io spec.

Usage:
    python validate_skill.py PATH [PATH ...]

PATH may be a skill folder or a folder containing skill folders.
Exit code 1 on any error. Standard library only (tiny YAML subset parser).
"""
import os
import re
import sys

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SECRET_RES = [
    re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(r"AIza[0-9A-Za-z_\-]{30,}"),
]
LINK_RE = re.compile(r"\]\(([^)#\s]+)\)")


def parse_frontmatter(text):
    if not text.startswith("---"):
        return None, "missing YAML frontmatter (file must start with ---)"
    end = text.find("\n---", 3)
    if end == -1:
        return None, "frontmatter is not closed with ---"
    data, key = {}, None
    for line in text[3:end].splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        if line.startswith((" ", "\t")) and key:
            if isinstance(data.get(key), dict):
                k, _, v = line.strip().partition(":")
                data[key][k.strip()] = v.strip().strip("\"'")
            continue
        k, sep, v = line.partition(":")
        if not sep:
            return None, f"cannot parse frontmatter line: {line!r}"
        key, v = k.strip(), v.strip()
        data[key] = {} if v == "" else v.strip("\"'")
    return data, None


def validate_skill(folder):
    errors, warnings = [], []
    path = os.path.join(folder, "SKILL.md")
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    fm, err = parse_frontmatter(text)
    if err:
        return [err], warnings
    name = fm.get("name", "")
    desc = fm.get("description", "")
    if not name:
        errors.append("name is required")
    elif len(name) > 64 or not NAME_RE.match(name):
        errors.append(f"name '{name}' must be 1 to 64 chars of a-z, 0-9 and single hyphens")
    if name and name != os.path.basename(os.path.normpath(folder)):
        errors.append(f"name '{name}' must match folder '{os.path.basename(folder)}'")
    if not desc:
        errors.append("description is required")
    elif len(desc) > 1024:
        errors.append(f"description is {len(desc)} chars (max 1024)")
    elif len(desc) < 80:
        warnings.append("description is short; say what it does AND when to use it")
    if "compatibility" in fm and len(str(fm["compatibility"])) > 500:
        errors.append("compatibility is over 500 chars")
    if "metadata" in fm and not isinstance(fm["metadata"], dict):
        errors.append("metadata must be a key: value map")
    lines = text.count("\n") + 1
    if lines > 500:
        warnings.append(f"SKILL.md has {lines} lines; move detail to references/")
    for m in LINK_RE.finditer(text):
        target = m.group(1)
        if "://" in target or target.startswith("mailto:"):
            continue
        if not os.path.exists(os.path.join(folder, target)):
            errors.append(f"broken relative link: {target}")
    for root, _, files in os.walk(folder):
        for f in files:
            p = os.path.join(root, f)
            try:
                with open(p, encoding="utf-8") as fh:
                    body = fh.read()
            except (UnicodeDecodeError, OSError):
                continue
            for rx in SECRET_RES:
                if rx.search(body):
                    errors.append(f"possible secret in {os.path.relpath(p, folder)}")
                    break
    return errors, warnings


def find_skills(path):
    if os.path.isfile(os.path.join(path, "SKILL.md")):
        return [path]
    return sorted(os.path.join(path, d) for d in os.listdir(path)
                  if os.path.isfile(os.path.join(path, d, "SKILL.md")))


def main(argv):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if len(argv) < 2:
        sys.exit(__doc__)
    total_errors, count = 0, 0
    for p in argv[1:]:
        for skill in find_skills(p):
            count += 1
            errors, warnings = validate_skill(skill)
            status = "FAIL" if errors else "PASS"
            print(f"{status} {skill}")
            for e in errors:
                print(f"  ERROR {e}")
            for w in warnings:
                print(f"  WARN  {w}")
            total_errors += len(errors)
    if count == 0:
        sys.exit("No SKILL.md found.")
    print(f"\n{count} skills checked, {total_errors} errors")
    sys.exit(1 if total_errors else 0)


if __name__ == "__main__":
    main(sys.argv)
