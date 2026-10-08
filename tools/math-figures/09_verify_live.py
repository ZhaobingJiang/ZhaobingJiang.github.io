# -*- coding: utf-8 -*-
"""Smoke test the deployed math-figures page and the other two editions."""
import json
import sys

from playwright.sync_api import sync_playwright

LIVE = "https://ZhaobingJiang.github.io/books/math-figures/"
LUCK = "https://ZhaobingJiang.github.io/books/luck-engineering/"
SURVIVAL = "https://ZhaobingJiang.github.io/books/survival-economics/"
BOOKS_ZH = "https://ZhaobingJiang.github.io/zh/books.html"
BOOKS_EN = "https://ZhaobingJiang.github.io/books/"

errors = []


def check(name, cond, detail=""):
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""), flush=True)
    if not cond:
        errors.append(name)


def open_page(pg, url, sel=None, tries=3, app=False):
    for i in range(1, tries + 1):
        try:
            pg.goto(url, wait_until="commit", timeout=60000)
            if sel:
                pg.wait_for_selector(sel, timeout=60000)
            if app:
                pg.wait_for_function(
                    "document.documentElement.getAttribute('data-ready') === '1'", timeout=90000)
            pg.wait_for_timeout(800)
            return True
        except Exception as e:
            print(f"      (retry {i}/{tries}: {str(e)[:60]})", flush=True)
    return False


with sync_playwright() as p:
    b = p.chromium.launch()
    c = b.new_context(viewport={"width": 1440, "height": 950})
    pg = c.new_page()
    console = []
    pg.on("console", lambda m: console.append((m.type, m.text)))
    pg.on("pageerror", lambda e: console.append(("pageerror", str(e))))

    check("live page loads", open_page(pg, LIVE, "#list .card", app=True))
    check("title", pg.title().startswith("史上最美数学图形"), pg.title())
    r = pg.evaluate("""() => ({
      cards: document.querySelectorAll('#list .card').length,
      visible: Array.from(document.querySelectorAll('#list .card')).filter(x => !x.hidden).length,
      blocks: document.querySelectorAll('#list .sec-block').length,
      parts: document.querySelectorAll('#list .part').length,
      figs: document.querySelectorAll('figure.fig img').length,
      broken: Array.from(document.images).filter(i => i.complete && i.naturalWidth === 0).length,
      eq: document.querySelectorAll('.eq').length,
      tables: document.querySelectorAll('details.more .body table').length,
      toc: document.querySelectorAll('.toc-sub a[data-go]').length,
      tocInGloss: document.querySelectorAll('#gloss .toc-list li').length,
      kinds: document.querySelectorAll('[data-dim="kind"] .chip').length,
      angle: (document.body.innerText.match(/[\\u27e8\\u27e9]/g) || []).length,
      width: Math.round(document.querySelector('.doc').getBoundingClientRect().width),
      fs: parseFloat(getComputedStyle(document.querySelector('.lede')).fontSize),
      logo: document.querySelector('.logo').textContent.trim(),
    })""")
    check("307 cards", r["cards"] == 307, str(r["cards"]))
    check("all visible", r["visible"] == 307, str(r["visible"]))
    check("53 blocks, 7 part banners", r["blocks"] == 53 and r["parts"] == 7, json.dumps(r))
    check("148 figures, none broken", r["figs"] == 148 and r["broken"] == 0, json.dumps(r))
    check("formulas typeset", r["eq"] > 400, str(r["eq"]))
    check("5 tables", r["tables"] == 5, str(r["tables"]))
    check("307 toc links, 60 printed toc entries",
          r["toc"] == 307 and r["tocInGloss"] == 60, json.dumps(r))
    check("six recurring section names plus 其他", r["kinds"] == 7, str(r["kinds"]))
    check("no placeholders", r["angle"] == 0, str(r["angle"]))
    check("900px column, 18px body", r["width"] == 900 and r["fs"] == 18, json.dumps(r))
    check("site mark is the author's surname", r["logo"] == "\u6c5f", r["logo"])
    check("no console errors", not [x for x in console if x[0] in ("error", "pageerror")],
          str(console[:3]))

    pg.click('[data-dim="kind"] .chip:has-text("设计应用")')
    pg.wait_for_timeout(700)
    n = pg.locator("#list .card:visible").count()
    check("设计应用 selects the fifty design sections", n == 50, str(n))
    pg.click("#reset")
    pg.wait_for_timeout(500)

    pg.click('#f-ch [data-v="1"]')
    pg.wait_for_timeout(600)
    g = pg.evaluate("""() => {
      const sub = document.querySelector('.toc-sub[data-for="1"]');
      const btn = document.querySelector('#f-ch [data-v="1"]');
      return {gap: Math.round(sub.getBoundingClientRect().top - btn.getBoundingClientRect().bottom),
              cards: Array.from(document.querySelectorAll('#list .card')).filter(x => !x.hidden).length};
    }""")
    check("chapter panel opens under its own button", 0 <= g["gap"] <= 12, json.dumps(g))
    check("chapter 1 shows its six sections", g["cards"] == 6, str(g["cards"]))
    pg.click("#reset")
    pg.wait_for_timeout(400)

    pg.fill("#q", "鹦鹉螺")
    pg.wait_for_timeout(700)
    n = pg.locator("#list .card:visible").count()
    check("live search works", 0 < n < 307, f"{n} cards")
    pg.click("#reset")
    pg.wait_for_timeout(400)
    check("live reset works", pg.locator("#list .card:visible").count() == 307)

    for src, sel in ((BOOKS_ZH, 'a[href="../books/math-figures/"]'),
                     (BOOKS_EN, 'a[href="./math-figures/"]')):
        check(f"entry link present on {src.split('github.io')[1]}",
              open_page(pg, src, sel) and pg.locator(sel).count() == 1)
        pg.locator(sel).first.click()
        pg.wait_for_selector("#list .card", timeout=60000)
        pg.wait_for_timeout(900)
        check("entry link lands on the web edition",
              pg.locator("#list .card").count() == 307, pg.url)

    # 另外两本仍然可用，且站点标记已统一
    for name, url, want in (("luck-engineering", LUCK, 183), ("survival-economics", SURVIVAL, 94)):
        check(f"{name} still live", open_page(pg, url, "#list .card", app=True))
        check(f"{name} still {want} cards", pg.locator("#list .card").count() == want,
              str(pg.locator("#list .card").count()))
        check(f"{name} uses the same site mark",
              pg.evaluate("document.querySelector('.logo').textContent.trim()") == "\u6c5f")
    c.close()

    m = b.new_context(viewport={"width": 390, "height": 844})
    mp = m.new_page()
    check("mobile loads", open_page(mp, LIVE, "#list .card", app=True))
    check("mobile: no horizontal overflow", mp.evaluate(
        "document.documentElement.scrollWidth <= document.documentElement.clientWidth"),
        mp.evaluate("document.documentElement.scrollWidth + ' vs ' + document.documentElement.clientWidth"))
    mp.click("#menu")
    mp.wait_for_timeout(500)
    check("mobile: drawer opens", mp.evaluate(
        "document.getElementById('sidebar').classList.contains('open')"))
    m.close()
    b.close()

print()
print("FAILED: " + "; ".join(errors) if errors else "all live checks passed")
sys.exit(1 if errors else 0)
