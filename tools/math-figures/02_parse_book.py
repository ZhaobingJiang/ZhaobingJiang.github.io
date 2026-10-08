# -*- coding: utf-8 -*-
"""Turn the math-figures DOCX into the book model.

Anatomy: Heading 1 marks 序章, the seven 篇, the fifty chapters, 尾声 and 附录;
every chapter then repeats the same six Heading 2 sections (引子之问 / 图形导览 /
数学原理 / 设计应用 / 数学家故事 / 点评). One card per Heading 2 gives 307 units,
and the six recurring names become the page's "这一节给你什么" filter.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import ITEMS, MODEL, IMAGES  # noqa: E402

IMG_SRC = {}
if os.path.exists(IMAGES):
    IMG_SRC = {x["idx"]: x["name"] for x in json.load(open(IMAGES, encoding="utf-8"))}

CH = re.compile(r"^第\s*(\d+)\s*章[\s\u3000]*(.+)$")
PART = re.compile(r"^第([一二三四五六七])篇[\s\u3000]*(.+)$")
PROLOGUE = re.compile(r"^序章[\s\u3000]*(.+)$")
EPILOGUE = re.compile(r"^尾声[\s\u3000]*(.+)$")
APPENDIX = re.compile(r"^书末附录[:：]?\s*(.*)$")
TOCLINE = re.compile(r"^(.*?)[\s\u3000]*\.{0,}\s*(\d+)$")

# 六个固定小节名 -> 页面上的「这一节给你什么」
KIND = {
    "引子之问": "引子之问",
    "图形导览": "图形导览",
    "数学原理": "数学原理",
    "设计应用": "设计应用",
    "数学家故事": "数学家故事",
    "点评": "点评",
}


def text_of(nodes):
    out = []
    for n in nodes:
        if n["t"] == "text":
            out.append(n["v"])
        elif n["t"] == "math":
            out.append(math_text(n["v"]))
    return "".join(out)


GREEK = {"\\lambda": "λ", "\\alpha": "α", "\\beta": "β", "\\sigma": "σ", "\\mu": "μ",
         "\\gamma": "γ", "\\pi": "π", "\\theta": "θ", "\\rho": "ρ", "\\tau": "τ",
         "\\varphi": "φ", "\\phi": "φ", "\\times": "×", "\\cdot": "·", "\\in": "∈",
         "\\to": "→", "\\approx": "≈", "\\infty": "∞", "\\sum": "Σ", "\\sqrt": "√"}


def math_text(nodes):
    out = []
    for n in nodes:
        if isinstance(n, str):
            for k, v in GREEK.items():
                n = n.replace(k, v)
            out.append(re.sub(r"\\[a-zA-Z]+", "", n))
        elif "sub" in n:
            out.append(math_text(n["sub"][0]) + "_" + math_text(n["sub"][1]))
        elif "sup" in n:
            out.append(math_text(n["sup"][0]) + "^" + math_text(n["sup"][1]))
        elif "frac" in n:
            out.append(math_text(n["frac"][0]) + "/" + math_text(n["frac"][1]))
    return "".join(out)


def blank(it):
    return it["kind"] == "p" and not text_of(it["nodes"]).strip() and not it.get("img")


UL = re.compile(r"^[-•·]\s*(.+)$", re.S)
OL = re.compile(r"^(\d+)[.、]\s*(.+)$", re.S)


def blocks_of(items, lo, hi):
    blocks, i = [], lo
    while i < hi:
        it = items[i]
        if it["kind"] == "table":
            blocks.append({"t": "table", "rows": it["rows"]})
            i += 1
            continue
        nodes, txt = it["nodes"], text_of(it["nodes"]).strip()
        if it["img"]:
            blocks.append({"t": "img", "src": f"img/{IMG_SRC[i]}" if i in IMG_SRC else "",
                           "idx": i})
            i += 1
            continue
        if any(n["t"] == "img" for n in nodes):
            nodes = [n for n in nodes if n["t"] != "img"]
            txt = text_of(nodes).strip()
            if not txt:
                i += 1
                continue
        if not txt:
            i += 1
            continue
        if it["style"] == "Heading 3":
            blocks.append({"t": "h4", "nodes": nodes})
            i += 1
            continue
        m, m2 = UL.match(txt), OL.match(txt)
        if m or m2:
            cut = 2 if m else len(m2.group(1)) + 2
            first = dict(nodes[0], v=nodes[0]["v"][cut:])
            entry = [[first] + list(nodes[1:])]
            j = i + 1
            while j < hi and items[j]["kind"] == "p":
                t2 = text_of(items[j]["nodes"]).strip()
                mm, mm2 = UL.match(t2), OL.match(t2)
                if not (mm or mm2):
                    break
                c = 2 if mm else len(mm2.group(1)) + 2
                e = items[j]["nodes"]
                entry.append([dict(e[0], v=e[0]["v"][c:])] + list(e[1:]))
                j += 1
            blocks.append({"t": "ul" if m else "ol", "items": entry})
            i = j
            continue
        blocks.append({"t": "p", "nodes": nodes})
        i += 1
    return blocks


def main():
    items = json.load(open(ITEMS, encoding="utf-8"))
    model = {"title": "史上最美数学图形", "subtitle": "科学与艺术的结合",
             "author": "江召兵", "parts": [], "units": [], "toc": []}

    # 印刷目录（"toc 1" 样式）
    for it in items:
        if it["kind"] != "p" or it["style"] != "toc 1":
            continue
        t = it["text"].strip()
        m = TOCLINE.match(t)
        if m:
            model["toc"].append({"title": m.group(1).strip(), "page": int(m.group(2))})
        else:
            model["toc"].append({"title": t, "page": None})

    h1 = [i for i, it in enumerate(items) if it["kind"] == "p" and it["style"] == "Heading 1"]
    n = len(items)
    part_keys = []
    for k, s in enumerate(h1):
        e = h1[k + 1] if k + 1 < len(h1) else n
        title = text_of(items[s]["nodes"]).strip()
        mp, mc = PART.match(title), CH.match(title)
        if mp:
            key = mp.group(1)
            part_keys.append(key)
            hero = f"img/fig-part{'一二三四五六七'.index(key) + 1}.jpg"
            body = blocks_of(items, s + 1, e)
            model["parts"].append({"key": key, "title": title, "name": mp.group(2),
                                   "hero": hero, "blocks": body})
            continue
        if mc:
            key, kind, part = mc.group(1), "chapter", None
            for p in model["parts"]:
                if p["key"] not in part_keys:
                    continue
            num = int(mc.group(1))
            part = next((p["key"] for p in reversed(model["parts"])
                         if h1.index(next(i2 for i2 in h1
                                          if PART.match(text_of(items[i2]["nodes"]).strip() or "x")
                                          and PART.match(text_of(items[i2]["nodes"]).strip()).group(1) == p["key"])) < s),
                        model["parts"][0]["key"])
            unit = {"key": str(num), "kind": "chapter", "num": num, "title": title,
                    "name": mc.group(2), "part": part, "hero": f"img/fig-ch{num:02d}.jpg"}
        elif PROLOGUE.match(title):
            unit = {"key": "0", "kind": "front", "num": None, "title": title,
                    "name": PROLOGUE.match(title).group(1), "part": "序", "hero": None}
        elif EPILOGUE.match(title):
            unit = {"key": "99", "kind": "back", "num": None, "title": title,
                    "name": EPILOGUE.match(title).group(1), "part": "结", "hero": None}
        elif APPENDIX.match(title):
            unit = {"key": "app", "kind": "appendix", "num": None, "title": title,
                    "name": (APPENDIX.match(title).group(1) or "延伸阅读、图源与代码索引"),
                    "part": "附", "hero": None}
        else:
            continue
        # 到下一个 Heading 2 之前是本章的开篇（有的章先来一张插图）
        h2 = [i2 for i2 in range(s + 1, e)
              if items[i2]["kind"] == "p" and items[i2]["style"] == "Heading 2"]
        head_end = h2[0] if h2 else e
        opening = blocks_of(items, s + 1, head_end)
        # 紧跟标题的那幅图由 hero 渲染；正文里同一张不再重复出现
        if unit.get("hero"):
            while opening and opening[0]["t"] == "img":
                opening.pop(0)
        unit["opening"] = opening
        unit["sections"] = []
        for q, st in enumerate(h2):
            se = h2[q + 1] if q + 1 < len(h2) else e
            stitle = text_of(items[st]["nodes"]).strip()
            unit["sections"].append({"title": stitle, "tnodes": items[st]["nodes"],
                                     "kind": KIND.get(stitle, "其他"),
                                     "blocks": blocks_of(items, st + 1, se)})
        model["units"].append(unit)

    json.dump(model, open(MODEL, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    nsec = sum(len(u["sections"]) for u in model["units"])
    print(f"toc={len(model['toc'])} parts={len(model['parts'])} units={len(model['units'])} "
          f"sections={nsec}")
    for u in model["units"][:6] + model["units"][-3:]:
        print(f"  {u['key']:>4} [{u['part']}] sec={len(u['sections']):>2} "
              f"opening={len(u['opening'])} hero={bool(u['hero'])} :: {u['name'][:34]}")


if __name__ == "__main__":
    sys.exit(main())
