"""Tests for vietnamese-voice-dictionary and content-originality-check (standard library only)."""
import importlib.util
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(rel, name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TitlePattern(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tp = load("skills/content-originality-check/scripts/title_pattern.py", "title_pattern")

    def test_templated_titles_are_high(self):
        titles = ["Bạn không tin nổi cảnh này số %d" % i for i in range(1, 7)]
        self.assertEqual(self.tp.analyse(titles)["muc"], "cao")

    def test_varied_titles_are_low(self):
        titles = ["Cách mình sửa chiếc ghế gỗ gãy chân trong 20 phút", "Vì sao xe tải hay lật ở khúc cua đèo",
                  "Review thật sau 3 tháng dùng máy cưa cầm tay", "Hỏi đáp: kênh mới có nên bật kiếm tiền sớm không",
                  "Một ngày làm việc ở xưởng mộc nhỏ", "Lỗi hay gặp khi phơi gỗ ngoài trời"]
        self.assertEqual(self.tp.analyse(titles)["muc"], "thap")

    def test_too_few_titles(self):
        self.assertEqual(self.tp.analyse(["a b c", "d e f"])["muc"], "chua_du_mau")
        self.assertEqual(self.tp.analyse(["only one"])["muc"], "chua_du_mau")
        self.assertEqual(self.tp.analyse([])["muc"], "chua_du_mau")

    def test_blank_lines_ignored(self):
        self.assertEqual(self.tp.analyse(["", "  ", "x y"])["so_tieu_de"], 1)


class VoiceDictionary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.td = load("skills/vietnamese-voice-dictionary/scripts/tu_dien.py", "tu_dien")
        seed = os.path.join(ROOT, "skills", "vietnamese-voice-dictionary", "data", "dictionary.json")
        cls.db = cls.td.load(seed)

    def test_fixes_known_words(self):
        r = self.td.sua("mở ghiếp H rồi cài plackin", self.db)
        self.assertEqual(r["van_ban_da_sua"], "mở GitHub rồi cài plugin")

    def test_real_words_are_only_hints(self):
        r = self.td.sua("viết câu SQL", self.db)
        self.assertEqual(r["van_ban_da_sua"], "viết câu SQL")
        self.assertEqual(r["da_sua"], [])
        self.assertTrue(r["goi_y"])

    def test_starter_data_has_no_private_fields(self):
        for m in self.db["muc"]:
            self.assertLessEqual(len(m["sai"]), 60)
            self.assertNotIn("chi_claude", m)


class BuildSiteLlms(unittest.TestCase):
    """build_site.py must add missing skills to an existing llms.txt section and keep CRLF."""

    def setUp(self):
        import tempfile
        self.bs = load("scripts/build_site.py", "build_site")
        self.site = tempfile.mkdtemp()
        with open(os.path.join(self.site, "sitemap.xml"), "w", encoding="utf-8", newline="") as fh:
            fh.write('<?xml version="1.0"?><urlset></urlset>')

    def write_llms(self, text):
        with open(os.path.join(self.site, "llms.txt"), "w", encoding="utf-8", newline="") as fh:
            fh.write(text)

    def read_llms(self):
        with open(os.path.join(self.site, "llms.txt"), encoding="utf-8", newline="") as fh:
            return fh.read()

    def old_section(self, nl):
        old = ["github-commit-streak", "knowledge-mindmap", "one-person-company-ai"]
        lines = ["# Site", "", "## Agent Skills", "", "- Hub: https://ducpt.com/skills/"]
        lines += ["- x: https://ducpt.com/skills/%s/" % n for n in old]
        lines += ["", "## Citation Guidance", "", "Cite the official page."]
        return nl.join(lines) + nl

    def test_adds_missing_skills_and_keeps_crlf(self):
        self.write_llms(self.old_section("\r\n"))
        self.bs.build(self.site)
        text = self.read_llms()
        for name in ("content-originality-check", "vietnamese-voice-dictionary", "youtube-title-lab"):
            self.assertIn("https://ducpt.com/skills/%s/" % name, text)
        self.assertEqual(text.count("\r\n"), text.count("\n"), "mixed line endings")
        self.assertLess(text.index("skills/vietnamese-voice-dictionary/"), text.index("## Citation Guidance"))

    def test_second_run_changes_nothing(self):
        self.write_llms(self.old_section("\n"))
        self.bs.build(self.site)
        first = self.read_llms()
        self.bs.build(self.site)
        self.assertEqual(self.read_llms(), first)
        self.assertNotIn("\r", first)


class SeoLengths(unittest.TestCase):
    def test_titles_and_descriptions_fit_search_results(self):
        import json
        with open(os.path.join(ROOT, "data", "site.json"), encoding="utf-8") as fh:
            cfg = json.load(fh)
        suffix = " · Agent Skill miễn phí · DUCPT"
        for name, meta in cfg["skills"].items():
            self.assertLessEqual(len(meta["title"] + suffix), 65, name)
            self.assertLessEqual(len(meta["summary"]), 165, name)
            self.assertGreaterEqual(len(meta["summary"]), 110, name)


if __name__ == "__main__":
    unittest.main()
