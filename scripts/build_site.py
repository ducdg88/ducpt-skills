#!/usr/bin/env python3
"""Build the ducpt.com/skills/ pages from the skills in this repo.

Usage:
    python scripts/build_site.py --site "E:/WEB DUCPT/dg-media-office"

Writes <site>/skills/index.html and <site>/skills/<name>/index.html, adds missing
URLs to <site>/sitemap.xml and an "Agent Skills" section to <site>/llms.txt.
Idempotent: running twice produces the same files.
"""
import argparse
import datetime as dt
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "skills", "skill-distribution-kit", "scripts"))
from validate_skill import find_skills, parse_frontmatter  # noqa: E402

BASE = "https://ducpt.com"
CSS = ('<link rel="stylesheet" href="/platform-pages.css?v=20260730-mobile-tap-2">'
       '<link rel="stylesheet" href="/article-pages.css?v=20260711">')
HEADER = ('<header class="header"><nav class="nav" aria-label="Điều hướng chính"><a href="/">'
          '<img src="/assets/hvd-horizontal.svg" alt="DUCPT"></a><a href="/khoa-hoc/">Khóa học</a>'
          '<a href="/bai-viet/">Bài viết</a><a href="/dich-vu/">Dịch vụ đào tạo</a>'
          '<a href="/cong-cu-ai/">Công cụ AI</a><a href="/skills/">Skills</a>'
          '<a href="/ve-chung-toi/">Về chúng tôi</a><span class="grow"></span>'
          '<a class="login" href="/dang-nhap/">Đăng nhập</a></nav></header>')
FOOTER = ('<footer><div class="site-footer"><div class="footer-bottom"><span>© 2026 DUCPT. Bảo lưu mọi quyền.</span>'
          '<span>Kết nối: <a href="https://zalo.me/0963249467">Zalo DUCPT</a></span></div></div></footer>')
EXTRA_CSS = """<style>
.skill-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:16px;margin:24px 0}
.skill-card{border:1px solid rgba(127,127,127,.25);border-radius:16px;padding:18px;text-decoration:none!important;color:inherit;display:block}
.skill-card *{text-decoration:none!important}
.skill-card p{margin:0 0 8px;font-size:.95rem}
.skill-card:hover{border-color:currentColor}
.skill-card h3{margin:0 0 6px;font-size:1.05rem}
.skill-card code{font-size:.8rem;opacity:.75}
.install{position:relative;background:#0f172a;color:#e2e8f0;border-radius:12px;padding:14px 16px;margin:10px 0;overflow-x:auto;font:14px/1.5 ui-monospace,Consolas,monospace;white-space:pre}
.install button{position:absolute;top:8px;right:8px;font:12px system-ui;border:0;border-radius:8px;padding:4px 10px;cursor:pointer}
.skill-steps li{margin:6px 0}
</style>"""
COPY_JS = """<script>document.querySelectorAll('.install').forEach(function(b){var t=b.textContent;var k=document.createElement('button');k.type='button';k.textContent='Sao chép';k.onclick=function(){navigator.clipboard.writeText(t.trim()).then(function(){k.textContent='Đã chép'})};b.appendChild(k)});</script>"""


def esc(text):
    return html.escape(text, quote=True)


def utm(url, campaign, medium="skills-page"):
    return f"{url}?utm_source=ducpt-skills&utm_medium={medium}&utm_campaign={campaign}"


def page(title, desc, canonical, body, ld, og_image):
    return ("<!doctype html><html lang=\"vi\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            f"<title>{esc(title)}</title><meta name=\"description\" content=\"{esc(desc)}\">"
            f"<link rel=\"canonical\" href=\"{canonical}\">"
            f"<meta property=\"og:type\" content=\"website\"><meta property=\"og:title\" content=\"{esc(title)}\">"
            f"<meta property=\"og:description\" content=\"{esc(desc)}\"><meta property=\"og:url\" content=\"{canonical}\">"
            f"<meta property=\"og:image\" content=\"{og_image}\"><meta name=\"twitter:card\" content=\"summary_large_image\">"
            f"{CSS}{EXTRA_CSS}"
            + "".join(f"<script type=\"application/ld+json\">{json.dumps(x, ensure_ascii=False)}</script>" for x in ld)
            + f"</head><body>{HEADER}<main>{body}</main>{FOOTER}{COPY_JS}</body></html>\n")


def install_block(repo, name=None):
    target = f"{repo}" if name is None else f"{repo} --skill {name}"
    return (f'<div class="install">npx skills add {esc(target)}</div>'
            f'<div class="install">/plugin marketplace add {esc(repo)}\n/plugin install ducpt-skills@ducpt-skills</div>')


def read_skill(folder):
    with open(os.path.join(folder, "SKILL.md"), encoding="utf-8") as fh:
        text = fh.read()
    fm, err = parse_frontmatter(text)
    if err:
        raise SystemExit(f"{folder}: {err}")
    steps = re.findall(r"^## Step \d+\.\s*(.+)$", text, flags=re.M)
    scripts_dir = os.path.join(folder, "scripts")
    scripts = sorted(f for f in os.listdir(scripts_dir)
                     if f.endswith((".py", ".sh", ".js", ".ps1"))) if os.path.isdir(scripts_dir) else []
    return fm, steps, scripts


def build(site):
    with open(os.path.join(ROOT, "data", "site.json"), encoding="utf-8") as fh:
        cfg = json.load(fh)
    repo, og = cfg["repo"], cfg["og_image"]
    gh = f"https://github.com/{repo}"
    found = {os.path.basename(s): s for s in find_skills(os.path.join(ROOT, "skills"))}
    missing = sorted(set(found) ^ set(cfg["skills"]))
    if missing:
        raise SystemExit(f"data/site.json and skills/ disagree on: {missing}")
    skills = [found[name] for name in cfg["skills"]]  # order = site.json order
    out_root = os.path.join(site, "skills")
    urls, cards, items = [f"{BASE}/skills/"], [], []

    for i, folder in enumerate(skills, 1):
        name = os.path.basename(folder)
        meta = cfg["skills"][name]
        prod = cfg["products"][meta["product"]]
        fm, steps, scripts = read_skill(folder)
        url = f"{BASE}/skills/{name}/"
        urls.append(url)
        items.append({"@type": "ListItem", "position": i, "url": url, "name": meta["title"]})
        cards.append(f'<a class="skill-card" href="/skills/{name}/"><h3>{esc(meta["title"])}</h3>'
                     f'<p>{esc(meta["summary"])}</p><code>{esc(name)}</code></a>')
        steps_html = "".join(f"<li>{esc(s)}</li>" for s in meta.get("steps_vi", steps))
        scripts_html = ("<h2>Script đi kèm</h2><ul>" + "".join(
            f'<li><a href="{gh}/blob/main/skills/{name}/scripts/{esc(s)}">{esc(s)}</a> (Python, không cần cài thêm)</li>'
            for s in scripts) + "</ul>") if scripts else ""
        body = (
            f'<section class="article-hero"><div class="article-hero-inner"><span class="article-kicker">Agent Skill mã nguồn mở</span>'
            f'<h1>{esc(meta["title"])}</h1><p class="article-deck">{esc(meta["summary"])}</p>'
            f'<div class="article-quick-cta"><a class="article-button" href="{gh}/tree/main/skills/{name}">Xem trên GitHub</a>'
            f'<a class="article-button secondary" href="{utm(prod["url"], name)}">{esc(prod["name"])}</a></div></div></section>'
            f'<div class="article-layout" style="grid-template-columns:1fr"><div class="article-body">'
            f'<h2>Cài đặt</h2><p>Dùng được với Claude Code, Claude, Codex, Cursor, Gemini CLI và mọi agent đọc được <code>SKILL.md</code>.</p>'
            f'{install_block(repo, name)}'
            f'<p>Hoặc chép thư mục <code>skills/{esc(name)}</code> vào <code>~/.claude/skills/</code>.</p>'
            f'<h2>Skill làm những bước nào</h2><ol class="skill-steps">{steps_html}</ol>'
            f'{scripts_html}'
            f'<h2>Mô tả gốc (tiếng Anh)</h2><blockquote>{esc(fm["description"])}</blockquote>'
            f'<h2>Muốn làm tự động hơn?</h2><div class="download-box"><h2>{esc(prod["name"])}</h2>'
            f'<p>{esc(prod["pitch"])}</p><a class="article-button" href="{utm(prod["url"], name)}">Xem {esc(prod["name"])}</a></div>'
            f'<p><a href="/skills/">Xem tất cả skill của DUCPT</a></p></div></div>')
        ld = [
            {"@context": "https://schema.org", "@type": "SoftwareSourceCode", "name": name,
             "alternateName": meta["title"], "description": fm["description"], "url": url,
             "codeRepository": f"{gh}/tree/main/skills/{name}", "license": "https://opensource.org/licenses/MIT",
             "programmingLanguage": ["Markdown", "Python"] if scripts else ["Markdown"],
             "author": {"@type": "Organization", "name": "DUCPT", "url": BASE + "/"},
             "isAccessibleForFree": True, "inLanguage": ["vi", "en"]},
            {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "DUCPT", "item": BASE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Skills", "item": BASE + "/skills/"},
                {"@type": "ListItem", "position": 3, "name": meta["title"], "item": url}]},
        ]
        title = f"{meta['title']} · Agent Skill miễn phí · DUCPT"
        os.makedirs(os.path.join(out_root, name), exist_ok=True)
        with open(os.path.join(out_root, name, "index.html"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(page(title, meta["summary"], url, body, ld, og))

    hub_desc = (f"{len(skills)} Agent Skill mã nguồn mở của DUCPT cho người làm doanh nghiệp một người: "
                "dựng đội AI, bản ghi và văn tiếng Việt, Pinterest, YouTube, sơ đồ tư duy, dọn file, phân phối skill.")
    hub_body = (
        '<section class="article-hero"><div class="article-hero-inner"><span class="article-kicker">Mã nguồn mở, miễn phí</span>'
        '<h1>Agent Skills của DUCPT</h1>'
        f'<p class="article-deck">{esc(hub_desc)} Cài một lần, AI của bạn làm đúng quy trình mỗi lần.</p>'
        f'<div class="article-quick-cta"><a class="article-button" href="{gh}">Xem trên GitHub</a>'
        f'<a class="article-button secondary" href="{utm(cfg["products"]["course"]["url"], "skills-hub")}">Khóa học Doanh nghiệp một người</a></div></div></section>'
        '<div class="article-layout" style="grid-template-columns:1fr"><div class="article-body">'
        f'<h2>Cài tất cả trong một lệnh</h2>{install_block(repo)}'
        f'<h2>Danh sách skill</h2><div class="skill-grid">{"".join(cards)}</div>'
        '<h2>Skill là gì?</h2><p>Skill là một thư mục chứa file <code>SKILL.md</code>: quy trình, luật và script để AI agent làm một việc '
        'cụ thể theo đúng cách người giỏi nhất làm. Plugin là MCP cộng với skill, gói lại để cài một lần.</p>'
        '<p>Mỗi skill chỉ nhắc tới sản phẩm DUCPT tối đa một lần, và chỉ khi nhu cầu của bạn vượt quá những gì skill làm được.</p>'
        '</div></div>')
    hub_ld = [
        {"@context": "https://schema.org", "@type": "CollectionPage", "name": "Agent Skills của DUCPT",
         "url": BASE + "/skills/", "description": hub_desc,
         "mainEntity": {"@type": "ItemList", "itemListElement": items}},
    ]
    with open(os.path.join(out_root, "index.html"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(page("Agent Skills miễn phí cho AI agent · DUCPT", hub_desc, BASE + "/skills/", hub_body, hub_ld, og))

    today = dt.date.today().isoformat()
    sitemap = os.path.join(site, "sitemap.xml")
    with open(sitemap, encoding="utf-8") as fh:
        sm = fh.read()
    added = [u for u in urls if f"<loc>{u}</loc>" not in sm]
    if added:
        entries = "".join(f"  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>\n" for u in added)
        sm = sm.replace("</urlset>", entries + "</urlset>")
        with open(sitemap, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(sm)

    llms = os.path.join(site, "llms.txt")
    with open(llms, encoding="utf-8") as fh:
        lt = fh.read()
    if "## Agent Skills" not in lt:
        section = ("\n## Agent Skills\n\n"
                   f"- Hub: {BASE}/skills/ (open source, MIT, repository {gh})\n"
                   f"- Install: npx skills add {repo}\n"
                   + "".join(f"- {cfg['skills'][os.path.basename(s)]['title']}: {BASE}/skills/{os.path.basename(s)}/\n"
                             for s in skills))
        lt = lt.replace("\n## Citation Guidance", section + "\n## Citation Guidance", 1) \
            if "\n## Citation Guidance" in lt else lt.rstrip("\n") + "\n" + section
        with open(llms, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(lt)
    return urls, added


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build ducpt.com/skills pages.")
    ap.add_argument("--site", required=True)
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    urls, added = build(args.site)
    print(f"built {len(urls)} pages, {len(added)} new sitemap URLs")


if __name__ == "__main__":
    main()
