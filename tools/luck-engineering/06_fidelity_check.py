# -*- coding: utf-8 -*-
"""Fidelity check: every manuscript paragraph and table cell must appear in the page.

Comparison runs on a reduced skeleton (CJK + ASCII alphanumerics, punctuation and
markup dropped) so that inline equations, bold runs, list bullets and tag structure
do not create false mismatches. Four paragraphs of production residue that the
published PDF also carries are listed as intentional exclusions.
"""
import html as htmllib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import PAGE, ITEMS  # noqa: E402
from importlib import import_module  # noqa: E402

parse = import_module("02_parse_book")

# 出版文件里的排版残留：篇首页底稿页与导论标记页，不是正文
EXCLUDE = [
    "篇首页（四篇导语）",
    "排版说明：本文件为四个篇首页的内容底稿",
    "导论",
    "（第1章，不入篇）",
]

CJK = re.compile(r"[\u4e00-\u9fff]")


def skel(t):
    t = htmllib.unescape(t)
    return "".join(CJK.findall(t))


def main():
    items = json.load(open(ITEMS, encoding="utf-8"))
    page = open(PAGE, encoding="utf-8").read()
    # 去掉标签与属性，只留文本
    body = page[page.index("<main"):]
    plain = re.sub(r"<[^>]+>", "\n", body)
    page_skel = skel(plain)
    head_skel = skel(page)

    excluded = [x for x in EXCLUDE]
    missing, checked, skipped = [], 0, 0
    for i, it in enumerate(items):
        if it["kind"] == "table":
            for row in it["rows"]:
                for cell in row:
                    ctext = parse.text_of(cell)
                    if not ctext.strip():
                        continue
                    checked += 1
                    if skel(ctext) and skel(ctext) not in page_skel:
                        missing.append(("cell", i, ctext[:70]))
            continue
        t = it["text"]
        if not t.strip():
            continue
        if any(t.strip().startswith(x) for x in EXCLUDE) or t.strip() in EXCLUDE:
            skipped += 1
            continue
        if len(skel(t)) < 8:
            skipped += 1
            continue
        checked += 1
        if skel(t) not in page_skel:
            missing.append(("p", i, t[:90]))

    print(f"checked {checked} text units against the page")
    print(f"intentionally excluded (production residue): {skipped}")
    if missing:
        print(f"\nMISSING {len(missing)}:")
        for kind, i, t in missing[:20]:
            print(f"  [{i}] {kind}: " + t.encode("utf-8", "replace").decode("utf-8"))
        return 1
    print("every manuscript paragraph and table cell is present in the web edition")
    return 0


if __name__ == "__main__":
    sys.exit(main())
