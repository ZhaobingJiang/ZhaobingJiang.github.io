# -*- coding: utf-8 -*-
"""Headless verification of the Luck Engineering web edition.

Start a static server first, for example from the repository root:
    python -m http.server 8099 --bind 127.0.0.1
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import PAGE  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

BASE = "http://127.0.0.1:8099/books/luck-engineering/"
OUT = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.join(OUT, "shots")
os.makedirs(SHOTS, exist_ok=True)

report, errors = [], []


def check(name, cond, detail=""):
    report.append(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
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
    page.wait_for_timeout(900)

    # ---- 基本结构 ----
    check("title", page.title().startswith("运气工程学"), page.title())
    check("page marks itself ready",
          page.evaluate("document.documentElement.getAttribute('data-ready')") == "1")
    check("183 cards", page.locator("#list .card").count() == 183,
          str(page.locator("#list .card").count()))
    check("all cards visible at load", page.locator("#list .card:visible").count() == 183,
          str(page.locator("#list .card:visible").count()))
    check("25 section blocks", page.locator("#list .sec-block").count() == 25)
    check("4 part banners", page.locator("#list .part").count() == 4)
    check("46 figures", page.locator("figure.fig img").count() == 46)
    check("183 sidebar toc links", page.locator(".toc-sub a[data-go]").count() == 183)
    check("26 chapter buttons", page.locator("#f-ch [data-v]").count() == 26)
    check("counter shows 183", page.locator("#cnt").inner_text().strip() == "183")
    check("no console errors", not [x for x in console if x[0] in ("error", "pageerror")],
          json.dumps(console[:4], ensure_ascii=False))
    page.screenshot(path=os.path.join(SHOTS, "01-top.png"))

    # ---- 公式、表格、插图 ----
    m = page.evaluate("""() => ({
      eq: document.querySelectorAll('.eq').length,
      sub: document.querySelectorAll('.eq sub').length,
      frac: document.querySelectorAll('.eq .frac').length,
      tables: document.querySelectorAll('details.more .body table').length,
      figs: document.querySelectorAll('figure.fig img').length,
      tails: document.querySelectorAll('details.gloss').length,
      epigraph: document.querySelectorAll('.epigraph').length,
      marks: document.querySelectorAll('.mark').length,
      lede: document.querySelectorAll('.lede').length,
      dollars: (document.body.innerText.match(/\\$/g) || []).length,
      angle: (document.body.innerText.match(/[\\u27e8\\u27e9]/g) || []).length,
      latex: (document.body.innerText.match(/\\\\[a-zA-Z]{3,}/g) || []).length,
    })""")
    check("inline math rendered", m["eq"] > 700, f"{m['eq']} spans")
    check("subscripts rendered", m["sub"] > 390, f"{m['sub']}")
    check("fractions rendered", m["frac"] >= 2, f"{m['frac']}")
    check("78 tables rendered", m["tables"] == 78, f"{m['tables']}")
    check("chapter footers rendered", m["tails"] >= 80, f"{m['tails']}")
    check("epigraphs rendered", m["epigraph"] == 18, f"{m['epigraph']}")
    check("【进阶·可跳过】 markers rendered", m["marks"] == 37, f"{m['marks']}")
    check("no leftover LaTeX or placeholders",
          m["dollars"] == 0 and m["angle"] == 0 and m["latex"] == 0, json.dumps(m))

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
      const w = s => { const el = document.querySelector(s); return el ? Math.round(el.getBoundingClientRect().width) : null; };
      return {doc: w('.doc'), fig: w('figure.fig img'), card: w('.card'), intro: w('.intro'),
              fs: parseFloat(cs.fontSize), lh: parseFloat(cs.lineHeight),
              indentEm: parseFloat(cs.textIndent) / parseFloat(cs.fontSize),
              delta: Math.round(r.getClientRects()[0].left - p.getBoundingClientRect().left),
              hanPerLine: Math.round(p.getBoundingClientRect().width / per),
              sidebarFs: parseFloat(getComputedStyle(document.querySelector('.sec-link')).fontSize)};
    }""")
    check("one reading column for text and figures",
          typ["doc"] == typ["fig"] == typ["card"] == typ["intro"] == 900, json.dumps(typ))
    check("body text stays at the enlarged size", typ["fs"] >= 17, f"{typ['fs']}px")
    check("line spacing stays generous", typ["lh"] / typ["fs"] >= 1.8,
          f"{typ['lh']}px at {typ['fs']}px")
    check("line measure stays readable", 30 <= typ["hanPerLine"] <= 55,
          f"{typ['hanPerLine']} 汉字/行")
    check("book paragraph has a 2em first-line indent",
          abs(typ["indentEm"] - 2) < 0.01 and abs(typ["delta"] - typ["indentEm"] * typ["fs"]) < 1.5,
          f"indentEm={typ['indentEm']} delta={typ['delta']}px")
    check("navigation chrome keeps its size", typ["sidebarFs"] == 14, f"{typ['sidebarFs']}px")

    # ---- 章节目录面板必须贴着自己的按钮 ----
    panels = page.evaluate("""() => Array.from(document.querySelectorAll('.toc-sub')).map(s => ({
        for: s.dataset.for, parentId: s.parentElement.id,
        prevBtn: s.previousElementSibling && s.previousElementSibling.dataset
                 ? s.previousElementSibling.dataset.v : null }))""")
    check("every chapter panel follows its own button",
          len(panels) == 25 and all(p2["parentId"] == "f-ch" and p2["prevBtn"] == p2["for"]
                                    for p2 in panels),
          str([p2 for p2 in panels if p2["prevBtn"] != p2["for"]][:3]))
    page.click('#f-ch [data-v="7"]')
    page.wait_for_timeout(500)
    g = page.evaluate("""() => {
      const sub = document.querySelector('.toc-sub[data-for="7"]');
      const btn = document.querySelector('#f-ch [data-v="7"]');
      return {gap: Math.round(sub.getBoundingClientRect().top - btn.getBoundingClientRect().bottom),
              links: sub.querySelectorAll('a[data-go]').length,
              cards: Array.from(document.querySelectorAll('#list .card')).filter(x => !x.hidden).length,
              blocks: Array.from(document.querySelectorAll('#list .sec-block')).filter(x => !x.hidden).map(x => x.id)};
    }""")
    check("chapter panel opens under its own button", 0 <= g["gap"] <= 12, json.dumps(g))
    check("chapter 7 selects its 8 units",
          g["cards"] == 8 and g["blocks"] == ["sec-7"] and g["links"] == 8, json.dumps(g))
    page.screenshot(path=os.path.join(SHOTS, "02-chapter7.png"))
    page.click('#f-ch [data-v=""]')
    page.wait_for_timeout(400)

    # ---- 各筛选维度 ----
    for dim, n in (("part", 6), ("kind", 5), ("mat", 4), ("len", 3)):
        check(f"{dim} buttons", page.locator(f'[data-dim="{dim}"] [data-v]').count() == n,
              str(page.locator(f'[data-dim="{dim}"] [data-v]').count()))
    page.click('[data-dim="kind"] .chip:has-text("可执行清单")')
    page.wait_for_timeout(400)
    n = page.locator("#list .card:visible").count()
    check("kind filter narrows the list", 0 < n < 183, f"{n}")
    check("counter matches visible", page.locator("#cnt").inner_text().strip() == str(n))
    check("url carries the filter", "kind=" in page.url)
    page.click('[data-dim="len"] .chip:has-text("一坐")')
    page.wait_for_timeout(400)
    check("second group is AND", page.locator("#list .card:visible").count() <= n,
          f"{n} -> {page.locator('#list .card:visible').count()}")
    page.click("#reset")
    page.wait_for_timeout(400)
    check("reset restores all", page.locator("#list .card:visible").count() == 183)
    check("reset clears the url", "kind=" not in page.url, page.url)

    # 附录：七个字母各成一个区块
    page.click('#f-ch [data-v="B"]')
    page.wait_for_timeout(400)
    check("appendix B selects its 14 units",
          page.locator("#list .card:visible").count() == 14,
          str(page.locator("#list .card:visible").count()))
    page.click("#reset")
    page.wait_for_timeout(300)

    # ---- 检索 ----
    for term, lo, hi in (("机会到达率", 1, 183), ("尾部风险", 1, 183), ("明斯基", 0, 0)):
        page.fill("#q", term)
        page.wait_for_timeout(500)
        n = page.locator("#list .card:visible").count()
        check(f"search “{term}”", lo <= n <= hi, f"{n} cards")
    check("search highlights matches", page.locator("#list mark").count() > 0,
          str(page.locator("#list mark").count()))
    page.click("#reset2")
    page.wait_for_timeout(400)
    check("empty-state reset works", page.locator("#list .card:visible").count() == 183)

    # ---- 深链与深色模式 ----
    page.goto(BASE + "#e-13-3", wait_until="load")
    page.wait_for_timeout(900)
    check("deep link lands", page.locator("#e-13-3").is_visible())
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
    mp.wait_for_timeout(900)
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
check("static html has all cards", html.count('<article class="card"') == 183)
n_p = html.count("<p>") + html.count("<p ")
check("static html has full text", n_p > 800, f"{n_p} paragraphs")
check("book paragraphs carry the indent class", html.count('<p class="bk">') > 700,
      str(html.count('<p class="bk">')))
check("no placeholder braces", "{{" not in html and "⟨" not in html)
suite = open(os.path.join(OUT, "..", "web-edition", "app.js"), encoding="utf-8").read()
shipped = open(os.path.join(OUT, "..", "..", "books", "luck-engineering", "app.js"),
               encoding="utf-8").read()
check("shipped app.js matches the shared source", suite == shipped)

print("\n".join(report))
print()
print(f"{len(report) - len(errors)}/{len(report)} checks passed")
if errors:
    print("FAILED: " + "; ".join(errors))
    sys.exit(1)
