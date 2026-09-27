"""Tu dien sua loi giong noi (voice-to-text) cua Founder. Nho tu nghe nham, lan sau tu sua.

    python tu_dien.py sua "mo ghiep H roi kiem tra so ke"   # ap tu dien, in ban da sua + danh sach thay
    python tu_dien.py sua "..." --json                       # in JSON de may doc
    python tu_dien.py hoc "so ke" "skill"                    # nho: nghe la "so ke" thi hieu la "skill"
    python tu_dien.py hoc "sq" "skill" --nhap-nhang          # tu ngan / tu that de nham: chi goi y, khong tu sua
    python tu_dien.py xem                                    # liet ke
    python tu_dien.py xoa "so ke"                            # bo mot muc

Du lieu: data/dictionary.json canh thu muc scripts (doi bang bien moi truong HIEU_GIONG_NOI_DATA).
Chi luu tu vung, KHONG luu noi dung cuoc tro chuyen.
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
import tempfile
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = Path(os.environ.get("HIEU_GIONG_NOI_DATA") or (HERE.parent / "data" / "dictionary.json"))
MAX_LEN = 60
SHORT = 3  # tu <= 3 ky tu de trung tu that: mac dinh chi goi y


def norm(s):
    return unicodedata.normalize("NFC", (s or "").strip()).casefold()


def load(path=None):
    p = Path(path or DATA)
    if not p.exists():
        return {"phien_ban": 1, "muc": []}
    return json.loads(p.read_text(encoding="utf-8-sig"))


def save(db, path=None):
    p = Path(path or DATA)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(p.parent), suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(db, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    os.replace(tmp, p)


def _pattern(words):
    alts = sorted({re.escape(w) for w in words}, key=len, reverse=True)
    return re.compile(r"(?<!\w)(?:%s)(?!\w)" % "|".join(alts), re.IGNORECASE | re.UNICODE) if alts else None


def sua(text, db=None):
    """Tra ve dict: van_ban_da_sua, da_sua [(sai, dung)], goi_y [(sai, dung)]."""
    db = db or load()
    text = unicodedata.normalize("NFC", text or "")
    auto = {norm(m["sai"]): m for m in db["muc"] if m.get("chac")}
    hint = {norm(m["sai"]): m for m in db["muc"] if not m.get("chac")}
    done = []

    def rep(mt):
        m = auto[norm(mt.group(0))]
        done.append((mt.group(0), m["dung"]))
        return m["dung"]

    pat = _pattern(auto)
    out = pat.sub(rep, text) if pat else text
    hints, seen = [], set()
    hp = _pattern(hint)
    if hp:
        for mt in hp.finditer(out):
            k = norm(mt.group(0))
            if k not in seen:
                seen.add(k)
                hints.append((mt.group(0), hint[k]["dung"]))
    return {"van_ban_da_sua": out, "da_sua": done, "goi_y": hints}


def hoc(sai, dung, nhap_nhang=False, nguon="Founder sua", ghi_chu="", ep=False, db=None, path=None):
    sai, dung = (sai or "").strip(), (dung or "").strip()
    if not sai or not dung:
        raise ValueError("Thieu 'sai' hoac 'dung'.")
    if len(sai) > MAX_LEN or len(dung) > MAX_LEN:
        raise ValueError("Chi luu tu hoac cum ngan (toi da %d ky tu)." % MAX_LEN)
    if norm(sai) == norm(dung):
        raise ValueError("'sai' va 'dung' giong nhau.")
    if len(sai) <= SHORT and not ep:
        nhap_nhang = True  # tu qua ngan de trung tu that: chi goi y
    db = db or load(path)
    today = dt.date.today().isoformat()
    for m in db["muc"]:
        if norm(m["sai"]) == norm(sai):
            if norm(m["dung"]) != norm(dung):
                m["ghi_chu"] = ("Truoc do hieu la '%s'. " % m["dung"] + (ghi_chu or m.get("ghi_chu", ""))).strip()
                m["dung"] = dung
            m["so_lan"] = int(m.get("so_lan", 0)) + 1
            m["lan_cuoi"] = today
            m["chac"] = not nhap_nhang
            save(db, path)
            return m
    m = {"sai": sai, "dung": dung, "chac": not nhap_nhang, "so_lan": 1, "lan_cuoi": today,
         "nguon": nguon, "ghi_chu": ghi_chu}
    db["muc"].append(m)
    save(db, path)
    return m


def xoa(sai, db=None, path=None):
    db = db or load(path)
    n0 = len(db["muc"])
    db["muc"] = [m for m in db["muc"] if norm(m["sai"]) != norm(sai)]
    save(db, path)
    return n0 - len(db["muc"])


def main():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except Exception:
            pass
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sua")
    s.add_argument("text")
    s.add_argument("--json", action="store_true")
    h = sub.add_parser("hoc")
    h.add_argument("sai")
    h.add_argument("dung")
    h.add_argument("--nhap-nhang", action="store_true", help="Chi goi y, khong tu sua (tu de trung tu that)")
    h.add_argument("--ep", action="store_true", help="Cho phep tu sua du tu ngan")
    h.add_argument("--ghi-chu", default="")
    sub.add_parser("xem")
    x = sub.add_parser("xoa")
    x.add_argument("sai")
    a = ap.parse_args()
    try:
        if a.cmd == "sua":
            r = sua(a.text)
            if a.json:
                print(json.dumps(r, ensure_ascii=False, indent=2))
            else:
                print(r["van_ban_da_sua"])
                for sai, dung in r["da_sua"]:
                    print("  da sua: %s -> %s" % (sai, dung), file=sys.stderr)
                for sai, dung in r["goi_y"]:
                    print("  co the: %s la %s (tuy ngu canh)" % (sai, dung), file=sys.stderr)
        elif a.cmd == "hoc":
            m = hoc(a.sai, a.dung, a.nhap_nhang, ghi_chu=a.ghi_chu, ep=a.ep)
            print("Da nho: \"%s\" -> \"%s\" (%s, %d lan)" % (
                m["sai"], m["dung"], "tu sua" if m["chac"] else "chi goi y", m["so_lan"]))
        elif a.cmd == "xem":
            for m in sorted(load()["muc"], key=lambda m: -int(m.get("so_lan", 0))):
                print("%-16s -> %-14s %-9s %2d lan  %s" % (
                    m["sai"], m["dung"], "tu sua" if m.get("chac") else "goi y", m.get("so_lan", 0), m.get("nguon", "")))
        elif a.cmd == "xoa":
            print("Da xoa %d muc." % xoa(a.sai))
    except ValueError as ex:
        sys.exit("Loi: %s" % ex)


if __name__ == "__main__":
    main()
