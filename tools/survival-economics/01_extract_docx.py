# -*- coding: utf-8 -*-
"""Dump the illustrated Survival Economics DOCX into a flat text file + structure report."""
import json
import os
import re
import sys

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from paths import DOCX, ITEMS

BOOK = DOCX
OUT = os.path.dirname(os.path.abspath(__file__))


def iter_block_items(parent):
    from docx.oxml.ns import qn

    body = parent.element.body
    for child in body.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, parent)
        elif child.tag == qn("w:tbl"):
            yield Table(child, parent)


def main():
    doc = Document(BOOK)
    items = []
    for block in iter_block_items(doc):
        if isinstance(block, Paragraph):
            txt = block.text.strip()
            style = block.style.name if block.style is not None else ""
            has_img = bool(block._p.findall(".//{http://schemas.openxmlformats.org/drawingml/2006/main}blip"))
            items.append({"kind": "p", "style": style, "text": txt, "img": has_img})
        else:
            rows = []
            for row in block.rows:
                rows.append([c.text.strip() for c in row.cells])
            items.append({"kind": "table", "rows": rows})

    with open(ITEMS, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=1)

    pats = [
        re.compile(r"^第[一二三四五六七八九十百零\d]+部分"),
        re.compile(r"^第[一二三四五六七八九十百零\d]+章"),
        re.compile(r"^第[一二三四五六七八九十百零\d]+节"),
        re.compile(r"^附录[A-G]"),
        re.compile(r"^(序|前言|后记|结语|导言|目录)"),
    ]
    lines = []
    for i, it in enumerate(items):
        if it["kind"] == "table":
            lines.append(f"[{i}] <TABLE {len(it['rows'])}x{len(it['rows'][0]) if it['rows'] else 0}>")
            continue
        t = it["text"]
        mark = "IMG " if it["img"] else "    "
        hit = ""
        for p in pats:
            if t and p.match(t):
                hit = " <<HEAD>>"
                break
        lines.append(f"[{i}] {mark}{it['style']:<12} | {t[:120]}{hit}")
    with open(os.path.join(OUT, "docx_report.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("items:", len(items))
    print("non-empty paragraphs:", sum(1 for i in items if i["kind"] == "p" and i["text"]))
    print("images:", sum(1 for i in items if i["kind"] == "p" and i["img"]))
    print("tables:", sum(1 for i in items if i["kind"] == "table"))
    print("chars:", sum(len(i["text"]) for i in items if i["kind"] == "p"))


if __name__ == "__main__":
    sys.exit(main())
