# -*- coding: utf-8 -*-
"""Turn the Luck Engineering DOCX dump into the structured book model.

Chapter anatomy, as the manuscript lays it out:
  Heading 2 第N章　标题
    image + 图 N-1 caption, optional 【题记】
    Heading 3 三句话开篇        -> chapter opening
    Heading 3 N.M 标题 ...      -> one card each
    Heading 3 深水区 / 闭环校验（本章）/ 传统回响 / 外部对话 / 本章三句话  -> chapter footer
    Heading 3 你能马上做的一件事 -> the action card
Parts are Heading 1 banners; appendices are Heading 2 with A.1-style Heading 3 sections.
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

CH = re.compile(r"^第\s*(\d+)\s*章[\s\u3000]+(.+)$")
APP = re.compile(r"^附录\s*([A-Z])[\s\u3000]+(.+)$")
PART = re.compile(r"^篇\s*([一二三四五六七八九十])[\s\u3000]+(.+)$")
PREFACE = re.compile(r"^前言[\s\u3000]+(.+)$")
SEC = re.compile(r"^(\d{1,2}\.\d{1,2})[\s\u3000]+(.+)$")
APPSEC = re.compile(r"^([A-Z]\.\d{1,2})[\s\u3000]+(.+)$")
PREF_SEC = re.compile(r"^[一二三四五六七八九十]+、\S")
CAPTION = re.compile(r"^(图\s*[\dA-Z]+[-–]\d+|篇[一二三四]插图[:：])")

OPENING = "三句话开篇"
ACTION = "你能马上做的一件事"
SUMMARY = "本章三句话"
TAILS = ("深水区", "闭环校验（本章）", "传统回响", "外部对话", SUMMARY)
# 出版文件里的排版残留：篇首页底稿页与导论标记页，两页都不是正文
DROP_HEADS = ("篇首页（四篇导语）", "导论")
DROP_PARAS = ("排版说明：本文件为四个篇首页的内容底稿", "（第1章，不入篇）")

UL = re.compile(r"^[-*]\s+(.+)$", re.S)
OL = re.compile(r"^(\d+)[.、]\s+(.+)$", re.S)


GREEK = {"\\lambda": "λ", "\\alpha": "α", "\\beta": "β", "\\sigma": "σ", "\\mu": "μ",
         "\\gamma": "γ", "\\pi": "π", "\\theta": "θ", "\\rho": "ρ", "\\tau": "τ",
         "\\times": "×", "\\cdot": "·", "\\in": "∈", "\\to": "→", "\\approx": "≈"}


def math_text(nodes):
    """Plain-text reading of an equation: λ0, A_eff, p_det — used in titles, labels and search."""
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


def text_of(nodes):
    out = []
    for n in nodes:
        if n["t"] == "text":
            out.append(n["v"])
        elif n["t"] == "math":
            out.append(math_text(n["v"]))
    return "".join(out)


def blank(it):
    """True only for a paragraph with neither text nor an image.

    text_of() no longer marks images (they used to appear as ⟨img⟩ and leak into
    titles), so emptiness has to be judged on both text and the image flag.
    """
    return (it["kind"] == "p" and not text_of(it["nodes"]).strip() and not it.get("img"))


def blocks_of(items, lo, hi, drop_captions=False):
    """Convert items[lo:hi] into renderable blocks, grouping lists and captions."""
    blocks = []
    i = lo
    while i < hi:
        it = items[i]
        if it["kind"] == "table":
            blocks.append({"t": "table", "rows": it["rows"]})
            i += 1
            continue
        nodes = it["nodes"]
        txt = text_of(nodes).strip()
        if it["img"]:
            # 记下图片自己的序号：下面为了吃掉图注会把 i 前移，之后再查图名就查错了
            img_i = i
            cap = ""
            j = i + 1
            while j < hi and blank(items[j]):
                j += 1
            if j < hi and items[j]["kind"] == "p" and not items[j].get("img"):
                nxt = text_of(items[j]["nodes"]).strip()
                if CAPTION.match(nxt) or nxt.startswith("图 "):
                    cap = nxt
                    i = j
            blocks.append({"t": "img", "src": f"img/{IMG_SRC[img_i]}" if img_i in IMG_SRC else "",
                           "idx": img_i, "caption": cap})
            i += 1
            continue
        # strip images that ride inside a paragraph of text
        if any(n["t"] == "img" for n in nodes):
            nodes = [n for n in nodes if n["t"] != "img"]
            txt = text_of(nodes).strip()
            if not txt:
                i += 1
                continue
        if not txt:
            i += 1
            continue
        if it["style"] == "Heading 4":
            blocks.append({"t": "h4", "nodes": nodes})
            i += 1
            continue
        if txt == "【进阶 · 可跳过】":
            blocks.append({"t": "mark"})
            i += 1
            continue
        m = UL.match(txt)
        m2 = OL.match(txt)
        if m or m2:
            kind = "ul" if m else "ol"
            entry = nodes
            # 去掉行首的项目符号
            first = entry[0]
            if first["t"] == "text":
                cut = 2 if m else len(m2.group(1)) + 2
                first = dict(first, v=first["v"][cut:])
            items_out = [([first] + list(entry[1:]))]
            j = i + 1
            while j < hi and items[j]["kind"] == "p":
                t2 = text_of(items[j]["nodes"]).strip()
                if UL.match(t2) or OL.match(t2):
                    e = items[j]["nodes"]
                    f = e[0]
                    c = 2 if UL.match(t2) else len(OL.match(t2).group(1)) + 2
                    items_out.append([dict(f, v=f["v"][c:])] + list(e[1:]))
                    j += 1
                else:
                    break
            blocks.append({"t": kind, "items": items_out})
            i = j
            continue
        blocks.append({"t": "p", "nodes": nodes})
        i += 1
    return blocks


def plain(blocks):
    out = []
    for b in blocks:
        if b["t"] in ("p", "h4"):
            out.append(text_of(b["nodes"]))
        elif b["t"] in ("ul", "ol"):
            out.extend(text_of(x) for x in b["items"])
        elif b["t"] == "table":
            out.extend(c for r in b["rows"] for c in r)
    return "\n".join(out)


def main():
    items = json.load(open(ITEMS, encoding="utf-8"))
    model = {
        "title": "运气工程学",
        "subtitle": "把偶发的幸运，变成可重复实现的高概率事件",
        "edition": "第一版",
        "author": "江召兵",
        "parts": [], "chapters": [], "appendices": [], "preface": None,
        "excluded": [],
    }

    n = len(items)
    # 找结构锚点
    h1 = [i for i, it in enumerate(items) if it["kind"] == "p" and it["style"] == "Heading 1"]
    h2 = [i for i, it in enumerate(items) if it["kind"] == "p" and it["style"] == "Heading 2"]
    idx_pref = next(i for i in h1 if PREFACE.match(text_of(items[i]["nodes"]).strip()))
    idx_parts = [i for i in h1 if PART.match(text_of(items[i]["nodes"]).strip())]

    # 出版文件里的排版残留
    for i in h1:
        t = text_of(items[i]["nodes"]).strip()
        if t in DROP_HEADS:
            model["excluded"].append(t)
    model["excluded"].extend(DROP_PARAS)

    # 前言
    first_anchor = min([i for i in idx_parts] + h2)
    pref_lo = idx_pref
    pref_hi = first_anchor
    pref_title = text_of(items[pref_lo]["nodes"]).strip()
    pref_body_lo = pref_lo + 1
    pref_epigraph = ""
    if pref_body_lo < pref_hi and items[pref_body_lo]["kind"] == "p":
        t = text_of(items[pref_body_lo]["nodes"]).strip()
        if t.startswith("【题记】"):
            pref_epigraph = t
            pref_body_lo += 1
    pref_secs = []
    sec_starts = [i for i in range(pref_body_lo, pref_hi)
                  if items[i]["kind"] == "p" and items[i]["style"] == "Heading 3"]
    for k, s in enumerate(sec_starts):
        e = sec_starts[k + 1] if k + 1 < len(sec_starts) else pref_hi
        title = text_of(items[s]["nodes"]).strip()
        pref_secs.append({"num": title.split("、")[0], "title": title,
                          "tnodes": items[s]["nodes"],
                          "blocks": blocks_of(items, s + 1, e)})
    model["preface"] = {"title": pref_title, "epigraph": pref_epigraph, "sections": pref_secs}

    # 篇
    for k, s in enumerate(idx_parts):
        e = idx_parts[k + 1] if k + 1 < len(idx_parts) else h2[0]
        t = text_of(items[s]["nodes"]).strip()
        m = PART.match(t)
        body = blocks_of(items, s + 1, e)
        caption = "".join(text_of(b["nodes"]) for b in body
                          if b["t"] == "p" and "插图" in text_of(b["nodes"]))[:200]
        intro = ""
        for b in body:
            if b["t"] == "p":
                tx = text_of(b["nodes"])
                if tx.startswith("本篇任务"):
                    intro = tx
                    break
        model["parts"].append({
            "key": m.group(1), "title": t, "name": m.group(2),
            "caption": caption, "intro": intro,
            "includes": [text_of(x) for b in body if b["t"] == "ul" for x in b["items"]],
            "blocks": body,
        })

    # 章 + 附录
    # 出版文件把四个篇首页排在一起、后面才接十七章，所以章与篇的归属不能按位置判断，
    # 用每篇自己写的「本篇包含：- 第N章…」来定。第1章是导论，按书稿标注不入篇。
    part_of_chapter = {}
    for p in model["parts"]:
        for entry in p["includes"]:
            m2 = re.search(r"第\s*(\d+)\s*章", entry)
            if m2:
                part_of_chapter[int(m2.group(1))] = p["key"]
    model["intro_part"] = "导"
    cur_part = None
    for k, s in enumerate(h2):
        e = h2[k + 1] if k + 1 < len(h2) else n
        t = text_of(items[s]["nodes"]).strip()
        mc, ma = CH.match(t), APP.match(t)
        if ma:
            letter = ma.group(1)
            secs = []
            starts = [i for i in range(s + 1, e)
                      if items[i]["kind"] == "p" and items[i]["style"] == "Heading 3"]
            intro = blocks_of(items, s + 1, starts[0]) if starts else blocks_of(items, s + 1, e)
            for q, st in enumerate(starts):
                se = starts[q + 1] if q + 1 < len(starts) else e
                stitle = text_of(items[st]["nodes"]).strip()
                ms = APPSEC.match(stitle)
                secs.append({"num": ms.group(1) if ms else "", "title": stitle,
                             "tnodes": items[st]["nodes"],
                             "blocks": blocks_of(items, st + 1, se)})
            model["appendices"].append({"letter": letter, "title": t, "name": ma.group(2),
                                        "intro": intro, "sections": secs})
            continue
        if not mc:
            continue
        num = int(mc.group(1))
        cur_part = part_of_chapter.get(num, "导")
        ch = {"num": num, "title": t, "name": mc.group(2), "part": cur_part,
              "hero": None, "caption": "", "epigraph": "",
              "opening": [], "sections": [], "tails": [], "action": []}
        # 章首插图 + 图注 + 题记
        body_lo = s + 1
        j = body_lo
        while j < e and blank(items[j]):
            j += 1
        if j < e and items[j]["kind"] == "p" and items[j]["img"]:
            ch["hero"] = f"fig-ch{num:02d}"
            j += 1
            while j < e and blank(items[j]):
                j += 1
            if j < e and items[j]["kind"] == "p" and not items[j].get("img"):
                tx = text_of(items[j]["nodes"]).strip()
                if tx.startswith("图"):
                    ch["caption"] = tx
                    j += 1
        while j < e and blank(items[j]):
            j += 1
        if j < e and items[j]["kind"] == "p" and not items[j].get("img"):
            tx = text_of(items[j]["nodes"]).strip()
            if tx.startswith("【题记】"):
                ch["epigraph"] = tx
                j += 1
        # 三句话开篇
        h3 = [i for i in range(j, e)
              if items[i]["kind"] == "p" and items[i]["style"] == "Heading 3"]
        op = next((i for i in h3 if text_of(items[i]["nodes"]).strip() == OPENING), None)
        if op is not None:
            nxt = next((x for x in h3 if x > op), e)
            ch["opening"] = blocks_of(items, op + 1, nxt)
            h3 = [x for x in h3 if x != op]
        # 正文小节
        tail_at = e
        for x in h3:
            if text_of(items[x]["nodes"]).strip() in TAILS + (ACTION,):
                tail_at = x
                break
        for q, st in enumerate(h3):
            if st >= tail_at:
                break
            title = text_of(items[st]["nodes"]).strip()
            ms = SEC.match(title)
            se = h3[q + 1] if q + 1 < len(h3) else tail_at
            se = min(se, tail_at)
            ch["sections"].append({"num": ms.group(1) if ms else "", "title": title,
                                   "tnodes": items[st]["nodes"],
                                   "blocks": blocks_of(items, st + 1, se)})
        # 章尾固定块
        for q, st in enumerate(h3):
            if st < tail_at:
                continue
            title = text_of(items[st]["nodes"]).strip()
            se = h3[q + 1] if q + 1 < len(h3) else e
            blk = blocks_of(items, st + 1, se)
            if title == ACTION:
                ch["action"] = blk
            else:
                ch["tails"].append({"title": title, "blocks": blk})
        model["chapters"].append(ch)

    json.dump(model, open(MODEL, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    nsec = sum(len(c["sections"]) for c in model["chapters"])
    print(f"preface sections={len(model['preface']['sections'])} parts={len(model['parts'])} "
          f"chapters={len(model['chapters'])} sections={nsec} appendices={len(model['appendices'])}")
    for c in model["chapters"]:
        print(f"  ch{c['num']:>2} [{c['part']}] sec={len(c['sections']):>2} "
              f"tail={len(c['tails'])} action={len(c['action'])} hero={bool(c['hero'])} :: {c['name'][:34]}")


if __name__ == "__main__":
    sys.exit(main())
