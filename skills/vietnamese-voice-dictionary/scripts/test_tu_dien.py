"""Kiem thu tu_dien.py tren du lieu tam. Chay: python test_tu_dien.py"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import tu_dien  # noqa: E402

SEED = HERE.parent / "data" / "dictionary.json"


class TestTuDien(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()) / "td.json"
        self.tmp.write_text(SEED.read_text(encoding="utf-8"), encoding="utf-8")
        self.db = tu_dien.load(self.tmp)

    def test_tu_sua(self):
        r = tu_dien.sua("Mở ghiếp H rồi kiểm tra sở kêu và plackin", self.db)
        self.assertEqual(r["van_ban_da_sua"], "Mở GitHub rồi kiểm tra skill và plugin")
        self.assertEqual(len(r["da_sua"]), 3)

    def test_khong_sua_giua_tu(self):
        r = tu_dien.sua("sở kêuxyz và tiền sở kêu", self.db)
        self.assertEqual(r["van_ban_da_sua"], "sở kêuxyz và tiền skill")

    def test_khong_phan_biet_hoa_thuong(self):
        self.assertEqual(tu_dien.sua("GHIẾP h", self.db)["van_ban_da_sua"], "GitHub")

    def test_tu_that_chi_goi_y(self):
        r = tu_dien.sua("viết câu lệnh SQL cho tôi", self.db)
        self.assertEqual(r["van_ban_da_sua"], "viết câu lệnh SQL cho tôi")
        self.assertEqual(r["da_sua"], [])
        self.assertEqual(r["goi_y"][0][1], "skill")

    def test_hoc_moi_roi_lan_sau_tu_sua(self):
        self.assertEqual(tu_dien.sua("cái ô tu này", self.db)["da_sua"], [])
        tu_dien.hoc("ô tu", "auto", path=self.tmp)
        r = tu_dien.sua("cái ô tu này", tu_dien.load(self.tmp))
        self.assertEqual(r["van_ban_da_sua"], "cái auto này")

    def test_hoc_lai_tang_dem_va_ghi_de(self):
        tu_dien.hoc("ô tu", "auto", path=self.tmp)
        m = tu_dien.hoc("ô tu", "tự động", path=self.tmp)
        self.assertEqual(m["so_lan"], 2)
        self.assertEqual(m["dung"], "tự động")
        self.assertIn("auto", m["ghi_chu"])
        self.assertEqual(sum(1 for x in tu_dien.load(self.tmp)["muc"] if x["sai"] == "ô tu"), 1)

    def test_tu_ngan_mac_dinh_chi_goi_y(self):
        m = tu_dien.hoc("bô", "bot", path=self.tmp)
        self.assertFalse(m["chac"])
        m2 = tu_dien.hoc("bô", "bot", ep=True, path=self.tmp)
        self.assertTrue(m2["chac"])

    def test_tu_choi_dau_vao_xau(self):
        for sai, dung in (("", "x"), ("abc", ""), ("abc", "ABC"), ("a" * 61, "b")):
            with self.assertRaises(ValueError):
                tu_dien.hoc(sai, dung, path=self.tmp)

    def test_xoa(self):
        self.assertEqual(tu_dien.xoa("sở kêu", path=self.tmp), 1)
        self.assertEqual(tu_dien.sua("sở kêu", tu_dien.load(self.tmp))["da_sua"], [])

    def test_cum_dai_thang_cum_ngan(self):
        db = {"muc": [{"sai": "plug", "dung": "X", "chac": True}, {"sai": "plug gain", "dung": "plugin", "chac": True}]}
        self.assertEqual(tu_dien.sua("cài plug gain", db)["van_ban_da_sua"], "cài plugin")

    def test_hook(self):
        hook = HERE / "hook_userprompt.py"
        env = {**os.environ, "HIEU_GIONG_NOI_DATA": str(self.tmp), "PYTHONIOENCODING": "utf-8"}
        inp = json.dumps({"prompt": "mở ghiếp H và sở kêu"}, ensure_ascii=False)
        p = subprocess.run([sys.executable, str(hook)], input=inp.encode("utf-8"), capture_output=True, env=env)
        out = json.loads(p.stdout.decode("utf-8"))
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "UserPromptSubmit")
        self.assertIn("GitHub", out["hookSpecificOutput"]["additionalContext"])
        # khong co gi de sua: im lang
        p = subprocess.run([sys.executable, str(hook)], input=json.dumps({"prompt": "xin chào"}).encode(),
                           capture_output=True, env=env)
        self.assertEqual(p.stdout, b"")
        # dau vao hong: im lang, khong loi
        p = subprocess.run([sys.executable, str(hook)], input=b"{khong phai json", capture_output=True, env=env)
        self.assertEqual((p.returncode, p.stdout), (0, b""))


if __name__ == "__main__":
    unittest.main(verbosity=2)
