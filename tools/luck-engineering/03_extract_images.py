# -*- coding: utf-8 -*-
"""Extract the manuscript drawings and name them after the figure numbers the book uses.

The DOCX labels every drawing in the paragraph right below it ("图 10-2　…",
"篇一插图：…"), so the file name can follow the book's own numbering instead of an
invented sequence. Drawings are resampled to the width the page displays.
"""
import io
import json
import os
import re
import sys

import docx
from PIL import Image
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import DOCX, IMG, IMAGES, ITEMS  # noqa: E402

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
NS = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
FIG = re.compile(r"^图\s*(\d{1,2})[-–](\d{1,2})")
PART_CAP = re.compile(r"^篇\s*([一二三四五六七八九十])插图")

HERO_W, FIG_W, PART_W, COVER_W = 1200, 1200, 1400, 560


def web_jpeg(blob, target_w, quality=82):
    im = Image.open(io.BytesIO(blob)).convert("RGB")
    if im.width > target_w:
        im = im.resize((target_w, round(im.height * target_w / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality, optimize=True, progressive=True)
    return buf.getvalue()


def iter_blocks(parent):
    for child in parent.element.body.iterchildren():
        if child.tag == f"{W}p":
            yield Paragraph(child, parent)
        elif child.tag == f"{W}tbl":
            yield Table(child, parent)


def main():
    items = json.load(open(ITEMS, encoding="utf-8"))
    doc = docx.Document(DOCX)
    parts = doc.part.related_parts
    os.makedirs(IMG, exist_ok=True)

    # 段落序号 -> 图片关系 id（与 docx_items.json 的序号一致：表格也占一个位置）
    blips, pi = {}, 0
    for block in iter_blocks(doc):
        if isinstance(block, Paragraph):
            found = block._p.findall(f".//{NS}blip")
            if found:
                blips[pi] = found[0].get(qn("r:embed"))
        pi += 1

    img_idx = [i for i, it in enumerate(items) if it["kind"] == "p" and it.get("img")]
    assert len(img_idx) == len(blips), (len(img_idx), len(blips))

    out = []
    seen = {}
    for k, i in enumerate(img_idx):
        caption = ""
        j = i + 1
        while j < len(items) and items[j]["kind"] == "p" and not items[j]["text"].strip():
            j += 1
        if j < len(items) and items[j]["kind"] == "p":
            t = items[j]["text"].strip()
            if FIG.match(t) or PART_CAP.match(t):
                caption = t
        if k == 0:
            name, width = "fig-cover.jpg", COVER_W
        elif k == len(img_idx) - 1:
            name, width = "fig-backcover.jpg", COVER_W
        elif PART_CAP.match(caption):
            zh = PART_CAP.match(caption).group(1)
            n = "一二三四五六七八九十".index(zh) + 1
            name = f"fig-part{n}.jpg"
            width = PART_W
        elif FIG.match(caption):
            g = FIG.match(caption)
            name = f"fig-{int(g.group(1))}-{int(g.group(2))}.jpg"
            width = FIG_W
        else:
            name = f"fig-extra-{k:02d}.jpg"
            width = FIG_W
        if name in seen:
            raise SystemExit(f"duplicate figure name {name} at items {seen[name]} and {i}")
        seen[name] = i
        rid = blips[i]
        data = web_jpeg(parts[rid].blob, width)
        with open(os.path.join(IMG, name), "wb") as f:
            f.write(data)
        out.append({"idx": i, "name": name, "caption": caption[:60], "bytes": len(data)})
        print(f"[{i:>5}] {name:<20} {len(data):>8,} B  {caption[:52]}")

    json.dump(out, open(IMAGES, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    total = sum(x["bytes"] for x in out)
    print(f"\n{len(out)} drawings, {total / 1024 / 1024:.2f} MB total -> {IMG}")


if __name__ == "__main__":
    sys.exit(main())
