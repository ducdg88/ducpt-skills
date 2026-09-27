#!/usr/bin/env python3
"""Read local Claude Code / Claude API usage logs, report tokens and cost, warn before over budget.

Runs fully offline, reads only files already on disk, never calls a paid API.

    python token_budget.py report session.jsonl [more.jsonl ...] [--prices prices.json] [--json]
    python token_budget.py guard session.jsonl --budget-usd 5 [--prices prices.json] [--strict]

Input: one JSON object per line (JSONL), or a JSON array. Any dict with a "usage" object
containing *_tokens fields is counted; the nearest sibling "model" key (if any) is used to
label it, else "unknown". This matches Claude API / Claude Code transcript shape:
{"message": {"model": "...", "usage": {"input_tokens": 1, "output_tokens": 2, ...}}}
A log in a different shape may find 0 events; check with --json to see what was read.

Prices are never guessed. Without --prices, cost is not computed, only token counts.
prices.json: {"<model>": {"input": USD_per_1M, "output": USD_per_1M,
"cache_write": USD_per_1M, "cache_read": USD_per_1M}}. Read the current numbers from the
provider's own pricing page before filling this in; a stale or wrong number here gives a
wrong budget check. See data/prices.example.json for the shape, not real prices.
"""
import argparse
import json
import sys
from pathlib import Path

TOKEN_FIELDS = ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")
PRICE_KEY = {"input_tokens": "input", "output_tokens": "output",
             "cache_creation_input_tokens": "cache_write", "cache_read_input_tokens": "cache_read"}


def find_usage_events(obj, model=None):
    """Walk any nested dict/list, yield (model, usage_dict) for every *_tokens bundle found."""
    events = []
    if isinstance(obj, dict):
        here = obj.get("model", model)
        usage = obj.get("usage")
        counted_usage = False
        if isinstance(usage, dict) and any(k in usage for k in TOKEN_FIELDS):
            events.append((here or "unknown", usage))
            counted_usage = True
        elif any(k in obj for k in TOKEN_FIELDS):
            events.append((here or "unknown", obj))
        for k, v in obj.items():
            if counted_usage and k == "usage":
                continue  # already counted this exact usage object, do not double count it
            events += find_usage_events(v, here)
    elif isinstance(obj, list):
        for v in obj:
            events += find_usage_events(v, model)
    return events


def read_records(path):
    text = Path(path).read_text(encoding="utf-8-sig")
    stripped = text.strip()
    if stripped.startswith("["):
        return json.loads(stripped)
    records = []
    for n, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as ex:
            raise SystemExit(f"{path}:{n}: not valid JSON ({ex})")
    return records


def collect(paths):
    """Return {model: {field: total_tokens}} across every file."""
    totals = {}
    for p in paths:
        for rec in read_records(p):
            for model, usage in find_usage_events(rec):
                bucket = totals.setdefault(model, {f: 0 for f in TOKEN_FIELDS})
                for f in TOKEN_FIELDS:
                    bucket[f] += int(usage.get(f) or 0)
    return totals


def load_prices(path):
    if not path:
        return {}
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def model_cost(usage, price):
    """Cost in USD for one model's totals, or None if any needed price is missing."""
    if price is None:
        return None
    total = 0.0
    for field in TOKEN_FIELDS:
        n = usage.get(field, 0)
        if n == 0:
            continue
        key = PRICE_KEY[field]
        if key not in price:
            return None
        total += n / 1_000_000 * price[key]
    return total


def build_report(totals, prices):
    rows, total_cost, missing_price = [], 0.0, []
    for model in sorted(totals):
        usage = totals[model]
        cost = model_cost(usage, prices.get(model))
        if cost is None and prices:
            missing_price.append(model)
        elif cost is not None:
            total_cost += cost
        cache_in = usage["input_tokens"] + usage["cache_read_input_tokens"]
        cache_hit = (usage["cache_read_input_tokens"] / cache_in) if cache_in else None
        rows.append({"model": model, **usage, "cache_hit_ratio": cache_hit, "cost_usd": cost})
    return {"models": rows, "total_cost_usd": (total_cost if prices else None),
            "models_missing_price": missing_price}


def render(report, budget=None):
    lines = []
    for r in report["models"]:
        cache = "%.0f%%" % (r["cache_hit_ratio"] * 100) if r["cache_hit_ratio"] is not None else "n/a"
        cost = ("$%.4f" % r["cost_usd"]) if r["cost_usd"] is not None else "no price"
        lines.append("  %-28s in=%-8d out=%-8d cache_write=%-7d cache_read=%-8d cache_hit=%-5s cost=%s" % (
            r["model"], r["input_tokens"], r["output_tokens"], r["cache_creation_input_tokens"],
            r["cache_read_input_tokens"], cache, cost))
    if report["models_missing_price"]:
        lines.append("  no price given for: %s (not counted in total)" % ", ".join(report["models_missing_price"]))
    if report["total_cost_usd"] is not None:
        lines.append("  TOTAL (priced models only): $%.4f" % report["total_cost_usd"])
        if budget is not None:
            over = report["total_cost_usd"] - budget
            lines.append(("  OVER budget by $%.4f" % over) if over > 0 else
                         ("  within budget, $%.4f left" % -over))
    else:
        lines.append("  No --prices given: token counts only, no cost estimate.")
    return "\n".join(lines) if lines else "  No usage events found in the given files."


def cmd_report(a):
    totals = collect(a.paths)
    report = build_report(totals, load_prices(a.prices))
    if a.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render(report))


def cmd_guard(a):
    totals = collect(a.paths)
    prices = load_prices(a.prices)
    if not prices:
        raise SystemExit("guard needs --prices (a budget cannot be checked without cost).")
    report = build_report(totals, prices)
    print(render(report, budget=a.budget_usd))
    if report["total_cost_usd"] is None:
        sys.exit(1)
    over = report["total_cost_usd"] > a.budget_usd
    missing = bool(report["models_missing_price"])
    if over or (a.strict and missing):
        sys.exit(1)


def main():
    for s in (sys.stdout, sys.stderr):
        if hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("report", help="Token counts and cost by model")
    r.add_argument("paths", nargs="+")
    r.add_argument("--prices")
    r.add_argument("--json", action="store_true")
    r.set_defaults(func=cmd_report)

    g = sub.add_parser("guard", help="Exit 1 when over budget (for use as a gate)")
    g.add_argument("paths", nargs="+")
    g.add_argument("--prices", required=True)
    g.add_argument("--budget-usd", type=float, required=True)
    g.add_argument("--strict", action="store_true", help="Also fail when a model has no price on file")
    g.set_defaults(func=cmd_guard)

    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
