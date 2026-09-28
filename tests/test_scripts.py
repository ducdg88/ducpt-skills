"""Tests for the bundled skill scripts. Run: python -m unittest discover -s tests"""
import csv
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = os.path.join(ROOT, "tests", "fixtures")


def load(skill, script):
    path = os.path.join(ROOT, "skills", skill, "scripts", script)
    spec = importlib.util.spec_from_file_location(script[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_script(skill, script, *args):
    path = os.path.join(ROOT, "skills", skill, "scripts", script)
    return subprocess.run([sys.executable, path, *args], capture_output=True, text=True, encoding="utf-8")


class CleanSubs(unittest.TestCase):
    def setUp(self):
        self.mod = load("vietnamese-transcript-cleaner", "clean_subs.py")

    def test_srt_merges_and_keeps_timestamps(self):
        out = run_script("vietnamese-transcript-cleaner", "clean_subs.py", os.path.join(FIX, "sample.srt"))
        self.assertEqual(out.returncode, 0, out.stderr)
        paras = [p for p in out.stdout.split("\n\n") if p.strip()]
        self.assertEqual(len(paras), 2)  # 5 second silence splits into 2 paragraphs
        self.assertTrue(paras[0].startswith("[00:00:01] xin chào cả nhà"))
        self.assertTrue(paras[1].startswith("[00:00:12]"))
        self.assertNotIn("<i>", out.stdout)

    def test_vtt_rolling_captions_deduped(self):
        out = run_script("vietnamese-transcript-cleaner", "clean_subs.py", os.path.join(FIX, "sample.vtt"))
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(out.stdout.count("hôm nay mình"), 1)
        self.assertIn("nói về skill", out.stdout)

    def test_not_a_caption_file(self):
        out = run_script("vietnamese-transcript-cleaner", "clean_subs.py", os.path.join(ROOT, "LICENSE"))
        self.assertNotEqual(out.returncode, 0)


class PinCsv(unittest.TestCase):
    def test_valid_pins_write_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            dst = os.path.join(tmp, "pins.csv")
            out = run_script("pinterest-pin-writer", "make_pin_csv.py", os.path.join(FIX, "pins_ok.json"), dst)
            self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
            with open(dst, encoding="utf-8") as fh:
                rows = list(csv.reader(fh))
            self.assertEqual(rows[0][0], "Title")
            self.assertEqual(len(rows), 3)
            self.assertIn("utm_source=pinterest", rows[1][5])

    def test_too_long_title_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = os.path.join(tmp, "bad.json")
            with open(bad, "w", encoding="utf-8") as fh:
                json.dump([{"title": "x" * 101, "board": "b", "media_url": "https://a.b/c.jpg",
                            "link": "https://a.b/?utm_source=pinterest"}], fh)
            out = run_script("pinterest-pin-writer", "make_pin_csv.py", bad, os.path.join(tmp, "o.csv"))
            self.assertEqual(out.returncode, 1)
            self.assertIn("title is 101 chars", out.stdout)
            self.assertFalse(os.path.exists(os.path.join(tmp, "o.csv")))


class FindDupes(unittest.TestCase):
    def setUp(self):
        self.mod = load("windows-duplicate-cleanup", "find_dupes.py")
        self.tmp = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.tmp, "a", "deep"))
        for p, data in [("one.bin", b"A" * 5000), ("a/deep/one_copy.bin", b"A" * 5000),
                        ("a/two.bin", b"B" * 5000), ("small.txt", b"hi")]:
            with open(os.path.join(self.tmp, p), "wb") as fh:
                fh.write(data)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_dry_run_changes_nothing(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.mod.main([self.tmp, "--min-size", "1KB"])
        self.assertIn("1 duplicate groups", buf.getvalue())
        self.assertTrue(os.path.exists(os.path.join(self.tmp, "a", "deep", "one_copy.bin")))

    def test_keep_shortest_path_and_move(self):
        q = os.path.join(self.tmp, "_q")
        with redirect_stdout(io.StringIO()):
            self.mod.main([self.tmp, "--min-size", "1KB", "--move-to", q])
        self.assertTrue(os.path.exists(os.path.join(self.tmp, "one.bin")))
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "a", "deep", "one_copy.bin")))
        self.assertTrue(os.path.exists(os.path.join(q, "a", "deep", "one_copy.bin")))
        with open(os.path.join(q, "moves.csv"), encoding="utf-8") as fh:
            self.assertEqual(len(list(csv.reader(fh))), 2)
        # second run must not treat the quarantine copy as a new duplicate
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.mod.main([self.tmp, "--min-size", "1KB", "--move-to", q])
        self.assertIn("0 duplicate groups", buf.getvalue())

    def test_refuses_drive_root(self):
        self.assertTrue(self.mod.is_forbidden_root(os.path.abspath(os.sep)))
        self.assertFalse(self.mod.is_forbidden_root(self.tmp))


class CheckCopy(unittest.TestCase):
    def setUp(self):
        self.mod = load("vietnamese-copy-polish", "check_copy.py")

    def test_dash_is_error(self):
        errors, _, _ = self.mod.lint("Mình làm skill " + chr(0x2014) + " rất hay. Comment \"1\" nhé.", "tiktok")
        self.assertEqual(len(errors), 1)

    def test_hyphen_in_word_is_fine(self):
        errors, _, _ = self.mod.lint("Bàn gỗ live-edge đẹp lắm. Nhắn mình để nhận giá.", "tiktok")
        self.assertEqual(errors, [])

    def test_missing_diacritics_warned(self):
        _, warnings, _ = self.mod.lint("hom nay minh se huong dan ban cach lam ban go dep " * 3, "tiktok")
        self.assertTrue(any("diacritics" in w for w in warnings))

    def test_missing_cta_warned(self):
        _, warnings, _ = self.mod.lint("Hôm nay trời đẹp quá.", "facebook")
        self.assertTrue(any("call to action" in w for w in warnings))


class ScoreTitles(unittest.TestCase):
    def setUp(self):
        self.mod = load("youtube-title-lab", "score_titles.py")

    def test_good_beats_bad(self):
        good, _ = self.mod.score("7 Woodworking Mistakes Beginners Make (and the Fix)", "woodworking", "en")
        bad, _ = self.mod.score("AMAZING VIDEO YOU WON'T BELIEVE!!!", "woodworking", "en")
        self.assertGreater(good, bad + 30)

    def test_vietnamese_keyword_position(self):
        early, _ = self.mod.score("Bàn gỗ nguyên tấm: 5 sai lầm khi chọn mua", "bàn gỗ", "vi")
        late, _ = self.mod.score("5 sai lầm khi chọn mua cho phòng khách: bàn gỗ", "bàn gỗ", "vi")
        self.assertGreater(early, late)

    def test_score_bounds(self):
        for t in ["", "a" * 200, "1 2 3"]:
            pts, _ = self.mod.score(t, "", "en")
            self.assertTrue(0 <= pts <= 100)


class Streak(unittest.TestCase):
    def setUp(self):
        self.mod = load("github-commit-streak", "streak.py")
        import datetime as dt
        self.dt = dt

    def days(self, counts, end):
        start = end - self.dt.timedelta(days=len(counts) - 1)
        return [{"date": (start + self.dt.timedelta(days=i)).isoformat(), "contributionCount": c}
                for i, c in enumerate(counts)]

    def test_open_today_does_not_break_streak(self):
        today = self.dt.date(2026, 9, 26)
        current, longest, _, today_count = self.mod.streaks(self.days([0, 1, 2, 3, 0], today), today)
        self.assertEqual((current, longest, today_count), (3, 3, 0))

    def test_gap_resets(self):
        today = self.dt.date(2026, 9, 26)
        current, longest, zero30, _ = self.mod.streaks(self.days([1, 1, 1, 1, 0, 1, 1], today), today)
        self.assertEqual((current, longest, zero30), (2, 4, 1))

    def test_per_day_uses_closed_days_only(self):
        today = self.dt.date(2026, 9, 29)
        counts = [0] * 23 + [17, 13, 9, 34, 52, 88, 73, 120, 5]
        d = self.mod.per_day(self.days(counts, today), today, 100)
        self.assertEqual(d["today_provisional"], 5)
        self.assertEqual([x["count"] for x in d["last_7"]], [13, 9, 34, 52, 88, 73, 120])
        self.assertEqual(d["avg_7"], 55.6)
        self.assertEqual(d["days_at_target_30"], 1)
        self.assertEqual(d["zero_days_7"], 0)
        self.assertEqual(d["zero_days_30"], 22)
        self.assertEqual(d["window_30"], ["2026-08-30", "2026-09-28"])

    def test_needed_per_day_ignores_contributions_that_slide_out(self):
        today = self.dt.date(2026, 9, 28)
        by = self.dt.date(2027, 9, 28)
        days = self.days([500] + [0] * 364, today)  # all of it will leave the window
        self.assertEqual(self.mod.needed_per_day(days, today, 36500, by), 100.0)
        near = self.dt.date(2026, 10, 8)  # 10 days out: last year's work mostly still counts
        days = self.days([10] * 365, today)
        self.assertEqual(self.mod.needed_per_day(days, today, 3650, near), 10.0)

    def test_avg_per_day_starts_at_account_creation(self):
        today = self.dt.date(2026, 9, 28)
        self.assertEqual(self.mod.avg_per_day(238, today, self.dt.date(2026, 2, 3)), 1.0)
        self.assertEqual(self.mod.avg_per_day(365, today, self.dt.date(2020, 1, 1)), 1.0)


class Validator(unittest.TestCase):
    def setUp(self):
        self.mod = load("skill-distribution-kit", "validate_skill.py")
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def make(self, folder, fm, body="Body"):
        path = os.path.join(self.tmp, folder)
        os.makedirs(path)
        with open(os.path.join(path, "SKILL.md"), "w", encoding="utf-8") as fh:
            fh.write(f"---\n{fm}\n---\n{body}\n")
        return path

    def test_all_repo_skills_pass(self):
        for skill in self.mod.find_skills(os.path.join(ROOT, "skills")):
            errors, _ = self.mod.validate_skill(skill)
            self.assertEqual(errors, [], skill)

    def test_bad_name_and_mismatch(self):
        p = self.make("good-name", "name: Bad--Name\ndescription: " + "d" * 100)
        errors, _ = self.mod.validate_skill(p)
        self.assertTrue(any("must be 1 to 64" in e for e in errors))
        self.assertTrue(any("must match folder" in e for e in errors))

    def test_secret_and_broken_link(self):
        p = self.make("leaky", "name: leaky\ndescription: " + "d" * 100,
                      "See [x](references/missing.md). api_key = 'abcdefghijklmnopqrstuvwxyz123456'")
        errors, _ = self.mod.validate_skill(p)
        self.assertTrue(any("broken relative link" in e for e in errors))
        self.assertTrue(any("possible secret" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
