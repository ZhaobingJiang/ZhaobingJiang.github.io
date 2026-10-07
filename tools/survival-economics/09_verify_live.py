# -*- coding: utf-8 -*-
"""Smoke test the deployed GitHub Pages edition.

GitHub Pages can be slow from some networks (the book is one ~630 KB HTML file), so
every navigation retries and the report prints as it goes.
"""
import json
import sys

from playwright.sync_api import sync_playwright

LIVE = "https://ZhaobingJiang.github.io/books/survival-economics/"
BOOKS_ZH = "https://ZhaobingJiang.github.io/zh/books.html"
BOOKS_EN = "https://ZhaobingJiang.github.io/books/"

errors = []


def check(name, cond, detail=""):
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""), flush=True)
    if not cond:
        errors.append(name)


def open_page(pg, url, sel=None, tries=3):
    """Navigate with retries; a cold GitHub Pages cache can take many seconds.

    Waits for readyState "complete": the book is one big HTML file, so the first
    card exists long before the document, its stylesheet and its script are in.
    """
    for i in range(1, tries + 1):
        try:
            pg.goto(url, wait_until="commit", timeout=60000)
            pg.wait_for_function("document.readyState === 'complete'", timeout=90000)
            if sel:
                pg.wait_for_selector(sel, timeout=60000)
            pg.wait_for_timeout(900)
            return True
        except Exception as e:
            print(f"      (retry {i}/{tries} for {url}: {str(e)[:70]})", flush=True)
    return False


with sync_playwright() as p:
    b = p.chromium.launch()
    c = b.new_context(viewport={"width": 1440, "height": 950})
    pg = c.new_page()
    console = []
    pg.on("console", lambda m: console.append((m.type, m.text)))
    pg.on("pageerror", lambda e: console.append(("pageerror", str(e))))

    check("live page loads", open_page(pg, LIVE, "#list .card"))
    check("title", pg.title().startswith("不确定年代的生存经济学"), pg.title())
    check("94 cards", pg.locator("#list .card").count() == 94)
    check("94 visible", pg.locator("#list .card:visible").count() == 94,
          str(pg.locator("#list .card:visible").count()))
    check("18 blocks", pg.locator("#list .sec-block").count() == 18)
    check("css applied (sidebar 272px)", pg.evaluate(
        "getComputedStyle(document.querySelector('.sidebar')).width") == "272px")
    check("no console errors", not [x for x in console if x[0] in ("error", "pageerror")],
          str(console[:3]))

    # ---- 正文与图片同宽 + 中文首行缩进 ----
    col = pg.evaluate("""() => {
      const w = s => Math.round(document.querySelector(s).getBoundingClientRect().width);
      const card = document.querySelector('#list .card');
      card.querySelector('details.more').open = true;
      const p = card.querySelector('details.more .body p');
      const cs = getComputedStyle(p);
      const r = document.createRange();
      r.setStart(p.firstChild, 0); r.setEnd(p.firstChild, 2);
      return {doc: w('.doc'), hero: w('.hero'), card: w('.card'), intro: w('.intro'),
              lede: w('.lede'), part: w('.part'),
              bodyP: Math.round(p.getBoundingClientRect().width),
              indentEm: parseFloat(cs.textIndent) / parseFloat(cs.fontSize),
              firstLineDelta: Math.round(r.getClientRects()[0].left - p.getBoundingClientRect().left)};
    }""")
    check("text column matches the image column",
          col["doc"] == col["hero"] == col["card"] == col["intro"] == col["lede"] == col["part"] == 900,
          json.dumps(col))
    check("book paragraph has a 2em first-line indent",
          abs(col["indentEm"] - 2) < 0.01 and abs(col["firstLineDelta"] - col["indentEm"] * 14.5) < 1.5,
          f"indentEm={col['indentEm']} firstLineDelta={col['firstLineDelta']}px")

    # ---- 交互 ----
    pg.fill("#q", "明斯基")
    pg.wait_for_timeout(700)
    n = pg.locator("#list .card:visible").count()
    check("live search works", 0 < n < 94, f"{n} cards")
    pg.click("#reset")
    pg.wait_for_timeout(400)
    check("live reset works", pg.locator("#list .card:visible").count() == 94)

    # ---- 入口链接 ----
    for src, sel in ((BOOKS_ZH, 'a[href="../books/survival-economics/"]'),
                     (BOOKS_EN, 'a[href="./survival-economics/"]')):
        check(f"entry link present on {src.split('github.io')[1]}",
              open_page(pg, src, sel) and pg.locator(sel).count() == 1)
        pg.locator(sel).first.click()
        pg.wait_for_selector("#list .card", timeout=60000)
        pg.wait_for_timeout(800)
        check("entry link lands on the web edition",
              pg.locator("#list .card").count() == 94, pg.url)

    # ---- 图片 ----
    check("live page reopens", open_page(pg, LIVE, "#list .card"))
    broken = pg.evaluate(
        "Array.from(document.images).filter(i => i.complete && i.naturalWidth === 0).map(i => i.src)")
    check("no broken images", not broken, str(broken))
    c.close()

    m = b.new_context(viewport={"width": 390, "height": 844})
    mp = m.new_page()
    check("mobile loads", open_page(mp, LIVE, "#list .card"))
    check("mobile no horizontal overflow", mp.evaluate(
        "document.documentElement.scrollWidth <= document.documentElement.clientWidth"),
        mp.evaluate("document.documentElement.scrollWidth + ' vs ' + document.documentElement.clientWidth"))
    mp.click("#menu")
    mp.wait_for_timeout(500)
    check("mobile drawer opens", mp.evaluate(
        "document.getElementById('sidebar').classList.contains('open')"))
    m.close()
    b.close()

print()
print("FAILED: " + "; ".join(errors) if errors else "all live checks passed")
sys.exit(1 if errors else 0)
