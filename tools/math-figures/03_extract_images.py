# -*- coding: utf-8 -*-
"""Extract the 149 drawings and name them after the unit they belong to.

The book puts one picture right under each 篇 or 章 heading, and further pictures
inside the chapter's 数学原理 / 图形导览 sections. Names follow that placement:
fig-cover / fig-part N / fig-ch N / fig-<chapter>-<n> for the rest.
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
CH = re.compile(r"^第\s*(\d+)\s*章")
PART = re.compile(r"^第([一二三四五六七])篇")
COVER_W, FIG_W = 560, 1000


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

    blips, bi = {}, 0
    for block in iter_blocks(doc):
        if isinstance(block, Paragraph):
            found = block._p.findall(f".//{NS}blip")
            if found:
                blips[bi] = found[0].get(qn("r:embed"))
        bi += 1

    img_idx = [i for i, it in enumerate(items) if it["kind"] == "p" and it.get("img")]
    assert len(img_idx) == len(blips), (len(img_idx), len(blips))

    # 前面最近的一个 Heading 1，以及此后是否已经进入小节：只有「标题后、小节前」的图
    # 才是篇首或章首插图，其余都是章节内部的插图
    owner, in_section = [], []
    cur_unit, seen_h2 = None, False
    for it in items:
        if it["kind"] == "p" and it["style"] == "Heading 1":
            cur_unit, seen_h2 = it["text"].strip(), False
        elif it["kind"] == "p" and it["style"] == "Heading 2":
            seen_h2 = True
        owner.append(cur_unit)
        in_section.append(seen_h2)

    out, used, per_chapter = [], {}, {}
    for k, i in enumerate(img_idx):
        if k == 0:
            name, width = "fig-cover.jpg", COVER_W
        elif k == len(img_idx) - 1 and not CH.match(owner[i] or "") and not PART.match(owner[i] or ""):
            name, width = "fig-backcover.jpg", COVER_W
        else:
            unit = owner[i] or ""
            mp, mc = PART.match(unit), CH.match(unit)
            head_img = not in_section[i]
            if mp and head_img:
                n = "一二三四五六七".index(mp.group(1)) + 1
                name, width = f"fig-part{n}.jpg", FIG_W
            elif mc and head_img:
                name, width = f"fig-ch{int(mc.group(1)):02d}.jpg", FIG_W
            else:
                key = mc.group(1) if mc else ("front" if "序章" in unit else "back")
                per_chapter[key] = per_chapter.get(key, 0) + 1
                name = f"fig-{key}-{per_chapter[key]}.jpg"
                width = FIG_W
        if name in used:
            raise SystemExit(f"duplicate {name} at items {used[name]} / {i}")
        used[name] = i
        data = web_jpeg(parts[blips[i]].blob, width)
        with open(os.path.join(IMG, name), "wb") as f:
            f.write(data)
        out.append({"idx": i, "name": name, "unit": owner[i], "bytes": len(data)})
        print(f"[{i:>5}] {name:<20} {len(data):>8,} B  {owner[i] or ''}")

    json.dump(out, open(IMAGES, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    total = sum(x["bytes"] for x in out)
    print(f"\n{len(out)} drawings, {total / 1024 / 1024:.2f} MB -> {IMG}")


if __name__ == "__main__":
    sys.exit(main())
