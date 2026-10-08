# -*- coding: utf-8 -*-
"""Headless verification of the math-figures web edition.

Start a static server first, for example from the repository root:
    python -m http.server 8099 --bind 127.0.0.1
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import PAGE  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

BASE = "http://127.0.0.1:8099/books/math-figures/"
OUT = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.join(OUT, "shots")
os.makedirs(SHOTS, exist_ok=True)

report, errors = [], []


def check(name, cond, detail=""):
    line = f"{'PASS' if cond else 'FAIL'}  {name}" + (f"  — {detail}" if detail else "")
    report.append(line)
    print(line, flush=True)
    if not cond:
        errors.append(name)


with sync_playwright() as p:
    b = p.chromium.launch()
    c = b.new_context(viewport={"width": 1440, "height": 950})
    page = c.new_page()
    console = []
    page.on("console", lambda m: console.append((m.type, m.text)))
    page.on("pageerror", lambda e: console.append(("pageerror", str(e))))
    page.goto(BASE, wait_until="load")
    page.wait_for_timeout(1200)

    check("title", page.title().startswith("史上最美数学图形"), page.title())
    check("page marks itself ready",
          page.evaluate("document.documentElement.getAttribute('data-ready')") == "1")
    check("307 cards", page.locator("#list .card").count() == 307,
          str(page.locator("#list .card").count()))
    check("all cards visible at load", page.locator("#list .card:visible").count() == 307,
          str(page.locator("#list .card:visible").count()))
    check("53 section blocks (序章 + 50 章 + 尾声 + 附录)",
          page.locator("#list .sec-block").count() == 53)
    check("7 part banners", page.locator("#list .part").count() == 7)
    check("307 sidebar toc links", page.locator(".toc-sub a[data-go]").count() == 307)
    check("54 chapter buttons", page.locator("#f-ch [data-v]").count() == 54)
    check("counter shows 307", page.locator("#cnt").inner_text().strip() == "307")
    check("no console errors", not [x for x in console if x[0] in ("error", "pageerror")],
          json.dumps(console[:4], ensure_ascii=False))
    page.screenshot(path=os.path.join(SHOTS, "01-top.png"))

    # ---- 图形、公式、表格 ----
    m = page.evaluate("""() => ({
      figs: document.querySelectorAll('figure.fig img').length,
      emptySrc: Array.from(document.images).filter(i => !i.getAttribute('src')).length,
      broken: Array.from(document.images).filter(i => i.complete && i.naturalWidth === 0).length,
      eq: document.querySelectorAll('.eq').length,
      sub: document.querySelectorAll('.eq sub').length,
      tables: document.querySelectorAll('details.more .body table').length,
      tocInGloss: document.querySelectorAll('#gloss .toc-list li').length,
      angle: (document.body.innerText.match(/[\\u27e8\\u27e9]/g) || []).length,
      dollars: (document.body.innerText.match(/\\$/g) || []).length,
    })""")
    check("148 figures, none duplicated or missing", m["figs"] == 148, str(m["figs"]))
    check("no empty image sources", m["emptySrc"] == 0, str(m["emptySrc"]))
    check("no broken images", m["broken"] == 0, str(m["broken"]))
    check("formulas typeset", m["eq"] > 400 and m["sub"] > 100,
          f"{m['eq']} eq, {m['sub']} sub")
    check("5 tables", m["tables"] == 5, str(m["tables"]))
    check("printed table of contents kept", m["tocInGloss"] == 60, str(m["tocInGloss"]))
    check("no placeholders or raw LaTeX",
          m["angle"] == 0 and m["dollars"] == 0, json.dumps(m))

    # ---- 阅读栏与字阶 ----
    typ = page.evaluate("""() => {
      const card = document.querySelector('#list .card');
      card.querySelector('details.more').open = true;
      const p = card.querySelector('details.more .body p.bk');
      const cs = getComputedStyle(p);
      const r = document.createRange();
      r.setStart(p.firstChild, 0); r.setEnd(p.firstChild, 2);
      const probe = document.createElement('span');
      probe.textContent = '汉'.repeat(40);
      probe.style.cssText = 'position:absolute;visibility:hidden;white-space:nowrap;font:' + cs.font;
      p.appendChild(probe);
      const per = probe.getBoundingClientRect().width / 40;
      probe.remove();
      const w = s => Math.round(document.querySelector(s).getBoundingClientRect().width);
      const figW = Array.from(document.querySelectorAll('figure.fig img'))
        .map(i => Math.round(i.getBoundingClientRect().width));
      return {doc: w('.doc'), card: w('.card'), intro: w('.intro'),
              figMax: Math.max(...figW), figOver: figW.filter(x => x > 900).length,
              fs: parseFloat(cs.fontSize), lh: parseFloat(cs.lineHeight),
              indentEm: parseFloat(cs.textIndent) / parseFloat(cs.fontSize),
              delta: Math.round(r.getClientRects()[0].left - p.getBoundingClientRect().left),
              hanPerLine: Math.round(p.getBoundingClientRect().width / per),
              sidebarFs: parseFloat(getComputedStyle(document.querySelector('.sec-link')).fontSize)};
    }""")
    check("one reading column: text fills it and no figure exceeds it",
          typ["doc"] == typ["card"] == typ["intro"] == 900 and typ["figMax"] == 900
          and typ["figOver"] == 0, json.dumps(typ))
    check("body text at the enlarged size", typ["fs"] >= 17, f"{typ['fs']}px")
    check("line spacing stays generous", typ["lh"] / typ["fs"] >= 1.8,
          f"{typ['lh']}px at {typ['fs']}px")
    check("line measure stays readable", 30 <= typ["hanPerLine"] <= 55,
          f"{typ['hanPerLine']} 汉字/行")
    check("book paragraph has a 2em first-line indent",
          abs(typ["indentEm"] - 2) < 0.01 and abs(typ["delta"] - typ["indentEm"] * typ["fs"]) < 1.5,
          f"indentEm={typ['indentEm']} delta={typ['delta']}px")
    check("navigation chrome keeps its size", typ["sidebarFs"] == 14, f"{typ['sidebarFs']}px")

    # ---- 章节目录面板贴着自己的按钮 ----
    panels = page.evaluate("""() => Array.from(document.querySelectorAll('.toc-sub')).map(s => ({
        for: s.dataset.for, parentId: s.parentElement.id,
        prevBtn: s.previousElementSibling && s.previousElementSibling.dataset
                 ? s.previousElementSibling.dataset.v : null }))""")
    check("every chapter panel follows its own button",
          len(panels) == 53 and all(x["parentId"] == "f-ch" and x["prevBtn"] == x["for"]
                                    for x in panels),
          str([x for x in panels if x["prevBtn"] != x["for"]][:3]))
    page.click('#f-ch [data-v="1"]')
    page.wait_for_timeout(500)
    g = page.evaluate("""() => {
      const sub = document.querySelector('.toc-sub[data-for="1"]');
      const btn = document.querySelector('#f-ch [data-v="1"]');
      return {gap: Math.round(sub.getBoundingClientRect().top - btn.getBoundingClientRect().bottom),
              links: sub.querySelectorAll('a[data-go]').length,
              cards: Array.from(document.querySelectorAll('#list .card')).filter(x => !x.hidden).length,
              blocks: Array.from(document.querySelectorAll('#list .sec-block')).filter(x => !x.hidden).map(x => x.id)};
    }""")
    check("chapter panel opens under its own button", 0 <= g["gap"] <= 12, json.dumps(g))
    check("chapter 1 selects its six sections",
          g["cards"] == 6 and g["blocks"] == ["sec-1"] and g["links"] == 6, json.dumps(g))
    page.screenshot(path=os.path.join(SHOTS, "02-chapter1.png"))
    page.click('#f-ch [data-v=""]')
    page.wait_for_timeout(400)

    # ---- 六个固定小节名成为筛选维度 ----
    for dim, n in (("part", 10), ("kind", 7), ("mat", 4), ("len", 3)):
        check(f"{dim} chips", page.locator(f'[data-dim="{dim}"] [data-v]').count() == n,
              str(page.locator(f'[data-dim="{dim}"] [data-v]').count()))
    page.click('[data-dim="kind"] .chip:has-text("设计应用")')
    page.wait_for_timeout(500)
    n = page.locator("#list .card:visible").count()
    check("「设计应用」 selects the fifty design sections", n == 50, f"{n}")
    check("counter matches visible", page.locator("#cnt").inner_text().strip() == str(n))
    check("url carries the filter", "kind=" in page.url)
    page.click('[data-dim="mat"] .chip:has-text("含插图")')
    page.wait_for_timeout(400)
    check("second group is AND", page.locator("#list .card:visible").count() <= n,
          f"{n} -> {page.locator('#list .card:visible').count()}")
    page.click("#reset")
    page.wait_for_timeout(400)
    check("reset restores all", page.locator("#list .card:visible").count() == 307)
    check("reset clears the url", "kind=" not in page.url, page.url)

    # ---- 检索 ----
    for term in ("鹦鹉螺", "曼德勃罗", "壁纸群"):
        page.fill("#q", term)
        page.wait_for_timeout(500)
        k = page.locator("#list .card:visible").count()
        check(f"search “{term}”", 0 < k < 307, f"{k} cards")
    check("search highlights matches", page.locator("#list mark").count() > 0)
    page.fill("#q", "zzz-no-such-term")
    page.wait_for_timeout(500)
    check("empty state shows for a term with no match", page.locator("#empty").is_visible())
    page.click("#reset2")
    page.wait_for_timeout(400)
    check("empty-state reset works", page.locator("#list .card:visible").count() == 307)

    # ---- 深链与深色模式 ----
    page.goto(BASE + "#e-14-3", wait_until="load")
    page.wait_for_timeout(1200)
    check("deep link lands", page.locator("#e-14-3").is_visible())
    page.click("#theme")
    page.wait_for_timeout(300)
    check("dark mode toggles", page.evaluate(
        "document.documentElement.classList.contains('dark')"))
    page.screenshot(path=os.path.join(SHOTS, "03-dark.png"))
    page.click("#theme")
    c.close()

    # ---- 移动端 ----
    m2 = b.new_context(viewport={"width": 390, "height": 844})
    mp = m2.new_page()
    errs = []
    mp.on("pageerror", lambda e: errs.append(str(e)))
    mp.goto(BASE, wait_until="load")
    mp.wait_for_timeout(1100)
    check("mobile: no js errors", not errs, str(errs[:2]))
    check("mobile: no horizontal overflow", mp.evaluate(
        "document.documentElement.scrollWidth <= document.documentElement.clientWidth"),
        mp.evaluate("document.documentElement.scrollWidth + ' vs ' + document.documentElement.clientWidth"))
    mp.click("#menu")
    mp.wait_for_timeout(400)
    check("mobile: drawer opens", mp.evaluate(
        "document.getElementById('sidebar').classList.contains('open')"))
    m2.close()
    b.close()

# ---- 静态文件检查 ----
html = open(PAGE, encoding="utf-8").read()
check("static html has all cards", html.count('<article class="card"') == 307)
n_p = html.count("<p>") + html.count("<p ")
check("static html has full text", n_p > 1000, f"{n_p} paragraphs")
check("book paragraphs carry the indent class", html.count('<p class="bk">') > 700,
      str(html.count('<p class="bk">')))
check("no placeholder braces", "{{" not in html and "\u27e8" not in html)
suite = open(os.path.join(OUT, "..", "web-edition", "app.js"), encoding="utf-8").read()
shipped = open(os.path.join(OUT, "..", "..", "books", "math-figures", "app.js"),
               encoding="utf-8").read()
check("shipped app.js matches the shared source", suite == shipped)

print("\n".join(report))
print()
print(f"{len(report) - len(errors)}/{len(report)} checks passed")
if errors:
    print("FAILED: " + "; ".join(errors))
    sys.exit(1)
