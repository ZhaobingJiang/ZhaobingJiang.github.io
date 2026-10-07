# -*- coding: utf-8 -*-
"""Extract the manuscript illustrations from the DOCX into the web edition's img/ folder.

Ten drawings ship with the manuscript: front cover, eight chapter openings
(chapters 1-4, 6, 8, 10, 15) and the back cover. Chapters without a drawing get a
typographic header instead, so no artwork is invented here. Each drawing is
resampled to the width the page displays it at, which keeps the pictures small.
"""
import io
import json
import os
import sys

import docx
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from paths import DOCX, IMG, IMAGES, MODEL, ITEMS as ITEMS_JSON

BOOK = DOCX
DEST = IMG
NS = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


def web_jpeg(blob, target_w, quality=82):
    """Resample a manuscript drawing to the width the page actually displays."""
    im = Image.open(io.BytesIO(blob)).convert("RGB")
    if im.width > target_w:
        h = round(im.height * target_w / im.width)
        im = im.resize((target_w, h), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality, optimize=True, progressive=True)
    return buf.getvalue()


def iter_blocks(parent):
    body = parent.element.body
    for child in body.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, parent)
        elif child.tag == qn("w:tbl"):
            yield Table(child, parent)


def main():
    model = json.load(open(MODEL, encoding="utf-8"))
    items = json.load(open(ITEMS_JSON, encoding="utf-8"))
    doc = docx.Document(BOOK)
    os.makedirs(DEST, exist_ok=True)
    parts = doc.part.related_parts

    blips = {}
    for i, block in enumerate(iter_blocks(doc)):
        if not isinstance(block, Paragraph):
            continue
        found = block._p.findall(f".//{NS}blip")
        if found:
            blips[i] = found[0].get(qn("r:embed"))

    positions = [i for i, it in enumerate(items) if it["kind"] == "p" and it.get("img")]
    assert positions == sorted(blips), (positions, sorted(blips))

    hero_chapters = [ch["num"] for ch in model["chapters"] if ch["hero"]]
    assert len(positions) == len(hero_chapters) + 2, (len(positions), len(hero_chapters))

    out = {"cover": None, "backcover": None, "heroes": {}}
    cover_w = {0: 560, len(positions) - 1: 660}   # 封面在页头 150px、封底在页脚 220px
    for k, pos in enumerate(positions):
        rid = blips[pos]
        part = parts[rid]
        ext = os.path.splitext(str(part.partname))[1].lower() or ".png"
        if k == 0:
            name = "fig-cover" + ext
            out["cover"] = name
        elif k == len(positions) - 1:
            name = "fig-backcover" + ext
            out["backcover"] = name
        else:
            chn = hero_chapters[k - 1]
            name = f"fig-ch{chn:02d}" + ext
            out["heroes"][chn] = name
        target_w = cover_w.get(k, 1200)   # 章首插图在正文里最宽 900px
        data = web_jpeg(part.blob, target_w)
        with open(os.path.join(DEST, name), "wb") as f:
            f.write(data)
        print(f"block {pos:>4} -> {name:<18} {len(data):>9,} bytes  ({part.partname} -> {target_w}px)")

    json.dump(out, open(IMAGES, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("hero chapters:", sorted(out["heroes"]))


if __name__ == "__main__":
    sys.exit(main())
