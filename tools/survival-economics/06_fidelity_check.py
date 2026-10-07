# -*- coding: utf-8 -*-
"""Fidelity check: every manuscript paragraph and table cell must appear in the web edition.

Structural labels (part banners, chapter/section headings, 行动清单 marker) are
rendered as page chrome rather than verbatim text, so they are checked separately.
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from paths import PAGE, ITEMS

STRUCT = re.compile(
    r"^(序\u3000言|结[\u3000\s]*语|目录|"
    r"(上|中|下)[\u3000\s]*篇|"
    r"第[一二三四五六七八九十]+章|"
    r"\d{1,2}\.\d{1,2}[\u3000\s].*|"
    r"行动清单|行动\d+[\u3000\s].*|"
    r"【本章小结】|"
    r"附录[A-Z]|"
    r"B1[\u3000\s].*|B2[\u3000\s].*)$"
)


def main():
    items = json.load(open(ITEMS, encoding="utf-8"))
    page = open(PAGE, encoding="utf-8").read()
    # the page escapes & < > " in text; compare against the same escaping
    page_esc = page

    missing = []
    checked = 0
    skipped = []
    for i, it in enumerate(items):
        if it["kind"] == "table":
            for row in it["rows"]:
                for cell in row:
                    c = cell.strip()
                    if not c:
                        continue
                    checked += 1
                    if html.escape(c, quote=True) not in page_esc:
                        missing.append(("table cell", i, c[:60]))
            continue
        t = it["text"]
        if not t:
            continue
        # 行动条目在页面上是带「行动N」标签的列表项，前缀由 CSS 生成，比对去掉前缀的正文
        m = re.match(r"^行动\s*\d+[\u3000\s]+(.*)$", t, re.S)
        if m:
            t = m.group(1).strip()
        if STRUCT.match(it["text"]) and len(it["text"]) < 60 and not m:
            skipped.append(it["text"][:40])
            continue
        # 章标题下一行是章名，作为 h2 渲染，末尾可能拼接标点；按子串核对
        checked += 1
        if html.escape(t, quote=True) not in page_esc:
            missing.append(("paragraph", i, t[:80]))

    print(f"checked {checked} text units against the page")
    print(f"structural labels handled as page chrome: {len(skipped)}")
    if missing:
        print(f"\nMISSING {len(missing)}:")
        for kind, i, t in missing[:20]:
            print(f"  [{i}] {kind}: {t}")
        return 1
    print("every manuscript paragraph and table cell is present in the web edition")
    return 0


if __name__ == "__main__":
    sys.exit(main())
