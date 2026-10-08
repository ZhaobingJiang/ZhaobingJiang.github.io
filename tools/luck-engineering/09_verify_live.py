# -*- coding: utf-8 -*-
"""Smoke test the deployed Luck Engineering page.

GitHub Pages can be slow from some networks, so every navigation retries and the
report prints as it goes.
"""
import json
import sys

from playwright.sync_api import sync_playwright

LIVE = "https://ZhaobingJiang.github.io/books/luck-engineering/"
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
            pg.wait_for_timeout(700)
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
    check("title", pg.title().startswith("运气工程学"), pg.title())
    r = pg.evaluate("""() => ({
      cards: document.querySelectorAll('#list .card').length,
      visible: Array.from(document.querySelectorAll('#list .card')).filter(x => !x.hidden).length,
      blocks: document.querySelectorAll('#list .sec-block').length,
      parts: document.querySelectorAll('#list .part').length,
      figs: document.querySelectorAll('figure.fig img').length,
      eq: document.querySelectorAll('.eq').length,
      sub: document.querySelectorAll('.eq sub').length,
      tables: document.querySelectorAll('details.more .body table').length,
      toc: document.querySelectorAll('.toc-sub a[data-go]').length,
      counter: document.getElementById('cnt').textContent,
      angle: (document.body.innerText.match(/[\\u27e8\\u27e9]/g) || []).length,
      broken: Array.from(document.images).filter(i => i.complete && i.naturalWidth === 0).length,
      width: Math.round(document.querySelector('.doc').getBoundingClientRect().width),
      fs: parseFloat(getComputedStyle(document.querySelector('.lede')).fontSize),
    })""")
    check("183 cards", r["cards"] == 183, str(r["cards"]))
    check("all visible", r["visible"] == 183, str(r["visible"]))
    check("25 blocks, 4 part banners", r["blocks"] == 25 and r["parts"] == 4, json.dumps(r))
    check("46 figures", r["figs"] == 46, str(r["figs"]))
    check("formulas typeset", r["eq"] > 700 and r["sub"] > 390, f"{r['eq']} eq, {r['sub']} sub")
    check("78 tables", r["tables"] == 78, str(r["tables"]))
    check("183 toc links", r["toc"] == 183, str(r["toc"]))
    check("no placeholders", r["angle"] == 0, str(r["angle"]))
    check("no broken images", r["broken"] == 0, str(r["broken"]))
    check("900px reading column", r["width"] == 900, str(r["width"]))
    check("body text at 18px", r["fs"] == 18, str(r["fs"]))
    check("no console errors", not [x for x in console if x[0] in ("error", "pageerror")],
          str(console[:3]))

    pg.click('#f-ch [data-v="7"]')
    pg.wait_for_timeout(600)
    g = pg.evaluate("""() => {
      const sub = document.querySelector('.toc-sub[data-for="7"]');
      const btn = document.querySelector('#f-ch [data-v="7"]');
      return {gap: Math.round(sub.getBoundingClientRect().top - btn.getBoundingClientRect().bottom),
              cards: Array.from(document.querySelectorAll('#list .card')).filter(x => !x.hidden).length};
    }""")
    check("chapter panel opens under its own button", 0 <= g["gap"] <= 12, json.dumps(g))
    check("chapter 7 shows its 8 units", g["cards"] == 8, str(g["cards"]))
    pg.click("#reset")
    pg.wait_for_timeout(400)

    pg.fill("#q", "机会到达率")
    pg.wait_for_timeout(700)
    n = pg.locator("#list .card:visible").count()
    check("live search works", 0 < n < 183, f"{n} cards")
    pg.click("#reset")
    pg.wait_for_timeout(400)
    check("live reset works", pg.locator("#list .card:visible").count() == 183)

    for src, sel in ((BOOKS_ZH, 'a[href="../books/luck-engineering/"]'),
                     (BOOKS_EN, 'a[href="./luck-engineering/"]')):
        check(f"entry link present on {src.split('github.io')[1]}",
              open_page(pg, src, sel) and pg.locator(sel).count() == 1)
        pg.locator(sel).first.click()
        pg.wait_for_selector("#list .card", timeout=60000)
        pg.wait_for_timeout(900)
        check("entry link lands on the web edition",
              pg.locator("#list .card").count() == 183, pg.url)

    check("survival edition still live", open_page(pg, SURVIVAL, "#list .card", app=True))
    check("survival edition still 94 cards", pg.locator("#list .card").count() == 94,
          str(pg.locator("#list .card").count()))
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
