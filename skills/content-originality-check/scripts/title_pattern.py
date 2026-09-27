"""Do muc lap khuon cua danh sach tieu de video (dau hieu "san xuat hang loat").

    python title_pattern.py titles.txt          # moi dong mot tieu de
    python title_pattern.py titles.txt --json   # in JSON de skill doc tiep
    type titles.txt | python title_pattern.py - # doc tu stdin

KET QUA LA UOC TINH CUA SKILL, KHONG PHAI PHAN QUYET CUA YOUTUBE HAY META. Nguong duoi day tu dat,
chua doi chieu voi quyet dinh that cua nen tang nao. Chi de bao "tieu de nay giong nhau bao nhieu".
"""
import argparse
import itertools
import json
import re
import sys
from collections import Counter

# Nguong tu dat (uoc tinh). Chinh sua khi co du lieu that de doi chieu.
BAND_HIGH = 0.45
BAND_MID = 0.25
MIN_TITLES = 5


def tokens(title):
    t = re.sub(r"\d+", "#", title.lower())
    return re.findall(r"[#\w]+", t, flags=re.UNICODE)


def jaccard(a, b):
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if (a or b) else 0.0


def share_of_top(counter, n):
    return (counter.most_common(1)[0][1] / n) if counter else 0.0


def analyse(titles):
    titles = [t.strip() for t in titles if t.strip()]
    n = len(titles)
    toks = [tokens(t) for t in titles]
    out = {"so_tieu_de": n, "du_mau": n >= MIN_TITLES}
    if n < 2:
        out.update({"muc": "chua_du_mau", "ly_do": "Can it nhat %d tieu de gan nhat cua kenh." % MIN_TITLES})
        return out
    pairs = [jaccard(a, b) for a, b in itertools.combinations(toks, 2)]
    opener = Counter(" ".join(t[:2]) for t in toks if len(t) >= 2)
    closer = Counter(" ".join(t[-2:]) for t in toks if len(t) >= 2)
    shape = Counter(" ".join("#" if w == "#" else "w" for w in t) for t in toks)
    top_open, top_close = share_of_top(opener, n), share_of_top(closer, n)
    mean_j, max_j = sum(pairs) / len(pairs), max(pairs)
    score = max(0.5 * mean_j + 0.25 * top_open + 0.25 * top_close, 0.0)
    muc = "cao" if score >= BAND_HIGH else "vua" if score >= BAND_MID else "thap"
    if n < MIN_TITLES:
        muc = "chua_du_mau"
    out.update({
        "jaccard_trung_binh": round(mean_j, 3),
        "jaccard_cao_nhat": round(max_j, 3),
        "ti_le_mo_dau_giong_nhau": round(top_open, 3),
        "mo_dau_pho_bien": opener.most_common(1)[0][0] if opener else "",
        "ti_le_ket_thuc_giong_nhau": round(top_close, 3),
        "ket_thuc_pho_bien": closer.most_common(1)[0][0] if closer else "",
        "ti_le_cung_khuon_do_dai": round(share_of_top(shape, n), 3),
        "diem": round(score, 3),
        "muc": muc,
        "luu_y": "Uoc tinh cua skill, nguong tu dat, khong phai phan quyet cua nen tang.",
    })
    return out


def render(r):
    ten = {"cao": "CAO", "vua": "VỪA", "thap": "THẤP", "chua_du_mau": "CHƯA ĐỦ MẪU"}[r["muc"]]
    lines = ["Độ lặp khuôn tiêu đề: %s (%d tiêu đề)" % (ten, r["so_tieu_de"])]
    if r["muc"] == "chua_du_mau":
        lines.append("Cần ít nhất %d tiêu đề gần nhất của kênh mới kết luận được." % MIN_TITLES)
        if "jaccard_trung_binh" not in r:
            return "\n".join(lines)
        lines.append("Số dưới đây chỉ để tham khảo:")
    lines += [
        "Giống nhau trung bình giữa các cặp tiêu đề: %.0f%% (cặp giống nhất: %.0f%%)"
        % (r["jaccard_trung_binh"] * 100, r["jaccard_cao_nhat"] * 100),
        "Mở đầu giống nhau: %.0f%% tiêu đề bắt đầu bằng \"%s\"" % (r["ti_le_mo_dau_giong_nhau"] * 100, r["mo_dau_pho_bien"]),
        "Kết thúc giống nhau: %.0f%% tiêu đề kết thúc bằng \"%s\"" % (r["ti_le_ket_thuc_giong_nhau"] * 100, r["ket_thuc_pho_bien"]),
        "Cùng khuôn độ dài và số: %.0f%%" % (r["ti_le_cung_khuon_do_dai"] * 100),
        "Đây là ước tính của skill, ngưỡng tự đặt, không phải phán quyết của YouTube hay Meta.",
    ]
    return "\n".join(lines)


def main():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except Exception:
            pass
    ap = argparse.ArgumentParser()
    ap.add_argument("path", help="File UTF-8, moi dong mot tieu de; '-' la stdin")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    text = sys.stdin.read() if a.path == "-" else open(a.path, encoding="utf-8-sig").read()
    r = analyse(text.splitlines())
    print(json.dumps(r, ensure_ascii=False, indent=2) if a.json else render(r))


if __name__ == "__main__":
    main()
