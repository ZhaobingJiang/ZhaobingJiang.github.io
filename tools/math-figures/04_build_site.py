# -*- coding: utf-8 -*-
"""Emit books/math-figures/index.html in the shared web-edition format.

One card per Heading 2 section. The book repeats the same six section names in all
fifty chapters, so those names become the page's "这一节给你什么" filter rather than
being flattened away.
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

from paths import MODEL, SITE, PAGE as DEST, SHARED  # noqa: E402

_parse = import_module("02_parse_book")

BASE = "https://ZhaobingJiang.github.io/books/math-figures/"
CHARS_PER_MIN = 380
GREEK = _parse.GREEK
PART_LABEL = {"序": "序章", "一": "第一篇·黄金与螺旋", "二": "第二篇·曲线之美",
              "三": "第三篇·分形世界", "四": "第四篇·混沌之美",
              "五": "第五篇·空间之美", "六": "第六篇·对称与镶嵌",
              "七": "第七篇·数字的图案", "结": "尾声", "附": "书末附录"}
PART_ORDER = ["序", "一", "二", "三", "四", "五", "六", "七", "结", "附"]
DATA_HINT = re.compile(r"\d+(?:\.\d+)?\s*(?:%|％|倍|万|亿|度|个)|研究|统计|数据显示|实验|论文")


def esc(t):
    return html.escape(t, quote=True)


def _var(c):
    return f"<i>{c}</i>" if c.isascii() and c.isalpha() else c


def render_latex(s):
    for k, v in GREEK.items():
        s = s.replace(k, v)
    s = re.sub(r"\\[a-zA-Z]+", "", s)
    out, i = [], 0
    while i < len(s):
        ch = s[i]
        if ch in "_^" and i + 1 < len(s):
            j = i + 1
            if s[j] == "{":
                depth, k2 = 1, j + 1
                while k2 < len(s) and depth:
                    depth += (s[k2] == "{") - (s[k2] == "}")
                    k2 += 1
                inner = s[j + 1:k2 - 1]
            else:
                inner, k2 = s[j], j + 1
            out.append(f"<{'sub' if ch == '_' else 'sup'}>{render_latex(inner)}</{'sub' if ch == '_' else 'sup'}>")
            i = k2
            continue
        out.append(_var(ch))
        i += 1
    return "".join(out)


def render_math(nodes):
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
    parts = inner.split("、")
    if len(parts) == 1:
        return f'<span class="eq">{inner}</span>'
    return "、".join(f'<span class="eq">{p}</span>' for p in parts if p != "")


MATH = re.compile(r"\$([^$\n]+)\$")
ITAL = re.compile(r"\*([^*\n]{2,60})\*")


def text_html(s, bold=False, italic=False):
    parts, pos = [], 0
    for m in MATH.finditer(s):
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
    return "".join(n["v"] if n["t"] == "text" else _parse.math_text(n["v"]) for n in nodes)


def render_blocks(blocks):
    out = []
    for b in blocks:
        if b["t"] == "p":
            out.append(f'<p class="bk">{inline_html(b["nodes"])}</p>')
        elif b["t"] == "h4":
            out.append(f'<h4>{inline_html(b["nodes"])}</h4>')
        elif b["t"] == "ul":
            out.append("<ul>" + "".join(f"<li>{inline_html(x)}</li>" for x in b["items"]) + "</ul>")
        elif b["t"] == "ol":
            out.append("<ol>" + "".join(f"<li>{inline_html(x)}</li>" for x in b["items"]) + "</ol>")
        elif b["t"] == "table":
            rows = b["rows"]
            th = "".join(f"<th>{inline_html(c)}</th>" for c in rows[0])
            trs = "".join("<tr>" + "".join(f"<td>{inline_html(c)}</td>" for c in r) + "</tr>"
                          for r in rows[1:])
            out.append(f'<div class="tw"><table><thead><tr>{th}</tr></thead>'
                       f'<tbody>{trs}</tbody></table></div>')
        elif b["t"] == "img":
            out.append(f'<figure class="fig"><img loading="lazy" src="{esc(b["src"])}" '
                       f'alt="数学图形插图"></figure>')
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
    return "\n".join(out)


def has_math(blocks):
    for b in blocks:
        if b["t"] in ("p", "h4"):
            if any(n["t"] == "math" for n in b["nodes"]) or "$" in inline_text(b["nodes"]):
                return True
        if b["t"] in ("ul", "ol") and any(
                any(n["t"] == "math" for n in x) or "$" in inline_text(x) for x in b["items"]):
            return True
        if b["t"] == "table" and any(
                any(n["t"] == "math" for n in c) or "$" in inline_text(c)
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
        if p >= 30:
            return cut[:p + len(sep)].rstrip() + "……"
    return cut.rstrip() + "……"


def minutes(chars):
    return f"{max(1.0, round(chars / CHARS_PER_MIN * 2) / 2):g}"


def main():
    model = json.load(open(MODEL, encoding="utf-8"))
    cards, blocks_html, groups = [], [], []
    cover, back = "img/fig-cover.jpg", "img/fig-ch01.jpg"

    def make_card(cid, ch_key, part, idx, title, title_nodes, blocks, unit_title, kind):
        mats = []
        if has_math(blocks):
            mats.append("含公式")
        if any(b["t"] == "img" for b in blocks):
            mats.append("含插图")
        if any(b["t"] == "table" for b in blocks):
            mats.append("含表")
        if DATA_HINT.search(blocks_text(blocks)):
            mats.append("含数据")
        chars = len(re.sub(r"\s", "", blocks_text(blocks)))
        tier = "一坐" if chars <= 250 else "一会儿" if chars <= 500 else "需专注"
        elems = []
        first = next((inline_text(b["nodes"]) for b in blocks if b["t"] == "p"), "")
        rows = [
            ("成本", f"约 {chars:,} 字 · 约 {minutes(chars)} 分钟"
                     + (" · 含公式" if has_math(blocks) else "")),
            ("结构", " · ".join([f"{sum(1 for b in blocks if b['t'] == 'p')} 段"]
                               + (["含插图"] if any(b["t"] == "img" for b in blocks) else [])
                               + (["含表"] if any(b["t"] == "table" for b in blocks) else []))),
            ("备注", f"出自《{unit_title}》"),
        ]
        cards.append({"id": cid, "ch": ch_key, "part": part, "title": title, "toc": idx,
                      "kind": kind, "mats": mats, "len": tier,
                      "flag": bool(mats and "含插图" in mats), "table": "含表" in mats})
        badges = [f'<span class="badge k">{esc(kind)}</span>']
        badges += [f'<span class="badge m">{esc(m)}</span>' for m in mats]
        badges.append(f'<span class="badge l">篇幅 {esc(tier)}</span>')
        row_html = "".join(
            f'<div class="k">{k}</div><div class="v{" note" if k == "备注" else ""}">{esc(v)}</div>'
            for k, v in rows)
        return f"""<article class="card" id="{cid}" data-ch="{esc(ch_key)}" data-part="{esc(part)}" data-kind="{esc(kind)}" data-mats="{esc('|'.join(mats))}" data-len="{esc(tier)}" data-flag="{1 if '含插图' in mats else 0}" data-table="{1 if '含表' in mats else 0}" data-search="{esc(unit_title)}">
  <div class="card-h"><span class="idx">{esc(idx)}</span><h3>{inline_html(title_nodes) if title_nodes else esc(title)}</h3><a class="anchor" href="#{cid}" aria-label="本单元固定链接">#</a></div>
  <div class="badges">{''.join(badges)}</div>
  <p class="human">{esc(judgement(first))}</p>
  <div class="rows">{row_html}</div>
  <details class="more"><summary>本节全文<span class="cnt"> · {esc(rows[0][1].split(' · ')[0])}</span></summary>
    <div class="body">
{render_blocks(blocks)}
    </div>
  </details>
</article>"""

    # ---- 序章 ----
    front = [u for u in model["units"] if u["part"] == "序"]
    seen = set()
    part_of_unit = {u["key"]: u["part"] for u in model["units"]}

    for u in model["units"]:
        # 篇首横幅
        if u["part"] in PART_LABEL and u["part"] not in seen and u["part"] in [p["key"] for p in model["parts"]]:
            seen.add(u["part"])
            p = next(x for x in model["parts"] if x["key"] == u["part"])
            blocks_html.append(
                f'<section class="part" id="part-{esc(p["key"])}" data-part="{esc(p["key"])}">'
                f'<span class="p-k">{esc(PART_LABEL[p["key"]])}</span>'
                f'<h2>{esc(p["name"])}</h2>'
                f'<figure class="fig"><img loading="lazy" src="{esc(p["hero"])}" '
                f'alt="{esc(p["name"])}"></figure>'
                + "".join(f'<p class="bk">{inline_html(x["nodes"])}</p>' for x in p["blocks"]
                          if x["t"] == "p")
                + "</section>")

        parts = []
        if u.get("hero"):
            parts.append(f'<figure class="fig"><img loading="lazy" src="{esc(u["hero"])}" '
                         f'alt="{esc(u["name"])}"></figure>')
        for b in u["opening"]:
            if b["t"] == "p":
                parts.append(f'<p class="lede">{inline_html(b["nodes"])}</p>')
            elif b["t"] == "img":
                parts.append(render_blocks([b]))

        uc = []
        for i, sec in enumerate(u["sections"]):
            cid = f"e-{u['key']}-{i + 1}"
            idx = f"{u['num']}.{i + 1}" if u["kind"] == "chapter" else str(i + 1)
            uc.append(make_card(cid, u["key"], u["part"], idx,
                                sec["title"], sec.get("tnodes"), sec["blocks"], u["title"], sec["kind"]))
        parts.extend(uc)
        n = len(uc)
        blocks_html.append(
            f'<section class="sec-block" id="sec-{esc(u["key"])}" data-ch="{esc(u["key"])}" '
            f'data-part="{esc(u["part"])}">\n'
            f'  <div class="sec-h"><span class="kicker">{esc(PART_LABEL.get(u["part"], u["part"]))}</span>'
            f'<h2>{esc(u["title"])}</h2>'
            f'<span class="shown"><span class="k">{n}</span> / {n}</span></div>\n'
            + "\n".join(parts) + "\n</section>")
        groups.append({"key": u["key"], "label": u["title"] if u["kind"] != "chapter"
                       else f"第 {u['num']} 章　{u['name'][:14]}",
                       "cards": [c["id"] for c in cards if c["ch"] == u["key"]]})

    # ---- 侧栏 ----
    part_html = []
    for p in PART_ORDER:
        n = sum(1 for c in cards if c["part"] == p)
        if not n:
            continue
        part_html.append(f'<button class="sec-link" data-v="{p}" aria-pressed="false">'
                         f'<span class="lb">{esc(PART_LABEL[p])}</span><i>{n}</i></button>')
    ch_html = [f'<button class="sec-link all" data-v="" aria-pressed="true">'
               f'<span class="lb">全部章节</span><i>{len(cards)}</i></button>']
    for g in groups:
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
    KIND_ORDER = ["引子之问", "图形导览", "数学原理", "设计应用", "数学家故事", "点评", "其他"]
    kind_chips = "".join(
        f'<button class="chip" data-v="{esc(k)}" aria-pressed="false">{esc(k)}<em>{kc[k]}</em></button>'
        for k in KIND_ORDER if kc[k])
    mat_chips = "".join(
        f'<button class="chip" data-v="{esc(m)}" aria-pressed="false">{esc(m)}<em>{mc[m]}</em></button>'
        for m in ["含公式", "含插图", "含表", "含数据"] if mc[m])
    len_chips = "".join(
        f'<button class="chip" data-v="{esc(t)}" aria-pressed="false">{esc(t)}<em>{lc[t]}</em></button>'
        for t in ["一坐", "一会儿", "需专注"] if lc[t])

    n_parts = len(model["parts"])
    n_ch = sum(1 for u in model["units"] if u["kind"] == "chapter")
    n_sec = sum(len(u["sections"]) for u in model["units"])
    n_fig = len([1 for u in model["units"] for b in u["opening"] + [x for s in u["sections"] for x in s["blocks"]] if b["t"] == "img"]) + n_parts
    stat = (f'<b>{len(cards)}</b> 个可检索单元 · <b>{n_ch}</b> 章 · <b>{n_parts}</b> 篇 · '
            f'<b>{n_fig}</b> 幅图形 · 每章固定六节')

    page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(model['title'])}：{esc(model['subtitle'])} · 网页版</title>
<meta name="description" content="《{esc(model['title'])}》全文网页版：七篇五十章、{len(cards)} 个可检索单元、{n_fig} 幅图形。按篇、章、这一节给你什么、材料与篇幅筛选，每章固定六节（引子之问、图形导览、数学原理、设计应用、数学家故事、点评）。作者：{esc(model['author'])}。">
<meta name="keywords" content="数学图形,数学之美,斐波那契螺旋,黄金分割,分形,曼德勃罗集,混沌,洛伦兹吸引子,柏拉图多面体,莫比乌斯带,埃舍尔,彭罗斯镶嵌,壁纸群,帕斯卡三角,乌拉姆螺旋,傅里叶级数">
<meta name="author" content="{esc(model['author'])}">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
<meta name="theme-color" content="#3451b2" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#1b1b1f" media="(prefers-color-scheme: dark)">
<link rel="canonical" href="{BASE}">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%233451b2'/%3E%3Ctext x='32' y='44' font-size='36' text-anchor='middle' fill='white' font-family='serif'%3E%E6%B1%9F%3C/text%3E%3C/svg%3E">
<meta property="og:type" content="book">
<meta property="og:site_name" content="江召兵 · 专著">
<meta property="og:locale" content="zh_CN">
<meta property="og:url" content="{BASE}">
<meta property="og:title" content="{esc(model['title'])} · 网页版">
<meta property="og:description" content="七篇五十章、{len(cards)} 个可检索单元、{n_fig} 幅图形，按篇、章、节名与材料筛选。">
<meta property="og:image" content="{BASE}{cover}">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">
{{"@context":"https://schema.org","@graph":[
{{"@type":"Book","@id":"{BASE}#book","name":"{model['title']}：{model['subtitle']}","url":"{BASE}","inLanguage":"zh-CN","bookFormat":"https://schema.org/EBook","numberOfPages":228,"author":{{"@type":"Person","name":"{model['author']}","url":"https://ZhaobingJiang.github.io/"}},"abstract":"五十个经典数学图形，从斐波那契螺旋到圆周率，每个图形讲清数学原理、设计应用与背后的人。","isAccessibleForFree":true,"encoding":[
{{"@type":"MediaObject","contentUrl":"{BASE}../most_beautiful_math_figures_science_and_art.pdf","encodingFormat":"application/pdf"}},
{{"@type":"MediaObject","contentUrl":"{BASE}../most_beautiful_math_figures_science_and_art.docx","encodingFormat":"application/vnd.openxmlformats-officedocument.wordprocessingml.document"}}]}},
{{"@type":"WebSite","@id":"{BASE}#website","url":"{BASE}","name":"{model['title']}（网页版）","inLanguage":"zh-CN"}}]}}
</script>
<script>(function(){{try{{var s=localStorage.getItem('theme');var d=s?s==='dark':matchMedia('(prefers-color-scheme: dark)').matches;if(d)document.documentElement.classList.add('dark')}}catch(e){{}}}})();</script>
<link rel="stylesheet" href="style.css">
</head>
<body>
<header class="nav">
  <div class="nav-in">
    <a class="title" href="./"><span class="logo">江</span><span>{esc(model['title'])}</span></a>
    <div class="search">
      <svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
      <input id="q" type="search" placeholder="搜索 {n_ch} 章 {n_sec} 节，例如：鹦鹉螺 / 曼德勃罗 / 壁纸群" autocomplete="off" spellcheck="false">
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
    <div class="gt">篇 <small>七篇 + 序章、尾声与附录</small></div>
    <div class="sec-links" data-dim="part">{''.join(part_html)}</div>
  </div>
  <div class="group">
    <div class="gt">章节 <small>点箭头看本节六节</small></div>
    <div class="sec-links" id="f-ch" data-dim="ch">{''.join(ch_html)}</div>
  </div>
  <div class="group">
    <div class="gt">这一节给你什么 <small>每章固定的六节</small></div>
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
    <label class="toggle"><input type="checkbox" id="f-flag">只看带图形的单元</label>
    <label class="toggle"><input type="checkbox" id="f-table">只看含表格的单元</label>
    <button class="reset" id="reset">清空筛选</button>
  </div>
  <p class="hint">
    章节单选，其余可多选；同一组内是「或」，不同组之间是「且」。每章内按原书顺序排，检索不改变顺序。
  </p>
  <p class="doc-links">
    <a href="../most_beautiful_math_figures_science_and_art.pdf">PDF 全文</a>
    <a href="../most_beautiful_math_figures_science_and_art.docx" download>DOCX</a>
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
        <b>{esc(model['author'])} 著</b>
        五十个经典数学图形，分七篇：黄金与螺旋、曲线之美、分形世界、混沌之美、空间之美、对称与镶嵌、数字的图案。
        每一章都按同样的六节展开——引子之问、图形导览、数学原理、设计应用、数学家故事、点评；
        全书 {n_fig} 幅图形，每章都给出可直接复现的绘图方法。
        本页把全书拆成 {len(cards)} 个可检索单元：上方搜索，左侧按篇、章、节名、材料与篇幅筛选。
      </div>
    </div>

    <p class="intro">每一条都回答三个问题：这一节讲什么、读完你能拿走什么、有没有公式或图形。左边把「这一节给你什么」选「设计应用」，就能一次看完五十个图形在真实设计里的用法；选「数学家故事」，就是一部围绕图形展开的人物小传。</p>
    <p class="intro">全书正文与 {n_fig} 幅图形都在这一个页面里，图形按章节顺序排在与它对应的那一节，公式用下标排版。索引、延伸阅读、图源与代码索引在书末附录。</p>
    <p class="intro">当前显示 <b id="cnt">{len(cards)}</b> 条，共 {len(cards)} 条。正文与标签全部来自书稿，正文未作删改。</p>

    <div id="list">
{chr(10).join(blocks_html)}
    </div>

    <div class="empty" id="empty" hidden>
      没有符合当前筛选的单元。<button type="button" id="reset2">清空筛选</button>
    </div>

    <details class="gloss" id="gloss">
      <summary>原书目录（含原书页码，{len(model['toc'])} 条）</summary>
      <div>
        <ol class="toc-list">{''.join(f'<li>{esc(t["title"])}{"　" + str(t["page"]) if t["page"] else ""}</li>' for t in model['toc'])}</ol>
      </div>
    </details>

    <div class="foot">
      <p>《{esc(model['title'])}：{esc(model['subtitle'])}》 {esc(model['author'])} 著 · 2026 年 · 228 页 · 约 10 万字 · 七篇五十章 · {n_fig} 幅图形。</p>
      <p>网页版按 <a href="https://eternity4719.github.io/HowToLiveBetter/" target="_blank" rel="noopener">HowToLiveBetter</a> 的版式组织，正文未作删改。</p>
      <p><a href="../most_beautiful_math_figures_science_and_art.pdf">下载 PDF 全文</a> · <a href="../most_beautiful_math_figures_science_and_art.docx" download>下载 DOCX</a> · <a href="../../zh/books.html">返回专著页</a> · <a href="../../">江召兵个人主页</a></p>
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
    print("units:", len(groups), "parts:", len(model["parts"]), "toc:", len(model["toc"]))
    for g in groups[:4] + groups[-3:]:
        print(f"   {g['key']:>4} {g['label'][:32]:<34} {len(g['cards'])}")


if __name__ == "__main__":
    sys.exit(main())
