# -*- coding: utf-8 -*-
"""Build books/survival-economics/index.html — the HowToLiveBetter-format web edition.

The page is emitted as complete static HTML so the whole book stays readable and
indexable without JavaScript; app.js only layers the sidebar filters, search and
theme switch on top of that markup.
"""
import html
import json
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from paths import MODEL as SRC, IMAGES as IMGS, SITE, PAGE as DEST, ITEMS as ITEMS_JSON
BASE = "https://ZhaobingJiang.github.io/books/survival-economics/"

CHARS_PER_MIN = 380
PART_LABEL = {"上": "上篇·变局", "中": "中篇·透镜", "下": "下篇·行动"}
PART_ORDER = ["上", "中", "下", "序", "结", "附"]
NOBEL = re.compile(r"诺贝尔|诺奖|皇家科学院")
DATA = re.compile(r"\d+(?:\.\d+)?\s*(?:%|％|万亿|亿元|万元|万套|亿美元|个百分点)|统计局|央行|官方统计|据统计|数据显示|同比")
CASE = re.compile(r"(?:^|。)(?:19|20)\d{2}年|一位|有一个|家庭主妇|退休教师|承包商|工程师|教师|老板|夫妇|家庭")
CN_NUM = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "七", 8: "八", 9: "九", 10: "十",
          11: "十一", 12: "十二", 13: "十三", 14: "十四", 15: "十五"}


def esc(t):
    return html.escape(t, quote=True)


def sent_split(t):
    return [s for s in re.split(r"(?<=[。！？])", t) if s.strip()]


def judgement(text, limit=76):
    if not text:
        return ""
    first = sent_split(text)
    s = first[0] if first else text
    if len(s) <= limit:
        return s.strip()
    cut = s[:limit]
    for sep in ("——", "：", "；", "，", "、"):
        pos = cut.rfind(sep)
        if pos >= 34:
            return cut[: pos + len(sep)].rstrip() + "……"
    return cut.rstrip() + "……"


def reading_time(chars):
    return max(1.0, round(chars / CHARS_PER_MIN * 2) / 2)


def minutes(chars):
    return f"{reading_time(chars):g}"


def blocks_text(blocks):
    return [b.get("x", "") for b in blocks if b.get("t") in ("p", "h")]


def render_blocks(blocks):
    """Body markup for a section: paragraphs, manuscript sub-heads and tables."""
    out = []
    for b in blocks:
        if b["t"] == "h":
            out.append(f"<h4>{esc(b['x'])}</h4>")
        elif b["t"] == "table":
            rows = b["rows"]
            head, body = rows[0], rows[1:]
            th = "".join(f"<th>{esc(c)}</th>" for c in head)
            trs = "".join("<tr>" + "".join(f"<td>{esc(c)}</td>" for c in r) + "</tr>" for r in body)
            out.append(f'<div class="tw"><table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>')
        else:
            # class="bk" 标记书稿正文段落：中文首行缩进两字，由 style.css 统一处理
            out.append(f'<p class="bk">{esc(b["x"])}</p>')
    return "\n".join(out)


def source_html(ch, unit_title):
    """来源与延伸: the chapter's own data note, its appendix-A theory rows, its appendix-C books."""
    items = []
    if ch.get("note"):
        items.append(f'<li><b>本章说明</b><div>{esc(ch["note"])}</div></li>')
    for r in ch.get("theory_rows", []):
        items.append(
            f'<li><b>{esc(r["theory"])}</b>'
            f'<div>{esc(r["who"])} · {esc(r["year"])} 年诺贝尔经济学奖 · {esc(r["gloss"])}</div>'
            f'<div class="meta">原书标注对应：{esc(r["chapters"])}｜见附录A 理论地图</div></li>')
    for e in ch.get("reading", []):
        items.append(f'<li><b>延伸阅读</b><div>{esc(e)}</div></li>')
    if not items:
        return ""
    kinds = []
    if ch.get("theory_rows"):
        kinds.append(f'{len(ch["theory_rows"])} 条理论')
    if ch.get("reading"):
        kinds.append(f'{len(ch["reading"])} 本延伸阅读')
    cnt = (" · " + " · ".join(kinds)) if kinds else ""
    return ('<details class="more"><summary>来源与延伸'
            f'<span class="cnt">{esc(cnt)}</span></summary>\n    <div class="body">'
            f'<ul class="src-list">{"".join(items)}</ul></div>\n  </details>')


def main():
    model = json.load(open(SRC, encoding="utf-8"))
    images = json.load(open(IMGS, encoding="utf-8"))
    items = json.load(open(ITEMS_JSON, encoding="utf-8"))
    book_chars = sum(len(i["text"]) for i in items if i["kind"] == "p")

    app_a = next(a for a in model["appendices"] if a["letter"] == "A")
    app_c = next(a for a in model["appendices"] if a["letter"] == "C")
    theory_table = next(b["rows"] for b in app_a["blocks"] if b["t"] == "table")[1:]
    theory_table = [{"year": r[0], "who": r[1], "theory": r[2], "chapters": r[3], "gloss": r[4]}
                    for r in theory_table if len(r) >= 5]
    reading_list = [b["x"] for b in app_c["blocks"] if b["t"] == "p"]

    def theory_for(no):
        want = CN_NUM[no]
        return [r for r in theory_table if want in re.findall(r"第([一二三四五六七八九十]+)章", r["chapters"])]

    def reading_for(no):
        want = CN_NUM[no]
        out = []
        for e in reading_list:
            m = re.search(r"（第([^）]+)章）", e)
            if m and want in re.findall(r"[一二三四五六七八九十]+", m.group(1)):
                out.append(e)
        return out

    for ch in model["chapters"]:
        ch["theory_rows"] = theory_for(ch["num"])
        ch["reading"] = reading_for(ch["num"])
        ch["hero_url"] = f"img/{ch['hero']}" if ch["hero"] else None

    cards = []          # every filterable unit, in reading order
    blocks_html = []    # rendered <section> blocks

    def facets(blocks, title, is_action=False, is_appendix=False):
        texts = blocks_text(blocks)
        body = "".join(texts)
        if is_action:
            kind = "可执行清单"
        elif "行动指南" in title:
            kind = "可执行清单"
        elif "理论透镜" in title:
            kind = "分析框架"
        elif "国内民生关切" in title:
            kind = "看懂自家账本"
        else:
            kind = "看懂变局机制"
        mats = []
        if NOBEL.search(title) or NOBEL.search(body):
            mats.append("诺奖理论")
        if DATA.search(body):
            mats.append("官方数据")
        if not is_action and not is_appendix and CASE.search(texts[0] if texts else ""):
            mats.append("案例故事")
        if is_action or is_appendix:
            if "行动工具" not in mats:
                mats.append("行动工具")
        chars = sum(len(t) for t in texts)
        tier = "一坐" if chars <= 1200 else "一会儿" if chars <= 1800 else "需专注"
        return kind, mats, chars, tier

    def card_html(cid, ch_key, part, idx, title, kind, mats, tier, elems, minsheng, human, rows,
                  body_html, extra_html="", search_note=""):
        badges = [f'<span class="badge k">{esc(kind)}</span>']
        for m in mats:
            badges.append(f'<span class="badge m">{esc(m)}</span>')
        badges.append(f'<span class="badge l">篇幅 {esc(tier)}</span>')
        for e in elems:
            badges.append(f'<span class="badge plain">{esc(e)}</span>')
        if minsheng:
            badges.append('<span class="badge plain">国内民生关切</span>')
        row_html = "".join(
            f'<div class="k">{k}</div><div class="v{" note" if k == "备注" else ""}">{esc(v)}</div>'
            for k, v in rows
        )
        cards.append({
            "id": cid, "ch": ch_key, "part": part, "title": title, "toc": idx,
            "kind": kind, "mats": mats, "len": tier,
            "flag": minsheng, "table": bool(elems),
        })
        return f"""<article class="card" id="{cid}" data-ch="{esc(ch_key)}" data-part="{esc(part)}" data-kind="{esc(kind)}" data-mats="{esc('|'.join(mats))}" data-len="{esc(tier)}" data-flag="{1 if minsheng else 0}" data-table="{1 if elems else 0}" data-search="{esc(search_note)}">
  <div class="card-h"><span class="idx">{esc(idx)}</span><h3>{esc(title)}</h3><a class="anchor" href="#{cid}" aria-label="本单元固定链接">#</a></div>
  <div class="badges">{''.join(badges)}</div>
  <p class="human">{esc(human)}</p>
  <div class="rows">{row_html}</div>
  <details class="more"><summary>本节全文<span class="cnt"> · {esc(rows[0][1].split(' · ')[0])}</span></summary>
    <div class="body">
{body_html}
    </div>
  </details>
{extra_html}
</article>"""

    # ---------------- 序言 --------------------------------------------------
    pref = model["preface"]
    ptexts = blocks_text(pref["blocks"])
    pk, pm, pc, pt = facets(pref["blocks"], "序言")
    preface_card = card_html(
        "e-0-0", "0", "序", "序", "序言：风浪不可选择，船的结构可以", pk, pm, pt, [], False,
        judgement(ptexts[0]),
        [("成本", f"约 {pc:,} 字 · 约 {minutes(pc)} 分钟 · 全书的用法说明"),
         ("结构", f"{len([b for b in pref['blocks'] if b['t'] == 'p'])} 段 · 三件事本书不做 · 阅读约定"),
         ("备注", "先读这一节，再决定从哪一篇开始")],
        render_blocks(pref["blocks"]), search_note="序言",
    )
    blocks_html.append(f"""<section class="sec-block" id="sec-0" data-ch="0" data-part="序">
  <div class="sec-h"><span class="kicker">序</span><h2>序言</h2><span class="shown"><span class="k">1</span> / 1</span></div>
{preface_card}
</section>""")

    # ---------------- 十五章 -------------------------------------------------
    seen_part = set()
    for ch in model["chapters"]:
        if ch["part"] not in seen_part:
            seen_part.add(ch["part"])
            p = next(x for x in model["parts"] if x["key"] == ch["part"])
            blocks_html.append(
                f'<section class="part" id="part-{esc(ch["part"])}" data-part="{esc(ch["part"])}">'
                f'<span class="p-k">{esc(ch["part"])}\u3000篇</span>'
                f'<h2>{esc(p["title"])}</h2>'
                f'<p class="bk">{esc(p["lede"])}</p></section>')
        parts = []
        if ch["hero_url"]:
            parts.append(f'<img class="hero" loading="lazy" src="{esc(ch["hero_url"])}" alt="第{ch["numCn"]}章插图">')
        for b in ch["lede"]:
            if b["t"] == "p":
                parts.append(f'<p class="lede">{esc(b["x"])}</p>')
        card_ids = []
        for sec in ch["sections"]:
            slot = sec["num"].split(".")[1]
            cid = f"e-{ch['num']}-{slot}"
            texts = blocks_text(sec["blocks"])
            kind, mats, chars, tier = facets(sec["blocks"], sec["title"])
            elems = ["含表"] if any(b["t"] == "table" for b in sec["blocks"]) else []
            minsheng = "国内民生关切" in sec["title"]
            heads = [b["x"] for b in sec["blocks"] if b["t"] == "h"]
            rowbits = [f"{len([b for b in sec['blocks'] if b['t'] == 'p'])} 段"]
            if heads:
                rowbits.append(f"含 {len(heads)} 个小标题")
            if elems:
                rowbits.append("含 1 张表")
            if ch["actions"]:
                rowbits.append(f"本章另有 {len(ch['actions'])} 条行动清单")
            note = "数据与政策口径截至 2026 年年中"
            if ch["theory_rows"] and "理论透镜" in sec["title"]:
                note += " · 理论地图：" + "、".join(r["who"].split("、")[0] for r in ch["theory_rows"][:3])
            parts.append(card_html(
                cid, str(ch["num"]), ch["part"], sec["num"], sec["title"], kind, mats, tier, elems, minsheng,
                judgement(texts[0] if texts else ""),
                [("成本", f"约 {chars:,} 字 · 约 {minutes(chars)} 分钟 · 不需要任何数学基础"),
                 ("结构", " · ".join(rowbits)),
                 ("备注", note)],
                render_blocks(sec["blocks"]),
                extra_html=source_html(ch, sec["title"]),
                search_note="",
            ))
            card_ids.append(cid)
        # 章末行动清单
        if ch["actions"]:
            cid = f"e-{ch['num']}-A"
            note_paras = ch.get("actionNote", [])
            ab = [{"t": "p", "x": a["text"]} for a in ch["actions"]] + \
                 [{"t": "p", "x": t} for t in note_paras]
            kind, mats, chars, tier = facets(ab, "行动清单", is_action=True)
            body = '<ol class="acts">' + "".join(f"<li><p>{esc(a['text'])}</p></li>" for a in ch["actions"]) + "</ol>"
            for t in note_paras:
                body += f'<p class="bk">{esc(t)}</p>'
            parts.append(card_html(
                cid, str(ch["num"]), ch["part"], "行动",
                f"第{ch['numCn']}章行动清单：{ch['title'].split('：')[0]}", kind, mats, "一会儿", [], False,
                judgement(ch["summary"][0] if ch["summary"] else ch["title"]),
                [("成本", f"{len(ch['actions'])} 条 · 约 {chars:,} 字 · 今晚就能开始第一条"),
                 ("结构", "每条都写明做什么、怎么开始、多久复查"),
                 ("备注", "数据与政策口径截至 2026 年年中 · 对应本章各节正文")],
                body, extra_html=source_html(ch, "行动清单"), search_note="行动清单",
            ))
            card_ids.append(cid)
        summary = ""
        if ch["summary"]:
            summary = ('<details class="gloss"><summary>本章小结</summary><div>'
                       + "".join(f'<p class="bk">{esc(t)}</p>' for t in ch["summary"]) + "</div></details>")
        blocks_html.append(
            f'<section class="sec-block" id="sec-{ch["num"]}" data-ch="{ch["num"]}" data-part="{esc(ch["part"])}">\n'
            f'  <div class="sec-h"><span class="kicker">{esc(PART_LABEL[ch["part"]])}</span>'
            f'<h2>第{ch["numCn"]}章 {esc(ch["title"])}</h2>'
            f'<span class="shown"><span class="k">{len(card_ids)}</span> / {len(card_ids)}</span></div>\n'
            + "\n".join(parts) + "\n" + summary + "\n</section>"
        )

    # ---------------- 结语 ---------------------------------------------------
    epi = model["epilogue"]
    ek, em, ec, et = facets([{"t": "p", "x": t} for t in epi], "结语", is_appendix=True)
    em = [m for m in em if m != "行动工具"]
    epi_card = card_html(
        "e-99-99", "99", "结", "结", "结语：三句话与一艘检修完毕的船", ek, em, et, [], False,
        judgement(epi[0]),
        [("成本", f"约 {ec:,} 字 · 约 {minutes(ec)} 分钟 · 全书收束"),
         ("结构", f"{len(epi)} 段 · 三句话总结全书"),
         ("备注", "读完任何一篇后都可以回来重读")],
        render_blocks([{"t": "p", "x": t} for t in epi]), search_note="结语",
    )
    blocks_html.append(f"""<section class="sec-block" id="sec-99" data-ch="99" data-part="结">
  <div class="sec-h"><span class="kicker">结</span><h2>结语</h2><span class="shown"><span class="k">1</span> / 1</span></div>
{epi_card}
</section>""")

    # ---------------- 附录 ---------------------------------------------------
    app_parts = []
    for app in model["appendices"]:
        letter = app["letter"]
        if app["blocks"] and app["blocks"][0]["t"] == "h":
            app["blocks"][0]["t"] = "p"
        texts = blocks_text(app["blocks"])
        tables = [b for b in app["blocks"] if b["t"] == "table"]
        n_rows = sum(len(t["rows"]) for t in tables)
        titles = {"A": "理论地图：25 副诺奖眼镜", "B": "家庭财务工作表：两张可直接填写的表",
                  "C": "参考文献与延伸阅读：按入门→进阶排序"}
        kinds = {"A": "分析框架", "B": "可执行清单", "C": "分析框架"}
        mats = {"A": ["诺奖理论", "官方数据"], "B": ["行动工具"], "C": []}[letter]
        if n_rows:
            cost = f"{n_rows} 行表格 · 可打印后直接填写"
        else:
            cost = f"{len(texts)} 条 · 可直接照着找书"
        human = app["lede"] or texts[0]
        body = render_blocks(app["blocks"])
        if letter == "C":
            body = '<ol class="acts">' + "".join(
                f"<li><p>{esc(t)}</p></li>" for t in texts) + "</ol>"
        elif letter == "B":
            body = render_blocks([b for b in app["blocks"] if b["t"] != "table"]) + \
                render_blocks([b for b in app["blocks"] if b["t"] == "table"])
        app_parts.append(card_html(
            f"e-app{letter}", "app", "附", "附录" + letter,
            f"{app['title']}｜{titles[letter]}", kinds[letter], mats, "一坐",
            ["含表"] if n_rows else [], False, human,
            [("成本", cost),
             ("结构", f"与正文 {len(model['chapters'])} 章的对应关系已逐条标注"),
             ("备注", "附录与正文互为索引，读到哪一章都可以回来查")],
            body, search_note="附录" + letter,
        ))
    blocks_html.append('<section class="sec-block" id="sec-app" data-ch="app" data-part="附">\n'
                       '  <div class="sec-h"><span class="kicker">附</span><h2>附录 A · B · C</h2>'
                       '<span class="shown"><span class="k">3</span> / 3</span></div>\n'
                       + "\n".join(app_parts) + "\n</section>")

    # ---------------- 侧栏 ---------------------------------------------------
    groups = [{"key": "0", "label": "序言", "cards": [c for c in cards if c["ch"] == "0"]}]
    for ch in model["chapters"]:
        groups.append({"key": str(ch["num"]),
                       "label": f"第{ch['numCn']}章 {ch['title'].split('：')[0]}",
                       "cards": [c for c in cards if c["ch"] == str(ch["num"])]})
    groups.append({"key": "99", "label": "结语", "cards": [c for c in cards if c["ch"] == "99"]})
    groups.append({"key": "app", "label": "附录 A · B · C", "cards": [c for c in cards if c["ch"] == "app"]})

    def chip(dim, val, label, n):
        return (f'<button class="chip" data-v="{esc(val)}" aria-pressed="false">{esc(label)}'
                f'<em>{n}</em></button>')

    PART_ALL = dict(PART_LABEL, **{"序": "序言", "结": "结语", "附": "附录"})
    part_html = []
    for p in PART_ORDER:
        n = sum(1 for c in cards if c["part"] == p)
        if not n:
            continue
        label = PART_ALL[p]
        part_html.append(f'<button class="sec-link" data-v="{p}" aria-pressed="false">'
                         f'<span class="lb">{esc(label)}</span><i>{n}</i></button>')

    # 每个章节按钮后面紧跟它自己的目录面板：面板必须贴着按钮，否则展开第五章时
    # 目录会跑到整份章节列表的末尾去（参考站也是 appendChild(button); appendChild(sub)）
    ch_html = [f'<button class="sec-link all" data-v="" aria-pressed="true"><span class="lb">全部章节</span><i>{len(cards)}</i></button>']
    for g in groups:
        ch_html.append(
            f'<button class="sec-link" data-v="{g["key"]}" aria-pressed="false">'
            f'<span class="lb">{esc(g["label"])}</span><i>{len(g["cards"])}</i>'
            f'<b class="fold" title="展开或收起本节目录"><svg viewBox="0 0 24 24">'
            f'<path d="m6 9 6 6 6-6" stroke-linecap="round" stroke-linejoin="round"/></svg></b></button>')
        sub = [f'<a href="#{c["id"]}" data-go="{c["id"]}"><i>{esc(c["toc"])}</i>'
               f'<span>{esc(c["title"])}</span></a>' for c in g["cards"]]
        sub.append('<p class="toc-none" hidden>没有符合当前筛选的单元</p>')
        ch_html.append(f'<div class="toc-sub" data-for="{g["key"]}" hidden>{"".join(sub)}</div>')

    def counts(field):
        if field == "kind":
            return Counter(c["kind"] for c in cards)
        if field == "len":
            return Counter(c["len"] for c in cards)
        return Counter(m for c in cards for m in c["mats"])

    kind_c = counts("kind")
    mat_c = counts("mat")
    len_c = counts("len")
    kind_chips = "".join(chip("kind", k, k, kind_c[k]) for k in ["看懂变局机制", "分析框架", "看懂自家账本", "可执行清单"])
    mat_chips = "".join(chip("mat", m, m, mat_c[m]) for m in ["诺奖理论", "官方数据", "案例故事", "行动工具"])
    len_chips = "".join(chip("len", t, t, len_c[t]) for t in ["一坐", "一会儿", "需专注"])

    glossary = "".join(
        f"<dt>{esc(r['theory'])}</dt><dd>{esc(r['year'])} 年诺贝尔经济学奖 · {esc(r['who'])}：{esc(r['gloss'])}（{esc(r['chapters'])}）</dd>"
        for r in sorted(theory_table, key=lambda r: r["year"]))

    meta = {
        "title": model["title"], "subtitle": model["subtitle"], "edition": model["edition"],
        "cards": len(cards), "sections": sum(len(c["sections"]) for c in model["chapters"]),
        "actions": sum(len(c["actions"]) for c in model["chapters"]),
        "chapters": len(model["chapters"]), "chars": book_chars,
        "theory": len(theory_table), "reading": len(reading_list),
        "pages": 132,
    }

    stat = (f'<b>{meta["cards"]}</b> 个可检索单元 · <b>{meta["sections"]}</b> 节正文 + '
            f'<b>{meta["actions"]}</b> 条行动清单 · 三篇十五章 · 约 <b>{meta["chars"] / 10000:.1f}</b> 万字')

    page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(model['title'])}{esc(model['subtitle'])} · 网页版</title>
<meta name="description" content="《{esc(model['title'])}》全文网页版：三篇十五章、{meta['sections']} 节正文与 {meta['actions']} 条行动清单，按“篇 / 章 / 这一节给你什么 / 材料 / 篇幅”检索，每条写明成本、结构与出处。作者：江召兵。">
<meta name="keywords" content="不确定年代的生存经济学,江召兵,通胀,债务,全球化,AI革命,老龄化,行为经济学,信息不对称,制度,风险,家庭资产负债表,投资纪律,压力测试">
<meta name="author" content="江召兵">
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
<meta property="og:description" content="三篇十五章、{meta['sections']} 节正文与 {meta['actions']} 条行动清单，可按篇、章、收益、材料与篇幅检索。">
<meta property="og:image" content="{BASE}img/{esc(images['cover'])}">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">
{{"@context":"https://schema.org","@graph":[
{{"@type":"Book","@id":"{BASE}#book","name":"{model['title']}{model['subtitle']}","url":"{BASE}","inLanguage":"zh-CN","bookFormat":"https://schema.org/EBook","numberOfPages":{meta['pages']},"author":{{"@type":"Person","name":"江召兵","url":"https://ZhaobingJiang.github.io/"}},"abstract":"三篇十五章、{meta['sections']} 节正文与 {meta['actions']} 条行动清单，回答变局发生了什么、为什么、怎么办。","isAccessibleForFree":true,"encoding":[
{{"@type":"MediaObject","contentUrl":"{BASE}../survival_economics_uncertain_times_v3_illustrated.pdf","encodingFormat":"application/pdf"}},
{{"@type":"MediaObject","contentUrl":"{BASE}../survival_economics_uncertain_times_v3_illustrated.docx","encodingFormat":"application/vnd.openxmlformats-officedocument.wordprocessingml.document"}}]}},
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
      <input id="q" type="search" placeholder="搜索 {meta['sections']} 节正文与 {meta['actions']} 条行动，例如：提前还贷 / 明斯基 / 法拍房" autocomplete="off" spellcheck="false">
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
    <div class="gt">篇 <small>三篇十五条主线</small></div>
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
    <label class="toggle"><input type="checkbox" id="f-flag">只看「国内民生关切」</label>
    <label class="toggle"><input type="checkbox" id="f-table">只看含表格的单元</label>
    <button class="reset" id="reset">清空筛选</button>
  </div>
  <p class="hint">
    章节单选，其余可多选；同一组内是「或」，不同组之间是「且」。每章内按原书顺序排，检索不改变顺序。
  </p>
  <p class="doc-links">
    <a href="../survival_economics_uncertain_times_v3_illustrated.pdf">PDF 全文</a>
    <a href="../survival_economics_uncertain_times_v3_illustrated.docx" download>DOCX</a>
    <a href="../../zh/books.html">返回专著页</a>
  </p>
</aside>
<div class="backdrop" id="backdrop"></div>

<main class="content">
  <div class="doc">
    <div class="doc-head">
      <h1>{esc(model['title'])}</h1>
      <p>{esc(model['subtitle'].lstrip('—'))}</p>
      <p class="stat">{stat}</p>
    </div>

    <div class="cover">
      <img src="img/{esc(images['cover'])}" alt="《{esc(model['title'])}》封面" loading="lazy">
      <div class="cv-t">
        <b>江召兵 著 · {esc(model['edition'])}</b>
        全书分三篇十五章，每章五节（第五章四节），每节按「故事 → 机制 → 国内关切 → 理论 → 行动」展开；
        每章末尾附行动清单，书末附理论地图、家庭财务工作表与延伸阅读。
        本页把全书拆成 {meta['cards']} 个可检索单元：上方搜索，左侧按篇、章、收益、材料与篇幅筛选，点开每条即可读全文。
      </div>
    </div>

    <p class="intro">每一条都回答三个问题：这一节讲什么、读完你能拿走什么、数据到什么时点为止。左边把「这一节给你什么」选「可执行清单」、「篇幅」选「一坐」，剩下的就是今晚就能读完并且动手的那几条。</p>
    <p class="intro">全书的判断都可以追到出处：正文引用的诺奖理论逐条列在附录A，延伸阅读逐条列在附录C，本页把两者按章挂回了对应单元。本页只呈现书稿原文与结构，不添加任何原文没有的结论。</p>
    <p class="intro">当前显示 <b id="cnt">{meta['cards']}</b> 条，共 {meta['cards']} 条。正文与标签全部来自书稿 <code>survival_economics_uncertain_times_v3_illustrated.docx</code>，改书稿即改这里。</p>

    <div id="list">
{chr(10).join(blocks_html)}
    </div>

    <div class="empty" id="empty" hidden>
      没有符合当前筛选的单元。<button type="button" id="reset2">清空筛选</button>
    </div>

    <details class="gloss" id="gloss">
      <summary>看不懂的诺奖名词（{len(theory_table)} 条，取自附录A 理论地图）</summary>
      <dl>{glossary}</dl>
    </details>

    <div class="foot">
      <p>《{esc(model['title'])}{esc(model['subtitle'])}》 江召兵 著 · {esc(model['edition'])} · {meta['pages']} 页 · 约 {meta['chars'] / 10000:.1f} 万字。</p>
      <p>全书正文数据与政策口径截至 2026 年年中；本书不做具体时点预测，不构成投资建议。网页版按 <a href="https://eternity4719.github.io/HowToLiveBetter/" target="_blank" rel="noopener">HowToLiveBetter</a> 的版式组织，正文未作删改。</p>
      <p><a href="../survival_economics_uncertain_times_v3_illustrated.pdf">下载 PDF 全文</a> · <a href="../survival_economics_uncertain_times_v3_illustrated.docx" download>下载 DOCX</a> · <a href="../../zh/books.html">返回专著页</a> · <a href="../../">江召兵个人主页</a></p>
      <img class="backcover" src="img/{esc(images['backcover'])}" alt="《{esc(model['title'])}》封底" loading="lazy">
    </div>
  </div>
</main>

<script src="app.js"></script>
</body>
</html>
"""

    with open(DEST, "w", encoding="utf-8") as f:
        f.write(page)

    # 版式与交互层来自 tools/web-edition/，构建时复制到本书目录，页面保持自包含
    import shutil
    shared = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web-edition")
    for name in ("style.css", "app.js"):
        shutil.copyfile(os.path.join(shared, name), os.path.join(SITE, name))
        print(f"copied {name} from tools/web-edition/")

    print(f"cards={len(cards)}  html={len(page):,} bytes  chars={book_chars:,}")
    print("kind:", dict(Counter(c['kind'] for c in cards)))
    print("len :", dict(Counter(c['len'] for c in cards)))
    print("mats:", dict(Counter(m for c in cards for m in c['mats'])))
    print("untagged:", sum(1 for c in cards if not c['mats']))
    print("glossary:", len(theory_table), "reading list:", len(reading_list))
    for g in groups:
        print(f"   {g['key']:>4} {g['label'][:32]:<34} {len(g['cards'])}")


if __name__ == "__main__":
    sys.exit(main())

