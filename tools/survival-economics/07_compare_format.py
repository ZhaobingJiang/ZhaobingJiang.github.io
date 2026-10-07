# -*- coding: utf-8 -*-
"""Compare the Survival Economics edition's layout tokens with the reference site."""
import json
import os
import sys

from playwright.sync_api import sync_playwright

MINE = "http://127.0.0.1:8099/books/survival-economics/"
REF = "https://eternity4719.github.io/HowToLiveBetter/"

PROBE = """() => {
  const cs = (sel, props) => {
    const el = document.querySelector(sel);
    if (!el) return null;
    const c = getComputedStyle(el);
    const out = {};
    for (const p of props) out[p] = c[p];
    const r = el.getBoundingClientRect();
    out._box = [Math.round(r.x), Math.round(r.y), Math.round(r.width)];
    return out;
  };
  return {
    nav: cs('.nav', ['height','position','borderBottomColor','backgroundColor']),
    sidebar: cs('.sidebar', ['width','position','backgroundColor','overflowY','paddingLeft']),
    content: cs('.content', ['paddingLeft','paddingTop']),
    doc: cs('.doc', ['maxWidth']),
    h1: cs('.doc-head h1', ['fontSize','fontWeight','lineHeight']),
    card: cs('.card', ['backgroundColor','borderRadius','paddingTop','paddingLeft','marginBottom']),
    cardH3: cs('.card-h h3', ['fontSize','fontWeight','lineHeight']),
    human: cs('.human', ['fontSize','backgroundColor','borderLeftColor','borderLeftWidth']),
    badge: cs('.badge', ['fontSize','lineHeight','borderRadius','fontWeight','paddingLeft']),
    chip: cs('.chip', ['fontSize','lineHeight','borderRadius','paddingLeft']),
    secH2: cs('.sec-h h2', ['fontSize','fontWeight','lineHeight']),
    body: cs('body', ['fontSize','lineHeight','backgroundColor','color']),
    vars: (() => {
      const c = getComputedStyle(document.documentElement);
      const names = ['--bg','--bg-alt','--bg-soft','--divider','--t1','--t2','--t3','--brand-1',
                     '--green-1','--yellow-1','--red-1','--gray-soft','--side-w','--nav-h','--font'];
      const o = {};
      for (const n of names) o[n] = c.getPropertyValue(n).trim();
      return o;
    })(),
  };
}"""

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1440, "height": 950})
    pg = ctx.new_page()
    mine = None
    ref = None
    try:
        pg.goto(MINE, wait_until="load")
        pg.wait_for_timeout(500)
        mine = pg.evaluate(PROBE)
    except Exception as e:
        print("mine failed:", e)
    try:
        pg.goto(REF, wait_until="load")
        pg.wait_for_timeout(2500)
        ref = pg.evaluate(PROBE)
    except Exception as e:
        print("reference unreachable:", str(e)[:200])
    b.close()

if not mine:
    sys.exit("could not probe our page")

keys = ["nav", "sidebar", "doc", "h1", "card", "cardH3", "human", "badge", "chip", "secH2", "body"]
# 阅读区字阶是按书稿正文可读性单独定的（--fs），与参考站不同是设计决定，
# 不参与版式一致性计分，只单独列出来备查
TYPE_PROPS = {"fontSize", "lineHeight"}
print(f"{'element':<10} {'property':<20} {'ours':<34} {'reference':<34} match")
mismatch = 0
total = 0
type_rows = []
for k in keys:
    a = mine.get(k) or {}
    r = (ref or {}).get(k) or {}
    for prop in a:
        if prop == "_box":
            continue
        av, rv = a.get(prop), r.get(prop)
        same = (rv is None) or (av == rv)
        if prop in TYPE_PROPS:
            if rv is not None and not same:
                type_rows.append((k, prop, av, rv))
            continue
        total += 1
        if not same:
            mismatch += 1
        print(f"{k:<10} {prop:<20} {str(av):<34} {str(rv):<34} {'OK' if same else 'DIFF'}")

print()
print("design tokens")
mv, rv = mine["vars"], (ref or {}).get("vars", {})
for n in mv:
    same = rv.get(n) in (None, mv[n])
    print(f"  {n:<12} {mv[n]:<44} {str(rv.get(n)):<44} {'OK' if same else 'DIFF'}")

print()
print("deliberate type-scale differences (reading area is set from --fs, not the reference)")
if type_rows:
    for k, prop, av, rv in type_rows:
        print(f"  {k:<10} {prop:<12} ours {av:<12} reference {rv}")
else:
    print("  none measured (the reference renders its cards after loading its corpus)")

print()
print(f"layout comparison: {total - mismatch}/{total} identical to the reference")
if not ref:
    print("NOTE: the reference site was unreachable; only our own computed values are shown")
