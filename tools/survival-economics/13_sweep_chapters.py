# -*- coding: utf-8 -*-
"""Sweep all 18 sidebar entries: each must open its own panel and filter to its own units."""
import json
import sys

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8099/books/survival-economics/"

with sync_playwright() as p:
    b = p.chromium.launch()
    c = b.new_context(viewport={"width": 1440, "height": 950})
    pg = c.new_page()
    pg.goto(BASE, wait_until="load")
    pg.wait_for_timeout(700)

    keys = pg.evaluate(
        "Array.from(document.querySelectorAll('#f-ch [data-v]')).map(b => b.dataset.v)")
    bad = []
    print(f"{'chapter':<8} {'button':>6} {'cards':>6} {'blocks':>22} {'panelGap':>9} {'links':>6} {'none':>6}")
    for k in keys:
        if k == "":
            continue
        sel = f'#f-ch [data-v="{k}"]'
        pg.click(sel)
        pg.wait_for_timeout(320)
        r = pg.evaluate("""(k) => {
          const key = k === '' ? '' : k;
          const sub = document.querySelector('.toc-sub[data-for="' + key + '"]');
          const btn = document.querySelector('#f-ch [data-v="' + key + '"]');
          const openSubs = Array.from(document.querySelectorAll('.toc-sub')).filter(s => !s.hidden).map(s => s.dataset.for);
          return {
            buttonCount: Number(btn.querySelector('i').textContent),
            cards: Array.from(document.querySelectorAll('#list .card')).filter(c => !c.hidden).length,
            blocks: Array.from(document.querySelectorAll('#list .sec-block')).filter(b => !b.hidden).map(b => b.id),
            gap: sub ? Math.round(sub.getBoundingClientRect().top - btn.getBoundingClientRect().bottom) : null,
            links: sub ? sub.querySelectorAll('a[data-go]').length : 0,
            noneShown: sub ? !sub.querySelector('.toc-none').hidden : null,
            openSubs,
          };
        }""", k)
        panel_ok = r["gap"] is not None and 0 <= r["gap"] <= 12 and r["openSubs"] == [k]
        count_ok = r["buttonCount"] == r["cards"] and r["links"] == r["cards"] and not r["noneShown"]
        blocks_ok = len(r["blocks"]) == 1 and r["blocks"][0] in ("sec-" + k, "sec-app" if k == "app" else "sec-" + k)
        mark = "OK " if (panel_ok and count_ok and blocks_ok) else "BAD"
        if mark == "BAD":
            bad.append((k, r))
        print(f"{k:<8} {r['buttonCount']:>6} {r['cards']:>6} {str(r['blocks']):>22} {str(r['gap']):>9} {r['links']:>6} {str(r['noneShown']):>6}  {mark}")

    # 全部章节
    pg.click('#f-ch [data-v=""]')
    pg.wait_for_timeout(400)
    allr = pg.evaluate("""() => ({
      cards: Array.from(document.querySelectorAll('#list .card')).filter(c => !c.hidden).length,
      blocks: Array.from(document.querySelectorAll('#list .sec-block')).filter(b => !b.hidden).length,
      counter: document.getElementById('cnt').textContent})""")
    print(f"\n全部章节: cards={allr['cards']} blocks={allr['blocks']} counter={allr['counter']}")
    if allr["cards"] != 94 or allr["blocks"] != 18 or allr["counter"] != "94":
        bad.append(("all", allr))

    c.close()
    b.close()

print()
if bad:
    print("PROBLEMS:")
    for k, r in bad:
        print(" ", k, json.dumps(r, ensure_ascii=False))
    sys.exit(1)
print("all 18 chapter entries open their own panel and filter to their own units")
