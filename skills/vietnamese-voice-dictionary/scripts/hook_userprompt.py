"""Hook UserPromptSubmit: doc tin nhan cua Founder, ap tu dien giong noi, dua ban da hieu cho Claude.

KHONG bat mac dinh. Bat bang cach them vao settings.json (xem SKILL.md). Loi gi cung im lang, khong
bao gio chan tin nhan.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def main():
    try:
        data = json.loads(sys.stdin.read() or "{}")
        prompt = data.get("prompt") or ""
        import tu_dien
        r = tu_dien.sua(prompt)
        if not r["da_sua"] and not r["goi_y"]:
            return
        parts = ["Tin nhan cua Founder co the do voice-to-text nghe nham. Theo tu dien giong noi:"]
        if r["da_sua"]:
            parts.append("Da hieu: " + "; ".join("\"%s\" la \"%s\"" % (a, b) for a, b in r["da_sua"]) + ".")
        if r["goi_y"]:
            parts.append("Co the nghe nham, xet theo ngu canh: "
                         + "; ".join("\"%s\" co the la \"%s\"" % (a, b) for a, b in r["goi_y"]) + ".")
        parts.append("Doc theo nghia da sua. Neu Founder chinh lai mot tu, chay: python \"%s\" hoc \"<sai>\" \"<dung>\"."
                     % (Path(tu_dien.__file__)))
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
                                                 "additionalContext": " ".join(parts)}}, ensure_ascii=False))
    except Exception:
        return


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    main()
