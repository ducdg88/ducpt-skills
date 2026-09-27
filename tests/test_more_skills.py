"""Tests for token-budget-guard and ai-kickstart-7-days (standard library only)."""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(rel, name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TokenBudget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tb = load("skills/token-budget-guard/scripts/token_budget.py", "token_budget")

    def write(self, records):
        f = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8")
        for r in records:
            f.write(json.dumps(r) + "\n")
        f.close()
        return f.name

    def test_finds_usage_nested_under_message(self):
        log = self.write([
            {"type": "assistant", "message": {"model": "claude-opus-4-5",
             "usage": {"input_tokens": 1000, "output_tokens": 200,
                       "cache_creation_input_tokens": 0, "cache_read_input_tokens": 800}}},
            {"type": "assistant", "message": {"model": "claude-opus-4-5",
             "usage": {"input_tokens": 500, "output_tokens": 100,
                       "cache_creation_input_tokens": 0, "cache_read_input_tokens": 400}}},
        ])
        totals = self.tb.collect([log])
        self.assertEqual(set(totals), {"claude-opus-4-5"})
        u = totals["claude-opus-4-5"]
        self.assertEqual((u["input_tokens"], u["output_tokens"], u["cache_read_input_tokens"]), (1500, 300, 1200))

    def test_cache_hit_ratio(self):
        totals = {"m": {"input_tokens": 200, "output_tokens": 0,
                        "cache_creation_input_tokens": 0, "cache_read_input_tokens": 800}}
        report = self.tb.build_report(totals, {})
        self.assertAlmostEqual(report["models"][0]["cache_hit_ratio"], 0.8)

    def test_no_prices_means_no_cost(self):
        totals = {"m": {"input_tokens": 1_000_000, "output_tokens": 0,
                        "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}}
        report = self.tb.build_report(totals, {})
        self.assertIsNone(report["models"][0]["cost_usd"])
        self.assertIsNone(report["total_cost_usd"])

    def test_cost_computed_from_given_prices(self):
        totals = {"m": {"input_tokens": 1_000_000, "output_tokens": 1_000_000,
                        "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}}
        report = self.tb.build_report(totals, {"m": {"input": 3.0, "output": 15.0}})
        self.assertAlmostEqual(report["models"][0]["cost_usd"], 18.0)
        self.assertAlmostEqual(report["total_cost_usd"], 18.0)

    def test_missing_price_for_one_model_excluded_from_total(self):
        totals = {"priced": {"input_tokens": 1_000_000, "output_tokens": 0,
                             "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0},
                  "unpriced": {"input_tokens": 1_000_000, "output_tokens": 0,
                              "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}}
        report = self.tb.build_report(totals, {"priced": {"input": 1.0, "output": 1.0}})
        self.assertEqual(report["models_missing_price"], ["unpriced"])
        self.assertAlmostEqual(report["total_cost_usd"], 1.0)

    def test_guard_exits_1_when_over_budget(self):
        script = os.path.join(ROOT, "skills", "token-budget-guard", "scripts", "token_budget.py")
        log = self.write([{"model": "m", "usage": {"input_tokens": 1_000_000, "output_tokens": 0}}])
        prices = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        json.dump({"m": {"input": 10.0, "output": 0.0}}, prices)
        prices.close()
        r = subprocess.run([sys.executable, script, "guard", log, "--prices", prices.name, "--budget-usd", "1"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        r2 = subprocess.run([sys.executable, script, "guard", log, "--prices", prices.name, "--budget-usd", "100"],
                            capture_output=True, text=True)
        self.assertEqual(r2.returncode, 0)

    def test_bad_json_line_is_a_clear_error_not_a_crash(self):
        f = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8")
        f.write("{not json\n")
        f.close()
        with self.assertRaises(SystemExit):
            self.tb.collect([f.name])


class AiKickstart(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tr = load("skills/ai-kickstart-7-days/scripts/track.py", "track")

    def setUp(self):
        self.path = os.path.join(tempfile.mkdtemp(), "plan.json")

    def test_init_creates_7_undone_days(self):
        plan = self.tr.new_plan("quán trà sữa", "trả lời tin nhắn khách")
        self.assertEqual(len(plan["days"]), 7)
        self.assertTrue(all(not v["done"] for v in plan["days"].values()))

    def test_done_and_status(self):
        self.tr.save(self.path, self.tr.new_plan("quán trà sữa", "trả lời tin nhắn"))
        plan = self.tr.load(self.path)
        plan["days"]["1"] = {"done": True, "note": "xong", "date": "2026-09-27"}
        self.tr.save(self.path, plan)
        s = self.tr.status_data(self.tr.load(self.path))
        self.assertEqual(s["done_count"], 1)
        self.assertEqual(s["next_day"], 2)
        self.assertFalse(s["finished"])

    def test_all_done_is_finished(self):
        plan = self.tr.new_plan("b", "p")
        for d in range(1, 8):
            plan["days"][str(d)]["done"] = True
        s = self.tr.status_data(plan)
        self.assertTrue(s["finished"])
        self.assertIsNone(s["next_day"])

    def test_init_refuses_to_overwrite_without_force(self):
        self.tr.save(self.path, self.tr.new_plan("a", "b"))
        script = os.path.join(ROOT, "skills", "ai-kickstart-7-days", "scripts", "track.py")
        r = subprocess.run([sys.executable, script, "init", self.path, "--business", "x", "--pain", "y"],
                           capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)

    def test_day_out_of_range_rejected(self):
        script = os.path.join(ROOT, "skills", "ai-kickstart-7-days", "scripts", "track.py")
        self.tr.save(self.path, self.tr.new_plan("a", "b"))
        r = subprocess.run([sys.executable, script, "done", self.path, "8"], capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
