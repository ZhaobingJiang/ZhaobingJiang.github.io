# -*- coding: utf-8 -*-
"""Headless verification of the Survival Economics web edition.

Start a static server first, for example from the repository root:
    python -m http.server 8099 --bind 127.0.0.1
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from paths import PAGE
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8099/books/survival-economics/"
OUT = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.join(OUT, "shots")
os.makedirs(SHOTS, exist_ok=True)

report = []
errors = []


def check(name, cond, detail=""):
    report.append(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not cond:
        errors.append(name)


with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1440, "height": 950}, device_scale_factor=1)
    page = ctx.new_page()
    console = []
    page.on("console", lambda m: console.append((m.type, m.text)))
    page.on("pageerror", lambda e: console.append(("pageerror", str(e))))

    page.goto(BASE, wait_until="load")
    page.wait_for_timeout(600)

    # ---- basics ----
    check("title", "不确定年代的生存经济学" in page.title(), page.title())
    n_cards = page.locator("#list .card").count()
    check("94 cards in DOM", n_cards == 94, f"got {n_cards}")
    n_visible = page.locator("#list .card:visible").count()
    check("all cards visible initially", n_visible == 94, f"got {n_visible}")
    check("counter shows 94", page.locator("#cnt").inner_text().strip() == "94",
          page.locator("#cnt").inner_text())
    check("18 chapter blocks", page.locator("#list .sec-block").count() == 18)
    check("no 404s / console errors", not [c for c in console if c[0] in ("error", "pageerror")],
          json.dumps(console[:5], ensure_ascii=False))

    # ---- sidebar ----
    check("part buttons", page.locator('[data-dim="part"] [data-v]').count() == 6,
          str(page.locator('[data-dim="part"] [data-v]').count()))
    check("chapter buttons", page.locator('#f-ch [data-v]').count() == 19)
    check("toc links", page.locator('.toc-sub a[data-go]').count() == 94)
    check("appendix cards laid out", page.evaluate(
        "['e-appA','e-appB','e-appC'].every(i=>{const r=document.getElementById(i).getBoundingClientRect();return r.width>0&&r.height>0;})"))
    check("appendix section visible", page.locator("#sec-app").is_visible())

    # ---- 回归：正文与图片同宽、中文首行缩进 ----
    col = page.evaluate("""() => {
      const w = s => { const el = document.querySelector(s); return el ? Math.round(el.getBoundingClientRect().width) : null; };
      const card = document.querySelector('#list .card');
      card.querySelector('details.more').open = true;
      // 正文不受额外 max-width 限制：宽度应等于所在容器的内容宽度
      const fills = s => {
        const el = document.querySelector(s);
        const p = el.parentElement, cs = getComputedStyle(p);
        const avail = p.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
        return {w: Math.round(el.getBoundingClientRect().width), avail: Math.round(avail),
                mw: getComputedStyle(el).maxWidth};
      };
      const of = s => { const el = document.querySelector(s); const cs = getComputedStyle(el);
        return [cs.textIndent, cs.fontSize]; };
      return {
        doc: w('.doc'), hero: w('.hero'), card: w('.card'), part: w('.part'),
        intro: fills('.intro'), lede: fills('.lede'), partP: fills('.part p'),
        bodyP: fills('details.more .body p.bk'), glossP: fills('.gloss dd'),
        indent: {bk: of('details.more .body p.bk'), lede: of('.lede'), intro: of('.intro'),
                 part: of('.part p'), human: of('.human'), rows: of('.rows'),
                 actionItem: of('details.more .body ol li p')},
      };
    }""")
    boxes = {col["doc"], col["hero"], col["card"], col["part"]}
    check("every block shares the 900px column", boxes == {900}, str(sorted(boxes)))
    for k in ("intro", "lede", "partP", "bodyP"):
        v = col[k]
        check(f"{k} fills its container without a width cap",
              v["w"] == v["avail"] and v["mw"] == "none", f"{v['w']} / {v['avail']} max-width={v['mw']}")
    for k in ("bk", "lede", "intro", "part"):
        ti, fs = col["indent"][k]
        check(f"{k} has a 2-character first-line indent", ti == f"{2 * float(fs[:-2]):g}px",
              f"{ti} at {fs}")
    for k in ("human", "rows", "actionItem"):
        check(f"{k} is not first-line indented", col["indent"][k][0] == "0px", col["indent"][k][0])
    check("kind chips", page.locator('[data-dim="kind"] .chip').count() == 4)
    check("mat chips", page.locator('[data-dim="mat"] .chip').count() == 4)
    check("len chips", page.locator('[data-dim="len"] .chip').count() == 3)
    check("glossary terms", page.locator("#gloss dt").count() == 24)
    page.screenshot(path=os.path.join(SHOTS, "01-desktop-full.png"), full_page=False)

    # ---- filter: kind = 可执行清单 ----
    page.click('[data-dim="kind"] .chip:has-text("可执行清单")')
    page.wait_for_timeout(250)
    n = page.locator("#list .card:visible").count()
    check("kind filter narrows list", 0 < n < 94, f"visible {n}")
    check("counter matches visible", page.locator("#cnt").inner_text().strip() == str(n))
    check("url carries filter", "kind=" in page.url, page.url)
    page.screenshot(path=os.path.join(SHOTS, "02-filter-action.png"))

    # ---- add len filter (AND across groups) ----
    page.click('[data-dim="len"] .chip:has-text("一坐")')
    page.wait_for_timeout(250)
    n2 = page.locator("#list .card:visible").count()
    check("second group is AND", n2 <= n, f"{n} -> {n2}")

    # ---- reset ----
    page.click("#reset")
    page.wait_for_timeout(250)
    check("reset restores all", page.locator("#list .card:visible").count() == 94)
    check("reset clears url", "kind=" not in page.url, page.url)

    # ---- 回归：章节目录面板必须贴着自己的按钮，不能被挤到列表末尾 ----
    panels = page.evaluate("""() => Array.from(document.querySelectorAll('.toc-sub')).map(s => ({
        for: s.dataset.for, parentId: s.parentElement.id,
        prevBtn: s.previousElementSibling && s.previousElementSibling.dataset
                 ? s.previousElementSibling.dataset.v : null }))""")
    check("every chapter panel lives inside #f-ch", len(panels) == 18 and
          all(x["parentId"] == "f-ch" for x in panels), str(len(panels)))
    check("every chapter panel follows its own button",
          all(x["prevBtn"] == x["for"] for x in panels),
          str([x for x in panels if x["prevBtn"] != x["for"]][:3]))

    # 第五章：4 节 + 1 份行动清单
    page.click('#f-ch [data-v="5"] .fold')
    page.wait_for_timeout(400)
    geom = page.evaluate("""() => {
      const sub = document.querySelector('.toc-sub[data-for="5"]');
      const btn = document.querySelector('#f-ch [data-v="5"]');
      return {gap: Math.round(sub.getBoundingClientRect().top - btn.getBoundingClientRect().bottom),
              links: sub.querySelectorAll('a[data-go]').length};
    }""")
    check("chapter 5 panel opens right under its own button", 0 <= geom["gap"] <= 12,
          f"gap {geom['gap']}px")
    check("chapter 5 panel lists its 5 units", geom["links"] == 5, str(geom["links"]))

    page.click('#f-ch [data-v="5"]')
    page.wait_for_timeout(400)
    ch5 = page.evaluate("""() => {
      const sub = document.querySelector('.toc-sub[data-for="5"]');
      return {cards: Array.from(document.querySelectorAll('#list .card')).filter(c => !c.hidden).length,
              blocks: Array.from(document.querySelectorAll('#list .sec-block')).filter(b => !b.hidden).map(b => b.id),
              noneShown: !sub.querySelector('.toc-none').hidden,
              linksHidden: Array.from(sub.querySelectorAll('a[data-go]')).filter(a => a.hidden).length,
              scrollY: Math.round(window.scrollY),
              headTop: Math.round(document.querySelector('#sec-5 .sec-h').getBoundingClientRect().top),
              appTop: Math.round(document.getElementById('sec-app').getBoundingClientRect().top)};
    }""")
    check("chapter 5 selects its 5 units", ch5["cards"] == 5, str(ch5["cards"]))
    check("chapter 5 is the only visible block", ch5["blocks"] == ["sec-5"], str(ch5["blocks"]))
    check("chapter 5 panel does not claim an empty result",
          not ch5["noneShown"] and ch5["linksHidden"] == 0, json.dumps(ch5))
    check("chapter 5 renders in the first screen, not after the appendices",
          ch5["scrollY"] == 0 and 0 < ch5["headTop"] < 950,
          f"scrollY={ch5['scrollY']} headTop={ch5['headTop']}")
    page.screenshot(path=os.path.join(SHOTS, "09-chapter-5.png"))

    # 空结果时，提示必须落在被点的那一章自己下面（第五章没有「需专注」的单元）
    page.click('[data-dim="len"] .chip:has-text("需专注")')
    page.wait_for_timeout(400)
    empty5 = page.evaluate("""() => {
      const sub = document.querySelector('.toc-sub[data-for="5"]');
      const none = sub.querySelector('.toc-none');
      const btn = document.querySelector('#f-ch [data-v="5"]');
      return {shown: !sub.hidden && !none.hidden,
              gap: Math.round(none.getBoundingClientRect().top - btn.getBoundingClientRect().bottom),
              panelsShowingIt: Array.from(document.querySelectorAll('.toc-sub'))
                .filter(s => !s.hidden && !s.querySelector('.toc-none').hidden).map(s => s.dataset.for),
              emptyState: !document.getElementById('empty').hidden,
              counter: document.getElementById('cnt').textContent};
    }""")
    check("empty-result note sits under the chapter that was clicked",
          empty5["shown"] and 0 <= empty5["gap"] <= 12 and empty5["panelsShowingIt"] == ["5"],
          json.dumps(empty5))
    check("empty result also shows the list empty state",
          empty5["emptyState"] and empty5["counter"] == "0", json.dumps(empty5))
    page.click("#reset")
    page.wait_for_timeout(300)
    page.click('#f-ch [data-v=""]')
    page.wait_for_timeout(250)

    # ---- chapter select + TOC ----
    page.click('#f-ch [data-v="3"]')
    page.wait_for_timeout(250)
    n3 = page.locator("#list .card:visible").count()
    check("chapter filter = 6", n3 == 6, f"got {n3}")
    check("only chapter 3 block visible", page.locator("#list .sec-block:visible").count() == 1)
    check("toc auto expanded", page.locator('.toc-sub[data-for="3"]').is_visible())
    page.screenshot(path=os.path.join(SHOTS, "03-chapter-3.png"))

    # ---- toc link navigation ----
    page.click('.toc-sub[data-for="3"] a[data-go="e-3-3"]')
    page.wait_for_timeout(900)
    check("toc navigation lands", page.locator("#e-3-3").is_visible())

    page.click('#f-ch [data-v=""]')
    page.wait_for_timeout(250)
    check("全部章节 restores", page.locator("#list .card:visible").count() == 94)

    # ---- search ----
    page.fill("#q", "提前还贷")
    page.wait_for_timeout(400)
    ns = page.locator("#list .card:visible").count()
    check("search finds 提前还贷", ns > 0, f"visible {ns}")
    check("search highlighted", page.locator("#list mark").count() > 0,
          f"{page.locator('#list mark').count()} marks")
    page.screenshot(path=os.path.join(SHOTS, "04-search.png"))

    page.fill("#q", "明斯基")
    page.wait_for_timeout(400)
    check("search finds 明斯基", page.locator("#list .card:visible").count() > 0)

    page.fill("#q", "zzzz-no-such-term")
    page.wait_for_timeout(400)
    check("empty state shows", page.locator("#empty").is_visible())
    page.screenshot(path=os.path.join(SHOTS, "05-empty.png"))
    page.click("#reset2")
    page.wait_for_timeout(250)
    check("empty reset works", page.locator("#list .card:visible").count() == 94)

    # ---- full text readable without JS? check details content ----
    first = page.locator("#list .card").first
    first.locator("details.more").first.click()
    page.wait_for_timeout(200)
    check("section full text expands", first.locator("details.more[open] .body p").count() > 0,
          f"{first.locator('details.more[open] .body p').count()} paragraphs")

    # ---- deep link ----
    page.goto(BASE + "#e-10-4", wait_until="load")
    page.wait_for_timeout(700)
    check("deep link card visible", page.locator("#e-10-4").is_visible())

    page.goto(BASE + "?kind=" + "%E5%8F%AF%E6%89%A7%E8%A1%8C%E6%B8%85%E5%8D%95", wait_until="load")
    page.wait_for_timeout(500)
    check("filter restored from url", page.locator("#list .card:visible").count() < 94,
          f"{page.locator('#list .card:visible').count()}")

    # ---- entry points from the existing site ----
    for src, sel in (("http://127.0.0.1:8099/zh/books.html", 'a[href="../books/survival-economics/"]'),
                     ("http://127.0.0.1:8099/books/", 'a[href="./survival-economics/"]')):
        page.goto(src, wait_until="load")
        page.wait_for_timeout(200)
        link = page.locator(sel)
        check(f"entry link present on {src.split('8099')[1]}", link.count() == 1)
        link.first.click()
        page.wait_for_timeout(900)
        check(f"entry link lands on web edition from {src.split('8099')[1]}",
              page.locator("#list .card").count() == 94, page.url)

    # ---- dark mode ----
    page.goto(BASE, wait_until="load")
    page.wait_for_timeout(400)
    page.click("#theme")
    page.wait_for_timeout(300)
    check("dark class set", page.evaluate("document.documentElement.classList.contains('dark')"))
    bg = page.evaluate("getComputedStyle(document.body).backgroundColor")
    check("dark background", bg not in ("rgb(255, 255, 255)",), bg)
    page.screenshot(path=os.path.join(SHOTS, "06-dark.png"))
    page.click("#theme")
    page.wait_for_timeout(200)
    page.evaluate("try{localStorage.removeItem('theme')}catch(e){}")

    # ---- accessibility-ish checks ----
    check("html lang", page.get_attribute("html", "lang") == "zh-CN")
    check("single h1", page.locator("h1").count() == 1)
    check("images have alt", page.evaluate(
        "Array.from(document.images).every(i => i.alt !== undefined)"))

    ctx.close()

    # ---- mobile ----
    m = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2)
    mp = m.new_page()
    cerr = []
    mp.on("pageerror", lambda e: cerr.append(str(e)))
    mp.goto(BASE, wait_until="load")
    mp.wait_for_timeout(600)
    check("mobile: no js errors", not cerr, str(cerr[:2]))
    check("mobile: drawer off-canvas", mp.evaluate(
        "document.getElementById('sidebar').getBoundingClientRect().x < 0"))
    mp.click("#menu")
    mp.wait_for_timeout(400)
    check("mobile: drawer opens", mp.evaluate(
        "document.getElementById('sidebar').classList.contains('open') "
        "&& document.getElementById('sidebar').getBoundingClientRect().x >= 0"))
    mp.screenshot(path=os.path.join(SHOTS, "07-mobile-drawer.png"))
    # 点抽屉右侧的遮罩区：遮罩中心落在抽屉里，点中心关不掉是正确行为
    mp.click("#backdrop", position={"x": 350, "y": 400})
    mp.wait_for_timeout(400)
    check("mobile: drawer closes", mp.evaluate(
        "!document.getElementById('sidebar').classList.contains('open')"))
    mp.screenshot(path=os.path.join(SHOTS, "08-mobile.png"), full_page=False)
    m.close()
    browser.close()

# ---- static checks on the file itself ----
html = open(PAGE, encoding="utf-8").read()
check("static html has all cards", html.count('<article class="card"') == 94)
n_p = html.count("<p>") + html.count("<p ")
check("static html has full text", n_p > 400, f"{n_p} paragraphs")
check("book paragraphs carry the indent class", html.count('<p class="bk">') > 350,
      str(html.count('<p class="bk">')))
check("chapter ledes carry the indent class", html.count('<p class="lede">') > 25,
      str(html.count('<p class="lede">')))
check("static chapter keys consistent", html.count('data-ch="app"') == 4, str(html.count('data-ch="app"')))
check("no placeholder braces", "{{" not in html and "%s" not in html)

print("\n".join(report))
print()
print(f"{len(report) - len(errors)}/{len(report)} checks passed")
if errors:
    print("FAILED: " + "; ".join(errors))
    sys.exit(1)
