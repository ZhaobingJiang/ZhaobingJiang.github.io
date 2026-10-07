# -*- coding: utf-8 -*-
"""Parse the flat DOCX dump into the structured book model used by the web edition.

Output: book_model.json — metadata, three parts, fifteen chapters, every section's
paragraphs, the chapter action lists, chapter notes/summaries and the appendices.
Derived card fields (first sentence, reading time, row text) are computed in
04_build_site.py so this file stays a faithful transcript of the manuscript.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from paths import ITEMS, MODEL

SRC = ITEMS
OUT = MODEL

PART_RE = re.compile(r"^(上|中|下)[\u3000\s]*篇$")
CH_RE = re.compile(r"^第([一二三四五六七八九十百零\d]+)章$")
SEC_RE = re.compile(r"^(\d{1,2})\.(\d{1,2})[\u3000\s]+(.+)$")
ACT_RE = re.compile(r"^行动\s*(\d+)[\u3000\s]+(.+)$", re.S)
APP_RE = re.compile(r"^附录([A-Z])$")
SUBHEAD_MAX = 34


def is_subhead(text, nxt):
    """A manuscript sub-head: short, unterminated, and followed by body prose."""
    if not text or len(text) > SUBHEAD_MAX:
        return False
    if text[-1] in "。！？；：,，、":
        return False
    if text.startswith(("行动", "本章说明", "【", "［", "（", "●", "·", "-")):
        return False
    return bool(nxt) and len(nxt) > 60


def blocks_of(paras):
    """Split a run of paragraphs into {type: 'p'|'h'|'table'} blocks."""
    out = []
    for i, t in enumerate(paras):
        if isinstance(t, dict):  # table placeholder from paras_between
            out.append({"t": "table", "rows": t["__table__"]})
            continue
        nxt = paras[i + 1] if i + 1 < len(paras) else ""
        if isinstance(nxt, dict):
            nxt = ""
        kind = "h" if is_subhead(t, nxt) else "p"
        out.append({"t": kind, "x": t})
    return out


def main():
    items = json.load(open(SRC, encoding="utf-8"))
    stream = [it for it in items]

    model = {
        "title": "不确定年代的生存经济学",
        "subtitle": "——写给普通人的变局观察与行动指南",
        "edition": "（第三版·黄金标准扩写稿）",
        "cover": "fig-cover.jpg",
        "backcover": "fig-backcover.jpg",
        "preface": None,
        "parts": [],
        "chapters": [],
        "appendices": [],
        "epilogue": [],
    }

    # ---- locate landmarks -------------------------------------------------
    idx_part = [i for i, it in enumerate(stream) if it["kind"] == "p" and PART_RE.match(it["text"])]
    idx_ch = [i for i, it in enumerate(stream) if it["kind"] == "p" and CH_RE.match(it["text"])]
    idx_sec = [i for i, it in enumerate(stream) if it["kind"] == "p" and SEC_RE.match(it["text"])]
    idx_app = [i for i, it in enumerate(stream) if it["kind"] == "p" and APP_RE.match(it["text"])]
    idx_pref = next(i for i, it in enumerate(stream) if it["kind"] == "p" and it["text"] == "序\u3000言")
    idx_body_start = idx_part[0]

    def span(a, b):
        return stream[a:b]

    def paras_between(a, b):
        out = []
        for it in stream[a:b]:
            if it["kind"] == "table":
                out.append({"__table__": it["rows"]})
            elif it["text"]:
                out.append(it["text"])
        return out

    # ---- preface ----------------------------------------------------------
    pref_raw = paras_between(idx_pref + 1, idx_body_start)
    model["preface"] = {"title": "序言", "blocks": blocks_of(pref_raw)}

    # ---- parts ------------------------------------------------------------
    part_bounds = []
    for k, i in enumerate(idx_part):
        end = idx_part[k + 1] if k + 1 < len(idx_part) else (idx_app[0] if idx_app else len(stream))
        part_bounds.append((i, end))
    for pi, (s, e) in enumerate(part_bounds):
        label = stream[s]["text"][0]
        head = [t for t in paras_between(s + 1, min(s + 6, e)) if t]
        title = head[0] if head else ""
        lede = head[1] if len(head) > 1 else ""
        model["parts"].append({"key": label, "title": title, "lede": lede})

    # ---- chapters ---------------------------------------------------------
    epilogue = []
    ch_bounds = []
    for k, i in enumerate(idx_ch):
        nxt = [j for j in (idx_ch + idx_part + idx_app) if j > i]
        end = min(nxt) if nxt else len(stream)
        ch_bounds.append((i, end))

    for ci, (s, e) in enumerate(ch_bounds):
        num_cn = CH_RE.match(stream[s]["text"]).group(1)
        raw = paras_between(s + 1, e)
        title = raw[0] if raw else ""
        # part membership: the nearest part landmark above this chapter
        part = model["parts"][0]["key"] if model["parts"] else None
        for pk, pi in enumerate(idx_part):
            if pi < s:
                part = stream[pi]["text"][0]
        ch = {
            "num": ci + 1,
            "numCn": num_cn,
            "part": part,
            "title": title,
            "hero": None,
            "lede": [],
            "sections": [],
            "theory": None,
            "actions": [],
            "actionNote": [],
            "note": "",
            "summary": [],
        }
        # hero image
        for it in stream[s + 1 : min(s + 4, e)]:
            if it["kind"] == "p" and it.get("img"):
                ch["hero"] = f"fig-ch{ci + 1:02d}.jpg"
                break

        # split the tail (actions / note / summary) off
        tail_at = e
        for j in range(s, e):
            it = stream[j]
            if it["kind"] == "p" and (it["text"] == "行动清单" or it["text"].startswith("本章说明") or it["text"] == "【本章小结】"):
                tail_at = j
                break
        body = paras_between(s + 1, tail_at)
        tail = paras_between(tail_at, e)

        # drop title / image placeholder / leading blanks from body
        while body and body[0] == title:
            body.pop(0)
        while body and (body[0] == "" or body[0].startswith("__")):
            body.pop(0)

        # lede = paragraphs before the first numbered section
        sec_positions = []
        for j in range(s, tail_at):
            it = stream[j]
            if it["kind"] == "p":
                m = SEC_RE.match(it["text"])
                if m:
                    sec_positions.append((j, f"{int(m.group(1))}.{int(m.group(2))}", m.group(3).strip()))
        first_sec = sec_positions[0][0] if sec_positions else tail_at
        lede_raw = paras_between(s + 1, first_sec)
        while lede_raw and (lede_raw[0] == title or lede_raw[0] == ""):
            lede_raw.pop(0)
        if ch["hero"]:
            for k, t in enumerate(lede_raw):
                if t == title:
                    del lede_raw[k]
                    break
        ch["lede"] = blocks_of(lede_raw)

        # sections
        for si, (pos, num, stitle) in enumerate(sec_positions):
            nxt = sec_positions[si + 1][0] if si + 1 < len(sec_positions) else tail_at
            sec_raw = paras_between(pos + 1, nxt)
            # theory lens heading that stands on its own (chapter 1) belongs to the chapter
            ch["sections"].append({"num": num, "title": stitle, "blocks": blocks_of(sec_raw)})

        # stand-alone 理论透镜 block: only chapter 1 carries one outside a numbered
        # section; every later chapter folds it into its X.4/X.5 section, so a
        # heading found inside a section stays there.
        sec_block_ids = {p for p, _, _ in sec_positions}
        for j in range(first_sec, tail_at):
            it = stream[j]
            if it["kind"] != "p" or not it["text"].startswith("理论透镜"):
                continue
            prev_sec = max([p for p in sec_block_ids if p < j], default=None)
            if prev_sec is not None and prev_sec >= first_sec:
                continue  # belongs to the section that started above it
            nxt = [k for k in range(j + 1, tail_at) if stream[k]["kind"] == "p" and stream[k]["text"]]
            stop = nxt[0] if nxt else tail_at
            th = paras_between(j, stop)
            ch["theory"] = {"title": th[0], "blocks": blocks_of(th[1:])}
            break

        # tail: actions / note / summary / epilogue
        cur = None
        for t in tail:
            if t == "行动清单":
                cur = "actions"
                continue
            if t.startswith("本章说明"):
                cur = "note"
                ch["note"] = t
                continue
            if t == "【本章小结】":
                cur = "summary"
                continue
            if re.match(r"^结[\u3000\s]*语$", t):
                cur = "epilogue"
                continue
            if cur == "actions":
                m = ACT_RE.match(t)
                if m:
                    ch["actions"].append({"n": int(m.group(1)), "text": m.group(2).strip()})
                else:
                    ch["actionNote"].append(t)
            elif cur == "summary":
                ch["summary"].append(t)
            elif cur == "epilogue":
                epilogue.append(t)

        model["chapters"].append(ch)

    # ---- appendices -------------------------------------------------------
    model["epilogue"] = epilogue
    for ai, i in enumerate(idx_app):
        end = idx_app[ai + 1] if ai + 1 < len(idx_app) else len(stream)
        raw = paras_between(i + 1, end)
        letter = APP_RE.match(stream[i]["text"]).group(1)
        app = {"letter": letter, "title": raw[0] if raw else "", "lede": raw[1] if len(raw) > 1 else "", "blocks": []}
        for t in raw[2:]:
            if isinstance(t, dict):
                app["blocks"].append({"t": "table", "rows": t["__table__"]})
            elif t:
                app["blocks"].append({"t": "h" if re.match(r"^B\d", t) else "p", "x": t})
        model["appendices"].append(app)

    # ---- accounting: every manuscript character must land somewhere ---------
    total = sum(len(it["text"]) for it in stream if it["kind"] == "p")
    captured = 0

    def count(t):
        return len(t) if t else 0

    captured += sum(count(b.get("x")) for b in model["preface"]["blocks"])
    for p in model["parts"]:
        captured += count(p["title"]) + count(p["lede"])
    for c in model["chapters"]:
        captured += sum(count(b.get("x")) for b in c["lede"])
        for s in c["sections"]:
            captured += sum(count(b.get("x")) for b in s["blocks"])
        if c["theory"]:
            captured += count(c["theory"]["title"]) + sum(count(b.get("x")) for b in c["theory"]["blocks"])
        captured += sum(count(a["text"]) for a in c["actions"]) + sum(count(t) for t in c["actionNote"])
        captured += count(c["note"]) + sum(count(t) for t in c["summary"])
    captured += sum(count(t) for t in model["epilogue"])
    for a in model["appendices"]:
        for b in a["blocks"]:
            if b["t"] == "table":
                captured += sum(count(cell) for row in b["rows"] for cell in row)
            else:
                captured += count(b.get("x"))
    # headings and banner labels are page chrome, not body text
    labels = sum(count(it["text"]) for it in stream if it["kind"] == "p" and
                 (CH_RE.match(it["text"]) or PART_RE.match(it["text"]) or SEC_RE.match(it["text"])
                  or APP_RE.match(it["text"]) or it["text"] in ("序\u3000言", "行动清单", "【本章小结】", "结\u3000语")))

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(model, f, ensure_ascii=False, indent=1)

    # ---- report -----------------------------------------------------------
    ns = sum(len(c["sections"]) for c in model["chapters"])
    na = sum(len(c["actions"]) for c in model["chapters"])
    chars = sum(len(b.get("x", "")) for c in model["chapters"] for s in c["sections"] for b in s["blocks"])
    print(f"parts={len(model['parts'])} chapters={len(model['chapters'])} sections={ns} actions={na} appendix={len(model['appendices'])}")
    print(f"section chars={chars}")
    print(f"accounting: docx={total:,} captured={captured:,} labels={labels:,} unaccounted={total - captured - labels:,}")
    for c in model["chapters"]:
        print(
            f"  {c['num']:>2} [{c['part']}] {c['title'][:34]:<36} sec={len(c['sections'])} "
            f"hero={'Y' if c['hero'] else '-'} theory={'Y' if c['theory'] else '-'} act={len(c['actions'])} sum={len(c['summary'])}"
        )


if __name__ == "__main__":
    sys.exit(main())
