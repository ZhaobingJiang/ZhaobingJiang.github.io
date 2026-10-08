# -*- coding: utf-8 -*-
"""Emit books/luck-engineering/index.html in the shared web-edition format.

The page is complete static HTML, so the book stays readable and indexable without
JavaScript; app.js only adds the filters, the search and the theme switch. Inline
equations become real <sub>/<sup>/fraction markup instead of the LaTeX the
manuscript carries in some places.
"""
import html
import json
import os
import re
import shutil
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module  # noqa: E402

from importlib import import_module  # noqa: E402

from paths import MODEL, IMAGES, SITE, PAGE as DEST, SHARED  # noqa: E402

_parse = import_module("02_parse_book")

_parse = import_module("02_parse_book")

BASE = "https://ZhaobingJiang.github.io/books/luck-engineering/"
CHARS_PER_MIN = 380
GREEK = {
    r"\lambda": "λ", r"\alpha": "α", r"\beta": "β", r"\sigma": "σ", r"\mu": "μ",
    r"\gamma": "γ", r"\pi": "π", r"\theta": "θ", r"\rho": "ρ", r"\tau": "τ",
    r"\times": "×", r"\cdot": "·", r"\in": "∈", r"\to": "→", r"\approx": "≈",
    r"\le": "≤", r"\ge": "≥", r"\neq": "≠", r"\infty": "∞", r"\sum": "Σ",
}
PART_LABEL = {"导": "导论", "一": "篇一·体系地基", "二": "篇二·五段机制",
              "三": "篇三·三层干预", "四": "篇四·闭环、边界与议程"}
PART_ORDER = ["导", "一", "二", "三", "四", "附"]
PART_INDEX = {"一": 1, "二": 2, "三": 3, "四": 4}
TAIL_LABEL = {"深水区": "深水区（进阶·可跳过）", "闭环校验（本章）": "闭环校验",
              "传统回响": "传统回响", "外部对话": "外部对话", "本章三句话": "本章三句话"}


def esc(t):
    return html.escape(t, quote=True)


# ---------------------------------------------------------------- 公式渲染
def _var(ch):
    return f"<i>{ch}</i>" if ch.isascii() and ch.isalpha() else ch


def render_latex(s):
    """$…$ 里的 LaTeX 子集：希腊字母、上下标、简单分式。"""
    for k, v in GREEK.items():
        s = s.replace(k, v)
    s = re.sub(r"\\[a-zA-Z]+", "", s)
    out, i = [], 0
    while i < len(s):
        ch = s[i]
        if ch in "_^" and i + 1 < len(s):
            j = i + 1
            if s[j] == "{":
                depth, k = 1, j + 1
                while k < len(s) and depth:
                    depth += (s[k] == "{") - (s[k] == "}")
                    k += 1
                inner = s[j + 1:k - 1]
            else:
                inner, k = s[j], j + 1
            tag = "sub" if ch == "_" else "sup"
            out.append(f"<{tag}>{render_latex(inner)}</{tag}>")
            i = k
            continue
        out.append(_var(ch))
        i += 1
    return "".join(out)


def render_math(nodes):
    """OMML 节点树 -> HTML，与 render_latex 的输出保持同一种观感。"""
    out = []
    for n in nodes:
        if isinstance(n, str):
            for k, v in GREEK.items():
                n = n.replace(k, v)
            out.append("".join(_var(c) for c in n))
        elif "sub" in n:
            out.append(f"{render_math(n['sub'][0])}<sub>{render_math(n['sub'][1])}</sub>")
        elif "sup" in n:
            out.append(f"{render_math(n['sup'][0])}<sup>{render_math(n['sup'][1])}</sup>")
        elif "frac" in n:
            out.append(f'<span class="frac"><span class="num">{render_math(n["frac"][0])}</span>'
                       f'<span class="den">{render_math(n["frac"][1])}</span></span>')
    return "".join(out)


def wrap_math(inner):
    """Long parameter enumerations arrive as one expression; wrapping each 、-separated
    piece in its own nowrap span keeps short formulas unbreakable while letting an
    enumeration wrap instead of overflowing a phone."""
    parts = inner.split("、")
    if len(parts) == 1:
        return f'<span class="eq">{inner}</span>'
    return "、".join(f'<span class="eq">{p}</span>' for p in parts if p != "")


BOLD_MARK = re.compile(r"\$([^$\n]+)\$")
ITAL = re.compile(r"\*([^*\n]{2,60})\*")


def text_html(s, bold=False, italic=False):
    """A run of literal text: $…$ becomes math, *…* becomes italics, then escaping."""
    parts, pos = [], 0
    for m in BOLD_MARK.finditer(s):
        parts.append(("t", s[pos:m.start()]))
        parts.append(("m", m.group(1)))
        pos = m.end()
    parts.append(("t", s[pos:]))
    out = []
    for kind, chunk in parts:
        if kind == "m":
            out.append(wrap_math(render_latex(chunk)))
            continue
        sub, last = [], 0
        for m in ITAL.finditer(chunk):
            sub.append(("t", chunk[last:m.start()]))
            sub.append(("i", m.group(1)))
            last = m.end()
        sub.append(("t", chunk[last:]))
        for k2, c2 in sub:
            e = esc(c2)
            if k2 == "i":
                e = f"<em>{e}</em>"
            if bold:
                e = f"<strong>{e}</strong>"
            if italic:
                e = f"<em>{e}</em>"
            out.append(e)
    return "".join(out)


def inline_html(nodes):
    out = []
    for n in nodes:
        if n["t"] == "text":
            out.append(text_html(n["v"], n.get("b", False), n.get("i", False)))
        elif n["t"] == "math":
            out.append(wrap_math(render_math(n["v"])))
    return "".join(out)


def inline_text(nodes):
    """Plain-text reading of an inline run; equations read as λ0 / A_eff, never a placeholder."""
    return "".join(n["v"] if n["t"] == "text" else _parse.math_text(n["v"]) for n in nodes)


def render_blocks(blocks):
    out = []
    for b in blocks:
        if b["t"] == "p":
            out.append(f'<p class="bk">{inline_html(b["nodes"])}</p>')
        elif b["t"] == "h4":
            out.append(f'<h4>{inline_html(b["nodes"])}</h4>')
        elif b["t"] == "mark":
            out.append('<p class="mark">【进阶 · 可跳过】</p>')
        elif b["t"] == "ul":
            out.append("<ul>" + "".join(f'<li>{inline_html(x)}</li>' for x in b["items"]) + "</ul>")
        elif b["t"] == "ol":
            out.append("<ol>" + "".join(f'<li>{inline_html(x)}</li>' for x in b["items"]) + "</ol>")
        elif b["t"] == "table":
            rows = b["rows"]
            head, body = rows[0], rows[1:]
            th = "".join(f"<th>{inline_html(c)}</th>" for c in head)
            trs = "".join("<tr>" + "".join(f"<td>{inline_html(c)}</td>" for c in r) + "</tr>"
                          for r in body)
            out.append(f'<div class="tw"><table><thead><tr>{th}</tr></thead>'
                       f'<tbody>{trs}</tbody></table></div>')
        elif b["t"] == "img":
            cap = f'<figcaption>{text_html(b["caption"])}</figcaption>' if b.get("caption") else ""
            out.append(f'<figure class="fig"><img loading="lazy" src="{esc(b["src"])}" '
                       f'alt="{esc(b.get("caption") or "插图")}">{cap}</figure>')
    return "\n".join(out)


def blocks_text(blocks):
    out = []
    for b in blocks:
        if b["t"] in ("p", "h4"):
            out.append(inline_text(b["nodes"]))
        elif b["t"] in ("ul", "ol"):
            out.extend(inline_text(x) for x in b["items"])
        elif b["t"] == "table":
            out.extend(inline_text(c) for r in b["rows"] for c in r)
        elif b["t"] == "img" and b.get("caption"):
            out.append(b["caption"])
    return "\n".join(out)


def has_math(blocks):
    for b in blocks:
        if b["t"] in ("p", "h4") and any(n["t"] == "math" for n in b["nodes"]):
            return True
        if b["t"] in ("p", "h4") and "$" in inline_text(b["nodes"]):
            return True
        if b["t"] in ("ul", "ol") and any("$" in inline_text(x) or
                                          any(n["t"] == "math" for n in x) for x in b["items"]):
            return True
        if b["t"] == "table" and any("$" in inline_text(c) or
                                     any(n["t"] == "math" for n in c)
                                     for r in b["rows"] for c in r):
            return True
    return False


def judgement(text, limit=80):
    parts = [s for s in re.split(r"(?<=[。！？])", text) if s.strip()]
    s = parts[0] if parts else text
    if len(s) <= limit:
        return s.strip()
    cut = s[:limit]
    for sep in ("——", "：", "；", "，"):
        p = cut.rfind(sep)
        if p >= 34:
            return cut[:p + len(sep)].rstrip() + "……"
    return cut.rstrip() + "……"


def reading_time(chars):
    return max(1.0, round(chars / CHARS_PER_MIN * 2) / 2)


def minutes(chars):
    return f"{reading_time(chars):g}"


def kind_of(title, is_action=False):
    if is_action:
        return "可执行清单"
    if "可核的案例" in title:
        return "可核证据"
    if "主案例" in title:
        return "案例与直觉"
    if "产出物" in title:
        return "工具与产出物"
    return "概念与机制"


DATA_HINT = re.compile(r"\d+(?:\.\d+)?\s*(?:%|％|倍|万|亿|个百分点)|研究|统计|数据|实验|调查")


def mats_of(blocks, title, is_action=False):
    body = blocks_text(blocks)
    mats = []
    if has_math(blocks):
        mats.append("公式与参数")
    if any(b["t"] == "table" for b in blocks):
        mats.append("表格")
    if DATA_HINT.search(body):
        mats.append("可核数据")
    if is_action or "产出物" in title:
        mats.append("行动工具")
    return mats


def main():
    model = json.load(open(MODEL, encoding="utf-8"))
    images = json.load(open(IMAGES, encoding="utf-8"))
    img_by_name = {x["name"]: x for x in images}
    cover = "img/fig-cover.jpg"
    back = "img/fig-backcover.jpg"

    cards, blocks_html, groups = [], [], []

    def card_html(cid, ch_key, part, idx, title, kind, mats, tier, elems, flag, human, rows,
                  body, extra="", search_note="", title_nodes=None):
        badges = [f'<span class="badge k">{esc(kind)}</span>']
        badges += [f'<span class="badge m">{esc(m)}</span>' for m in mats]
        badges.append(f'<span class="badge l">篇幅 {esc(tier)}</span>')
        badges += [f'<span class="badge plain">{esc(e)}</span>' for e in elems]
        if flag:
            badges.append(f'<span class="badge plain">{esc(flag)}</span>')
        row_html = "".join(
            f'<div class="k">{k}</div><div class="v{" note" if k == "备注" else ""}">{esc(v)}</div>'
            for k, v in rows)
        cards.append({"id": cid, "ch": ch_key, "part": part, "title": title, "toc": idx,
                      "kind": kind, "mats": mats, "len": tier, "flag": bool(flag),
                      "table": bool(elems)})
        return f"""<article class="card" id="{cid}" data-ch="{esc(ch_key)}" data-part="{esc(part)}" data-kind="{esc(kind)}" data-mats="{esc('|'.join(mats))}" data-len="{esc(tier)}" data-flag="{1 if flag else 0}" data-table="{1 if elems else 0}" data-search="{esc(search_note)}">
  <div class="card-h"><span class="idx">{esc(idx)}</span><h3>{inline_html(title_nodes) if title_nodes else esc(title)}</h3><a class="anchor" href="#{cid}" aria-label="本单元固定链接">#</a></div>
  <div class="badges">{''.join(badges)}</div>
  <p class="human">{esc(human)}</p>
  <div class="rows">{row_html}</div>
  <details class="more"><summary>本节全文<span class="cnt"> · {esc(rows[0][1].split(' · ')[0])}</span></summary>
    <div class="body">
{body}
    </div>
  </details>
{extra}
</article>"""

    def make_card(cid, ch_key, part, idx, title, blocks, ch_title="", is_action=False,
                  flag_label="", note="", search_note="", actions=False, title_nodes=None):
        kind = kind_of(title, is_action)
        mats = mats_of(blocks, title, is_action)
        chars = len(re.sub(r"\s", "", blocks_text(blocks)))
        tier = "一坐" if chars <= 1200 else "一会儿" if chars <= 1800 else "需专注"
        elems = ["含表"] if any(b["t"] == "table" for b in blocks) else []
        body = render_blocks(blocks)
        if actions:
            body = "<ol>" + "".join(
                f'<li>{inline_html(b["nodes"])}</li>' for b in blocks if b["t"] == "p") + "</ol>"
            body += "".join(f'<p class="bk">{inline_html(b["nodes"])}</p>'
                            for b in blocks if b["t"] in ("ul", "ol"))
        first = next((inline_text(b["nodes"]) for b in blocks if b["t"] == "p"), "")
        rows = [
            ("成本", f"约 {chars:,} 字 · 约 {minutes(chars)} 分钟 · 不需要任何数学基础"
                     if not has_math(blocks) else
                     f"约 {chars:,} 字 · 约 {minutes(chars)} 分钟 · 含公式，附人话翻译"),
            ("结构", " · ".join([f"{sum(1 for b in blocks if b['t'] == 'p')} 段"] +
                               (["含小标题"] if any(b["t"] == "h4" for b in blocks) else []) +
                               (["含表"] if elems else []) +
                               (["含插图"] if any(b["t"] == "img" for b in blocks) else []))),
            ("备注", note or (f"出自《{ch_title}》" if ch_title else "数据与口径以书稿为准")),
        ]
        extra = ""
        tail = [b for b in blocks if False]
        return card_html(cid, ch_key, part, idx, title, kind, mats, tier, elems, flag_label,
                         judgement(first), rows, body, extra, search_note, title_nodes)

    # ---------------- 前言 ----------------
    pref = model["preface"]
    pref_cards = []
    for i, sec in enumerate(pref["sections"]):
        cid = f"e-0-{i + 1}"
        pref_cards.append(make_card(
            cid, "0", "序", sec["num"], sec["title"], sec["blocks"], pref["title"],
            note="《前言　为什么写这本书》", search_note="前言", title_nodes=sec.get("tnodes")))
    pre_epi = (f'<p class="epigraph">{text_html(pref["epigraph"])}</p>'
               if pref.get("epigraph") else "")
    blocks_html.append(
        f'<section class="sec-block" id="sec-0" data-ch="0" data-part="序">\n'
        f'  <div class="sec-h"><span class="kicker">前言</span><h2>{esc(pref["title"])}</h2>'
        f'<span class="shown"><span class="k">{len(pref_cards)}</span> / {len(pref_cards)}</span></div>\n'
        + pre_epi + "\n" + "\n".join(pref_cards) + "\n</section>")
    groups.append({"key": "0", "label": "前言", "cards": [c["id"] for c in cards if c["ch"] == "0"]})

    # ---------------- 四篇 + 十七章 ----------------
    seen = set()
    for ch in model["chapters"]:
        if ch["part"] in PART_INDEX and ch["part"] not in seen:
            seen.add(ch["part"])
            p = next(x for x in model["parts"] if x["key"] == ch["part"])
            pn = PART_INDEX[p["key"]]
            part_cap = next((x.get("caption", "") for x in p["blocks"] if x["t"] == "img"), "")
            blocks_html.append(
                f'<section class="part" id="part-{esc(p["key"])}" data-part="{esc(p["key"])}">'
                f'<span class="p-k">{esc(PART_LABEL[p["key"]])}</span>'
                f'<h2>{esc(p["title"].split(chr(0x3000))[-1])}</h2>'
                f'<figure class="fig"><img loading="lazy" src="img/fig-part{pn}.jpg" '
                f'alt="{esc(p["caption"] or p["name"])}">'
                + (f'<figcaption>{text_html(part_cap)}</figcaption>' if part_cap else "")
                + "</figure>"
                + "".join(f'<p class="bk">{inline_html(x["nodes"])}</p>' for x in p["blocks"]
                          if x["t"] == "p" and "本篇" in inline_text(x["nodes"]))
                + "".join('<ul class="part-inc">' + "".join(
                    f'<li>{inline_html(x)}</li>' for x in x2["items"]) + "</ul>"
                    for x2 in p["blocks"] if x2["t"] == "ul")
                + "</section>")

        parts = []
        if ch.get("hero"):
            hero = f"img/fig-{ch['num']}-1.jpg"
            cap = f'<figcaption>{text_html(ch["caption"])}</figcaption>' if ch["caption"] else ""
            parts.append(f'<figure class="fig"><img loading="lazy" src="{esc(hero)}" '
                         f'alt="{esc(ch["caption"] or ch["name"])}">{cap}</figure>')
        if ch.get("epigraph"):
            parts.append(f'<p class="epigraph">{text_html(ch["epigraph"])}</p>')
        for b in ch["opening"]:
            if b["t"] == "p":
                parts.append(f'<p class="lede">{inline_html(b["nodes"])}</p>')

        ch_cards = []
        for sec in ch["sections"]:
            slot = sec["num"].split(".")[1] if sec["num"] else str(len(ch_cards) + 1)
            cid = f"e-{ch['num']}-{slot}"
            ch_cards.append(make_card(
                cid, str(ch["num"]), ch["part"], sec["num"], sec["title"], sec["blocks"],
                ch["title"], flag_label="主案例" if "主案例" in sec["title"] else "",
                note=f"《{ch['title']}》", title_nodes=sec.get("tnodes")))
        if ch["action"]:
            cid = f"e-{ch['num']}-A"
            ch_cards.append(make_card(
                cid, str(ch["num"]), ch["part"], "行动",
                f"第{ch['num']}章　你能马上做的一件事", ch["action"], ch["title"],
                is_action=True, note=f"《{ch['title']}》· 本章交付的动作"))
        parts.extend(ch_cards)

        tails = ""
        for t in ch["tails"]:
            label = TAIL_LABEL.get(t["title"], t["title"])
            tails += (f'<details class="gloss"><summary>{esc(label)}</summary><div>'
                      + render_blocks(t["blocks"]) + "</div></details>")
        n = len(ch_cards)
        blocks_html.append(
            f'<section class="sec-block" id="sec-{ch["num"]}" data-ch="{ch["num"]}" '
            f'data-part="{esc(ch["part"])}">\n'
            f'  <div class="sec-h"><span class="kicker">{esc(PART_LABEL[ch["part"]])}</span>'
            f'<h2>{esc(ch["title"])}</h2>'
            f'<span class="shown"><span class="k">{n}</span> / {n}</span></div>\n'
            + "\n".join(parts) + "\n" + tails + "\n</section>")
        groups.append({"key": str(ch["num"]), "label": f"第{ch['num']}章 {ch['name'][:16]}",
                       "cards": [c["id"] for c in cards if c["ch"] == str(ch["num"])]})

    # ---------------- 附录：每个附录一个区块，键与侧栏分组一致 ----------------
    for app in model["appendices"]:
        letter = app["letter"]
        app_parts = []
        for i, sec in enumerate(app["sections"]):
            cid = f"e-{letter}-{i + 1}"
            app_parts.append(make_card(cid, letter, "附", sec["num"], sec["title"], sec["blocks"],
                                       app["title"], note=f"《{app['title']}》",
                                       title_nodes=sec.get("tnodes")))
        app_intro = "".join(f'<p class="intro">{inline_html(x["nodes"])}</p>'
                            for x in app["intro"] if x["t"] == "p")
        app_intro += "".join(f'<p class="intro">{inline_html(x)}</p>'
                             for x2 in app["intro"] if x2["t"] in ("ul", "ol") for x in x2["items"])
        blocks_html.append(
            f'<section class="sec-block" id="sec-{letter}" data-ch="{letter}" data-part="附">\n'
            f'  <div class="sec-h"><span class="kicker">附录</span><h2>{esc(app["title"])}</h2>'
            f'<span class="shown"><span class="k">{len(app_parts)}</span> / {len(app_parts)}</span></div>\n'
            + app_intro + "\n" + "\n".join(app_parts) + "\n</section>")
        groups.append({"key": letter, "label": f"附录{letter} {app['name'][:12]}",
                       "cards": [c["id"] for c in cards if c["ch"] == letter]})

    # ---------------- 侧栏 ----------------
    ALL_LABEL = {"序": "前言", "导": "导论", "附": "附录"}
    part_html = []
    for p in PART_ORDER:
        n = sum(1 for c in cards if c["part"] == p)
        if not n:
            continue
        part_html.append(f'<button class="sec-link" data-v="{p}" aria-pressed="false">'
                         f'<span class="lb">{esc(PART_LABEL.get(p) or ALL_LABEL.get(p) or p)}</span>'
                         f'<i>{n}</i></button>')
    ch_html = [f'<button class="sec-link all" data-v="" aria-pressed="true">'
               f'<span class="lb">全部章节</span><i>{len(cards)}</i></button>']
    for g in groups:
        if g.get("hidden"):
            continue
        ch_html.append(
            f'<button class="sec-link" data-v="{g["key"]}" aria-pressed="false">'
            f'<span class="lb">{esc(g["label"])}</span><i>{len(g["cards"])}</i>'
            f'<b class="fold" title="展开或收起本节目录"><svg viewBox="0 0 24 24">'
            f'<path d="m6 9 6 6 6-6" stroke-linecap="round" stroke-linejoin="round"/></svg></b></button>')
        sub = [f'<a href="#{c["id"]}" data-go="{c["id"]}"><i>{esc(c["toc"])}</i>'
               f'<span>{esc(c["title"])}</span></a>' for c in cards if c["id"] in g["cards"]]
        sub.append('<p class="toc-none" hidden>没有符合当前筛选的单元</p>')
        ch_html.append(f'<div class="toc-sub" data-for="{g["key"]}" hidden>{"".join(sub)}</div>')

    kc = Counter(c["kind"] for c in cards)
    mc = Counter(m for c in cards for m in c["mats"])
    lc = Counter(c["len"] for c in cards)
    kind_chips = "".join(
        f'<button class="chip" data-v="{esc(k)}" aria-pressed="false">{esc(k)}<em>{kc[k]}</em></button>'
        for k in ["概念与机制", "案例与直觉", "可核证据", "工具与产出物", "可执行清单"] if kc[k])
    mat_chips = "".join(
        f'<button class="chip" data-v="{esc(m)}" aria-pressed="false">{esc(m)}<em>{mc[m]}</em></button>'
        for m in ["公式与参数", "表格", "可核数据", "行动工具"] if mc[m])
    len_chips = "".join(
        f'<button class="chip" data-v="{esc(t)}" aria-pressed="false">{esc(t)}<em>{lc[t]}</em></button>'
        for t in ["一坐", "一会儿", "需专注"] if lc[t])

    body_chars = sum(len(re.sub(r"\s", "", blocks_text(
        b["blocks"]))) for ch in model["chapters"] for b in
        [{"blocks": s["blocks"]} for s in ch["sections"]] + [{"blocks": ch["action"]}])
    n_sections = sum(len(c["sections"]) for c in model["chapters"])
    napp = sum(len(a["sections"]) for a in model["appendices"])
    n_actions = sum(1 for c in model["chapters"] if c["action"])
    stat = (f'<b>{len(cards)}</b> 个可检索单元 · <b>{n_sections}</b> 节正文 + '
            f'<b>{n_actions}</b> 个「你能马上做的一件事」 · 四篇十七章 + 附录 A–G')
    footnote = (f"全书 {len(model['chapters'])} 章、{n_sections} 节，"
                f"外加 {len(model['appendices'])} 个附录共 {napp} 个条目。")

    page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(model['title'])} · {esc(model['subtitle'])} · 网页版</title>
<meta name="description" content="《{esc(model['title'])}》全文网页版：四篇十七章与附录 A–G，共 {len(cards)} 个可检索单元。按篇、章、这一节给你什么、材料与篇幅筛选，每条写明成本、结构、公式与出处。作者：{esc(model['author'])}。">
<meta name="keywords" content="运气工程学,江召兵,运气,机遇,暴露,识别,转化,放大,收敛,运气审计,团队造运,平台造运,验收命题">
<meta name="author" content="{esc(model['author'])}">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
<meta name="theme-color" content="#3451b2" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#1b1b1f" media="(prefers-color-scheme: dark)">
<link rel="canonical" href="{BASE}">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%233451b2'/%3E%3Ctext x='32' y='44' font-size='36' text-anchor='middle' fill='white' font-family='serif'%3E%E8%BF%90%3C/text%3E%3C/svg%3E">
<meta property="og:type" content="book">
<meta property="og:site_name" content="江召兵 · 专著">
<meta property="og:locale" content="zh_CN">
<meta property="og:url" content="{BASE}">
<meta property="og:title" content="{esc(model['title'])} · 网页版">
<meta property="og:description" content="四篇十七章与附录 A–G，共 {len(cards)} 个可检索单元；含公式、量表与可复现算例。">
<meta property="og:image" content="{BASE}{cover}">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">
{{"@context":"https://schema.org","@graph":[
{{"@type":"Book","@id":"{BASE}#book","name":"{model['title']}：{model['subtitle']}","url":"{BASE}","inLanguage":"zh-CN","bookFormat":"https://schema.org/EBook","author":{{"@type":"Person","name":"{model['author']}","url":"https://ZhaobingJiang.github.io/"}},"abstract":"把偶发的幸运变成可重复实现的高概率事件：三大公设、五机制三尺度分类法、五段过程闭环、指标体系与干预工具。","isAccessibleForFree":true,"encoding":[
{{"@type":"MediaObject","contentUrl":"{BASE}../luck_engineering.pdf","encodingFormat":"application/pdf"}},
{{"@type":"MediaObject","contentUrl":"{BASE}../luck_engineering.docx","encodingFormat":"application/vnd.openxmlformats-officedocument.wordprocessingml.document"}}]}},
{{"@type":"WebSite","@id":"{BASE}#website","url":"{BASE}","name":"{model['title']}（网页版）","inLanguage":"zh-CN"}}]}}
</script>
<script>(function(){{try{{var s=localStorage.getItem('theme');var d=s?s==='dark':matchMedia('(prefers-color-scheme: dark)').matches;if(d)document.documentElement.classList.add('dark')}}catch(e){{}}}})();</script>
<link rel="stylesheet" href="style.css">
</head>
<body>
<header class="nav">
  <div class="nav-in">
    <a class="title" href="./"><span class="logo">运</span><span>{esc(model['title'])}</span></a>
    <div class="search">
      <svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
      <input id="q" type="search" placeholder="搜索 {n_sections} 节正文与 {len(model['appendices'])} 个附录，例如：机会到达率 / 换域 / 尾部风险" autocomplete="off" spellcheck="false">
      <kbd>/</kbd>
    </div>
    <div class="nav-r">
      <a class="icon-btn" href="../../zh/books.html" title="返回专著列表" aria-label="返回专著列表">
        <svg viewBox="0 0 24 24"><path d="M20 11H7.8l5.6-5.6L12 4l-8 8 8 8 1.4-1.4L7.8 13H20z"/></svg>
      </a>
      <button class="switch" id="theme" title="切换深色模式" aria-label="切换深色模式">
        <span class="knob"><svg class="sun" viewBox="0 0 24 24"><path d="M12 17a5 5 0 1 0 0-10 5 5 0 0 0 0 10zm0 2a1 1 0 0 1 1 1v1a1 1 0 0 1-2 0v-1a1 1 0 0 1 1-1zm0-20a1 1 0 0 1 1 1v1a1 1 0 0 1-2 0V1a1 1 0 0 1 1-1zM3 12a1 1 0 0 1 1-1h1a1 1 0 0 1 0 2H4a1 1 0 0 1-1-1zm16 0a1 1 0 0 1 1-1h1a1 1 0 0 1 0 2h-1a1 1 0 0 1-1-1z"/></svg><svg class="moon" viewBox="0 0 24 24"><path d="M12.5 2a9.5 9.5 0 1 0 8.9 12.8A8 8 0 0 1 12.5 2z"/></svg></span>
      </button>
      <button class="icon-btn menu-btn" id="menu" aria-label="打开目录" aria-expanded="false">
        <svg viewBox="0 0 24 24"><path d="M3 6h18v2H3zM3 11h18v2H3zM3 16h18v2H3z"/></svg>
      </button>
    </div>
  </div>
</header>

<aside class="sidebar" id="sidebar">
  <div class="group">
    <div class="gt">篇 <small>四篇 + 前言与附录</small></div>
    <div class="sec-links" data-dim="part">{''.join(part_html)}</div>
  </div>
  <div class="group">
    <div class="gt">章节 <small>点箭头看本节目录</small></div>
    <div class="sec-links" id="f-ch" data-dim="ch">{''.join(ch_html)}</div>
  </div>
  <div class="group">
    <div class="gt">这一节给你什么 <small>可多选</small></div>
    <div class="chips" data-dim="kind">{kind_chips}</div>
  </div>
  <div class="group">
    <div class="gt">材料 <small>正文里实际出现的</small></div>
    <div class="chips" data-dim="mat">{mat_chips}</div>
  </div>
  <div class="group">
    <div class="gt">篇幅 <small>按正文字数</small></div>
    <div class="chips" data-dim="len">{len_chips}</div>
  </div>
  <div class="group">
    <label class="toggle"><input type="checkbox" id="f-flag">只看「主案例」</label>
    <label class="toggle"><input type="checkbox" id="f-table">只看含表格的单元</label>
    <button class="reset" id="reset">清空筛选</button>
  </div>
  <p class="hint">
    章节单选，其余可多选；同一组内是「或」，不同组之间是「且」。每章内按原书顺序排，检索不改变顺序。
  </p>
  <p class="doc-links">
    <a href="../luck_engineering.pdf">PDF 全文</a>
    <a href="../luck_engineering.docx" download>DOCX</a>
    <a href="../../zh/books.html">返回专著页</a>
  </p>
</aside>
<div class="backdrop" id="backdrop"></div>

<main class="content">
  <div class="doc">
    <div class="doc-head">
      <h1>{esc(model['title'])}</h1>
      <p>{esc(model['subtitle'])}</p>
      <p class="stat">{stat}</p>
    </div>

    <div class="cover">
      <img src="{cover}" alt="《{esc(model['title'])}》封面" loading="lazy">
      <div class="cv-t">
        <b>{esc(model['author'])} 著 · {esc(model['edition'])}</b>
        全书四篇十七章：篇一立三大公设与分类法，篇二拆五段机制（暴露、识别、转化、放大、收敛），
        篇三给三层干预（个人、团队、平台），篇四交付验收命题与边界。每章开头三句话说完结论，
        正文一图一例一段推进，章末给出「你能马上做的一件事」。
        本页把全书拆成 {len(cards)} 个可检索单元：上方搜索，左侧按篇、章、收益、材料与篇幅筛选，点开每条即可读全文。
      </div>
    </div>

    <p class="intro">每一条都回答三个问题：这一节讲什么、读完你能拿走什么、有没有公式、有没有表格。左边把「这一节给你什么」选「工具与产出物」、「篇幅」选「一坐」，剩下的就是今晚就能读完并且上手的那几条。</p>
    <p class="intro">全书的公式都在这里排好了：行内公式用下标与分式排版，旁边保留书稿里的人话翻译与算例。附录 A–G（术语与符号表、工具包、可复现算例、学术对话表、审计表、案例库、速查表）也拆成条目，读到哪一章都可以回来查。</p>
    <p class="intro">当前显示 <b id="cnt">{len(cards)}</b> 条，共 {len(cards)} 条。{footnote}正文与标签全部来自书稿，正文未作删改。</p>

    <div id="list">
{chr(10).join(blocks_html)}
    </div>

    <div class="empty" id="empty" hidden>
      没有符合当前筛选的单元。<button type="button" id="reset2">清空筛选</button>
    </div>

    <details class="gloss" id="gloss">
      <summary>术语与符号速查（取自附录 A）</summary>
      <div class="glossary-body">读到不认识的符号时回到这里。完整表见下方附录 A 单元，量纲说明见 A.4。</div>
    </details>

    <div class="foot">
      <p>《{esc(model['title'])}：{esc(model['subtitle'])}》 {esc(model['author'])} 著 · {esc(model['edition'])}。</p>
      <p>本书是一门学科的奠基之作：给出公设、术语、分类法、模型、测量方案、干预工具与可验收命题；未核实的数字在正文中标为「待核」。网页版按 <a href="https://eternity4719.github.io/HowToLiveBetter/" target="_blank" rel="noopener">HowToLiveBetter</a> 的版式组织，正文未作删改。</p>
      <p><a href="../luck_engineering.pdf">下载 PDF 全文</a> · <a href="../luck_engineering.docx" download>下载 DOCX</a> · <a href="../../zh/books.html">返回专著页</a> · <a href="../../">江召兵个人主页</a></p>
      <img class="backcover" src="{back}" alt="《{esc(model['title'])}》封底" loading="lazy">
    </div>
  </div>
</main>

<script src="app.js"></script>
</body>
</html>
"""

    os.makedirs(SITE, exist_ok=True)
    with open(DEST, "w", encoding="utf-8") as f:
        f.write(page)
    for name in ("style.css", "app.js"):
        shutil.copyfile(os.path.join(SHARED, name), os.path.join(SITE, name))

    print(f"cards={len(cards)} html={len(page):,} bytes")
    print("kind:", dict(Counter(c["kind"] for c in cards)))
    print("len :", dict(Counter(c["len"] for c in cards)))
    print("mats:", dict(Counter(m for c in cards for m in c["mats"])))
    print("groups:", len([g for g in groups if not g.get('hidden')]))
    for g in groups:
        if not g.get("hidden"):
            print(f"   {g['key']:>4} {g['label'][:30]:<32} {len(g['cards'])}")


if __name__ == "__main__":
    sys.exit(main())
