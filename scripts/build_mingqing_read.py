# -*- coding: utf-8 -*-
r"""Render the web reading edition of 明清艳情词曲全编.

Outputs, under books/mingqing-yanqing-ciqu/:
  index.html   封面 / 出版信息 / 前言 / 总目录（三卷）
  shang.html   上卷正文
  zhong.html   中卷正文
  xia.html     下卷正文
"""
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = r"D:\deepseek-harness\OpatiyaAgent\JiangZhaobing.github.io"
OUTDIR = os.path.join(SITE, "books", "mingqing-yanqing-ciqu")
os.makedirs(OUTDIR, exist_ok=True)

with open(os.path.join(ROOT, "book.json"), encoding="utf-8") as f:
    BOOK = json.load(f)

SITE_URL = "https://ZhaobingJiang.github.io/books/mingqing-yanqing-ciqu/"
TITLE = "明清艳情词曲全编"
SUBTITLE = "白话注释 · 现代赏析"
COMPILER = "花子金"
VOL_FILES = {"上卷": "shang.html", "中卷": "zhong.html", "下卷": "xia.html"}
VOL_ORDER = ["上卷", "中卷", "下卷"]
SUBHEAD_RE = re.compile(
    r"^(又(一篇.*|云|一云)?|[一二三四五六七八九十]{1,2}|[一二三四五六七八九十]云|其[一二三四五六七八九十]{1,2})$"
)

# ---- global numbering
seq = 0
vol_meta = []
for vol in BOOK["volumes"]:
    pages = [e.get("book_page") for e in vol["entries"] if e.get("book_page")]
    for e in vol["entries"]:
        seq += 1
        e["idx"] = seq
        e["anchor"] = f"e-{seq:04d}"
    vol_meta.append({
        "name": vol["name"],
        "file": VOL_FILES[vol["name"]],
        "count": len(vol["entries"]),
        "first": pages[0] if pages else None,
        "last": pages[-1] if pages else None,
        "entries": vol["entries"],
    })
TOTAL = seq

total_chars = sum(len(p) for p in BOOK["preface"]["paras"]) + sum(
    len(p) for v in BOOK["volumes"] for e in v["entries"]
    for b in e.get("blocks", []) for p in b["paras"]
)


def esc(t):
    return html.escape(t, quote=False)


def para(p, cls=""):
    c = f' class="{cls}"' if cls else ""
    return f"<p{c}>{esc(p)}</p>"


# ---------------------------------------------------------------- head / style
def head(page_title, desc, url, extra_ld=""):
    return f"""<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(page_title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="keywords" content="明清艳情词曲全编,情经,冯梦龙,华广生,花子金,明清词曲,挂枝儿,山歌,在线阅读,全文">
<meta name="author" content="{esc(COMPILER)}">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
<meta name="theme-color" content="#fbfaf7">
<link rel="canonical" href="{url}">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%238c2f24'/%3E%3Ctext x='32' y='45' font-size='32' text-anchor='middle' fill='white' font-family='serif'%3E%E6%83%85%3C/text%3E%3C/svg%3E">
<meta property="og:type" content="book">
<meta property="og:site_name" content="江召兵 · 专著">
<meta property="og:locale" content="zh_CN">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{esc(page_title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="{SITE_URL}cover.jpg?v=1">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">
{{"@context":"https://schema.org","@graph":[
{{"@type":"Book","@id":"{SITE_URL}#book","name":"{TITLE}","alternateName":"情经","url":"{SITE_URL}","inLanguage":"zh-CN","bookFormat":"https://schema.org/EBook","numberOfPages":2032,"author":[{{"@type":"Person","name":"冯梦龙"}},{{"@type":"Person","name":"华广生"}}],"editor":{{"@type":"Person","name":"{COMPILER}"}},"publisher":{{"@type":"Organization","name":"广州出版社"}},"datePublished":"1995-07","isbn":"7-80592-268-3","abstract":"明代冯梦龙所辑时调、清代华广生所辑曲词等明清艳情词曲的选本，逐篇附现代语译、注释与评析。","isAccessibleForFree":true}},
{{"@type":"WebSite","@id":"{SITE_URL}#website","url":"{SITE_URL}","name":"明清艳情词曲全编（网页版）","inLanguage":"zh-CN"}}]}}
</script>
<link rel="stylesheet" href="../../assets/css/style.css">"""


STYLE = """<style>
  :root { --ink:#1f2328; --muted:#5b6470; --line:#e3e6ea; --paper:#fbfaf7; --seal:#8c2f24; }
  body { background:var(--paper); color:var(--ink); }
  .reader { max-width:48rem; margin:0 auto; padding:1.2rem 1.15rem 4rem; }
  .book-head { text-align:center; padding:2.2rem 0 1.2rem; border-bottom:1px solid var(--line); }
  .book-head .t { font-size:2.3rem; letter-spacing:.32rem; margin:0 0 .6rem; font-family:"Songti SC","SimSun",serif; }
  .book-head .s { color:var(--muted); letter-spacing:.12rem; font-size:.95rem; line-height:1.7; }
  .book-head .a { margin-top:.9rem; font-size:1.02rem; line-height:1.8; }
  .web-cover { width:200px; height:auto; max-width:56%; display:block; margin:0 auto 1.2rem; border:1px solid var(--line); box-shadow:0 8px 22px rgba(0,0,0,.10); }
  .notice { margin:1.2rem 0 0; padding:.9rem 1rem; background:#fff; border:1px solid var(--line); border-radius:8px; font-size:.92rem; color:var(--muted); line-height:1.75; }
  .notice b { color:var(--ink); }
  .read-top { display:flex; gap:.6rem; flex-wrap:wrap; justify-content:center; margin:1.2rem 0 0; }
  .read-top a { display:inline-block; padding:.42rem .85rem; border:1px solid #d8c6b8; border-radius:999px; color:var(--seal); text-decoration:none; font-size:.9rem; }
  section.front { margin:1.6rem 0 0; padding:1.2rem 1.15rem; background:#fff; border:1px solid var(--line); border-radius:8px; }
  section.front h1 { font-size:1.15rem; letter-spacing:.1rem; text-align:center; margin:.2rem 0 1rem; color:var(--muted); font-weight:600; }
  section.front h2 { font-size:1.05rem; letter-spacing:.08rem; margin:1.4rem 0 .6rem; padding-left:.55rem; border-left:3px solid var(--seal); }
  section.front p { font-family:"Songti SC","SimSun",serif; font-size:.98rem; line-height:1.95; margin:.55rem 0; text-indent:2em; }
  section.front p.center { text-indent:0; text-align:center; margin:.25rem 0; }
  section.front dl.meta { margin:.4rem 0; font-size:.94rem; line-height:1.9; }
  section.front dl.meta dt { float:left; width:5.5rem; color:var(--muted); clear:left; }
  section.front dl.meta dd { margin:0 0 0 5.5rem; }
  h2.section-h { margin:2.4rem 0 1rem; font-size:1.15rem; letter-spacing:.1rem; padding-left:.6rem; border-left:4px solid var(--seal); }
  .preface p { font-family:"Songti SC","SimSun",serif; font-size:1.04rem; line-height:2.1; text-indent:2em; margin:.75rem 0; }
  ol.toc { list-style:none; padding:0; margin:0 0 1.6rem; }
  ol.toc > li { padding:.34rem .2rem; border-bottom:1px dashed var(--line); font-size:.95rem; }
  ol.toc a { color:var(--ink); text-decoration:none; }
  ol.toc a:hover { color:var(--seal); }
  ol.toc .pg { color:var(--muted); font-size:.82rem; margin-left:.4rem; }
  h3.vol-h { margin:2rem 0 .6rem; font-size:1.05rem; letter-spacing:.16rem; color:var(--seal); }
  h3.vol-h a { color:var(--seal); text-decoration:none; }
  h2.vol-head { text-align:center; font-size:1.5rem; letter-spacing:.8rem; margin:2.6rem 0 1.4rem; padding:.6rem 0; color:var(--seal); border-top:1px solid var(--line); border-bottom:1px solid var(--line); font-family:"Songti SC","SimSun",serif; }
  .vol-sub { text-align:center; color:var(--muted); font-size:.88rem; margin:-.7rem 0 1.6rem; letter-spacing:.06rem; }
  article.entry { margin:2.8rem 0 0; padding-top:.4rem; border-top:1px solid var(--line); }
  .entry-title { font-size:1.32rem; line-height:1.9; margin:.4rem 0 1.1rem; text-align:center; font-family:"Songti SC","SimSun",serif; letter-spacing:.14rem; }
  .entry-title .pg { display:block; font-size:.76rem; font-weight:400; letter-spacing:.06rem; color:var(--muted); margin-top:.25rem; }
  .verse { margin:.6rem 0 1.2rem; padding:1rem 1.1rem; background:#fffdf9; border-left:3px solid #d9c3b0; border-radius:4px; }
  .verse p { font-family:"Kaiti SC","KaiTi","Songti SC",serif; font-size:1.1rem; line-height:2.15; text-indent:2em; margin:.5rem 0; }
  .verse p.sub { text-indent:0; text-align:center; color:var(--muted); letter-spacing:.3rem; margin:1.1rem 0; font-size:.98rem; }
  .verse .lbl.tune { display:inline-block; font-size:.86rem; letter-spacing:.16rem; color:var(--seal); margin-bottom:.2rem; }
  .sec { margin:1.1rem 0 0; }
  .sec .lbl { display:inline-block; font-size:.86rem; letter-spacing:.16rem; color:var(--seal); border-bottom:1px solid #e0cdc0; padding-bottom:.1rem; margin-bottom:.15rem; }
  .sec p { font-family:"Songti SC","SimSun",serif; font-size:.97rem; line-height:1.95; text-indent:2em; margin:.45rem 0; color:#33383d; }
  .missing { color:#a33; font-size:.9rem; }
  .vol-nav { display:flex; justify-content:space-between; align-items:center; gap:.6rem; margin:2.2rem 0 0; padding-top:1rem; border-top:1px dashed var(--line); font-size:.92rem; }
  .vol-nav a { color:var(--seal); text-decoration:none; }
  footer.reader-foot { margin-top:3rem; padding-top:1.2rem; border-top:1px solid var(--line); color:var(--muted); font-size:.86rem; line-height:1.8; }
  @media (max-width:640px) {
    .book-head .t { font-size:1.8rem; letter-spacing:.14rem; }
    .reader { padding:1rem .9rem 3rem; }
    .verse p { font-size:1.04rem; line-height:2; }
    section.front dl.meta dt { float:none; width:auto; }
    section.front dl.meta dd { margin:0 0 .2rem; }
  }
</style>"""

SITE_NAV = """<header class="site-header">
  <nav class="site-nav">
    <a href="../../" class="nav-link">首页</a>
    <a href="../" class="nav-link">专著与书稿</a>
    <a href="../../zh/books.html" class="nav-link">中文书籍</a>
  </nav>
</header>"""

FOOT = """<footer class="reader-foot">
  <p>原著：〔明〕冯梦龙　〔清〕华广生　编著：花子金　出版：广州出版社，1995 年 7 月第 1 版。</p>
  <p>本网页版据该书扫描本识别、校订并重新排版，仅供个人阅读与学习交流；原著版权归原作者及出版社所有。</p>
</footer>"""


# ---------------------------------------------------------------- index page
def build_index():
    toc_parts = []
    for vm in vol_meta:
        toc_parts.append(
            f'<h3 class="vol-h"><a href="{vm["file"]}">{vm["name"]}</a>'
            f'<span class="pg" style="color:var(--muted);font-size:.82rem;font-weight:400;letter-spacing:.04rem;margin-left:.6rem;">'
            f'原书第 {vm["first"]}–{vm["last"]} 页 · 共 {vm["count"]} 篇</span></h3>'
        )
        toc_parts.append('<ol class="toc">')
        for e in vm["entries"]:
            title = e.get("title") or e.get("toc_title") or "（标题待补）"
            page = e.get("book_page")
            pg = f'<span class="pg">p.{page}</span>' if page else ""
            toc_parts.append(
                f'<li><a href="{vm["file"]}#{e["anchor"]}">{esc(title)}</a>{pg}</li>'
            )
        toc_parts.append("</ol>")

    front = f"""  <section class="front">
    <h1>扉页</h1>
    <p class="center"><strong>明清艳情词曲全编</strong></p>
    <p class="center">白话注释　现代赏析</p>
    <p class="center">〔明〕冯梦龙　〔清〕华广生</p>
    <p class="center">{COMPILER}　编著</p>
    <p class="center">广州出版社</p>
    <hr>
    <h2>出版信息</h2>
    <dl class="meta">
      <dt>书　名</dt><dd>明清艳情词曲全编</dd>
      <dt>原　著</dt><dd>〔明〕冯梦龙　〔清〕华广生</dd>
      <dt>编　著</dt><dd>{COMPILER}</dd>
      <dt>责任编辑</dt><dd>赵辛予</dd>
      <dt>出版发行</dt><dd>广州出版社（广州市东风中路 503 号 7 楼）</dd>
      <dt>经　销</dt><dd>黑龙江省新华书店</dd>
      <dt>印　刷</dt><dd>广东省番禺市印刷厂</dd>
      <dt>开　本</dt><dd>850×1168 毫米　大 32 开　65.25 印张</dd>
      <dt>字　数</dt><dd>120 万字</dd>
      <dt>版　次</dt><dd>1995 年 7 月第 1 版　1995 年 7 月第 1 次印刷</dd>
      <dt>印　数</dt><dd>1—5000 册</dd>
      <dt>书　号</dt><dd>ISBN 7-80592-268-3 / I·89</dd>
      <dt>定　价</dt><dd>79.80 元（上、中、下册）</dd>
    </dl>
    <h2>内容简介</h2>
    <p>本书选录明代至清代嘉庆、道光年间的艳情词曲，以冯梦龙所辑《挂枝儿》《山歌》等时调、华广生所辑曲词为主，兼及明清杂剧传奇中析出的曲文，共一千二百余篇，分上、中、下三卷。每篇均附现代语译、注释与评析，是了解明清民歌时调、俗曲与情爱观念的重要读本。</p>
    <p>所收作品大多出自民间，语言率真质朴，写男女之情不加掩饰，既可见明清两代市井生活与情感世界的实况，也为研究中国俗文学、民歌与性观念史提供了大量一手材料。</p>
    <h2>整理说明</h2>
    <p>本网页版以原书扫描本为底本，逐页识别文字，按原书分卷、分篇重新排版；原书页码在各篇标题下标注，便于核对原书。文中异体字、旧字形一般改用通行字，明显的识读讹误已作校订，余下的可疑之处保留原貌，请读者以原书为准。</p>
    <p>全书约 {total_chars / 10000:.0f} 万字，分三卷阅读：<a href="shang.html">上卷</a>、<a href="zhong.html">中卷</a>、<a href="xia.html">下卷</a>。原著版权归作者及出版社所有，本网页版仅供个人阅读与学习交流，不作商业用途。</p>
  </section>

  <h2 class="section-h" id="preface">前言　谈经论道说《情经》</h2>
  <div class="preface">
    {''.join(para(p) for p in BOOK["preface"]["paras"])}
  </div>

  <h2 class="section-h" id="toc">总目录</h2>
  {''.join(toc_parts)}
"""

    body = f"""<body>
{SITE_NAV}

<main class="reader" id="top">
  <div class="book-head">
    <img class="web-cover" src="cover.jpg?v=1" alt="《明清艳情词曲全编》封面：冯梦龙、华广生原著，花子金编著，广州出版社" width="640" height="960">
    <h1 class="t">{TITLE}</h1>
    <div class="s">{SUBTITLE}</div>
    <div class="a">原著　〔明〕冯梦龙　〔清〕华广生　·　编著　{COMPILER}</div>
  </div>

  <div class="notice">
    <b>上、中、下三卷 · 一千二百二十篇 · 约 {total_chars / 10000:.0f} 万字 · 据广州出版社 1995 年 7 月第 1 版扫描本整理。</b>
    明代时调、清代曲词与杂剧传奇中析出的艳情词曲，逐篇附现代语译、注释与评析。全书免费在线阅读。
  </div>

  <div class="read-top">
    <a href="#preface">前言</a>
    <a href="#toc">总目录</a>
    <a href="shang.html">上卷</a>
    <a href="zhong.html">中卷</a>
    <a href="xia.html">下卷</a>
  </div>

{front}
{FOOT}
</main>
</body>
</html>
"""
    doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
{head(f"{TITLE} · 明清词曲 · 在线阅读",
      f"《{TITLE}》网页版：{SUBTITLE}，上中下三卷一千二百二十篇，{BOOK['preface']['title']}及全文在线阅读。",
      SITE_URL)}
{STYLE}
</head>
{body}"""
    path = os.path.join(OUTDIR, "index.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(doc)
    print("index", len(doc))


# ---------------------------------------------------------------- volume pages
def entry_html(e):
    title = e.get("title") or e.get("toc_title") or "（标题待补）"
    out = [f'<article class="entry" id="{e["anchor"]}">']
    pg = e.get("book_page")
    pg_html = f'<span class="pg">原书第 {pg} 页</span>' if pg else ""
    out.append(f'<h3 class="entry-title">{esc(title)}{pg_html}</h3>')
    if e.get("missing_title"):
        out.append('<p class="missing">（本篇标题未能从扫描页识别，正文待补。）</p>')
    blocks = e.get("blocks") or []
    if not blocks:
        out.append('<p class="missing">（本篇正文待整理。）</p>')
    for blk in blocks:
        paras = [p for p in blk.get("paras", []) if p]
        if not paras:
            continue
        if blk["kind"] == "verse":
            out.append('<div class="verse">')
            if blk.get("label"):
                out.append(f'<span class="lbl tune">〔{esc(blk["label"])}〕</span>')
            for p in paras:
                if SUBHEAD_RE.match(p.strip()):
                    out.append(f'<p class="sub">{esc(p)}</p>')
                else:
                    out.append(para(p))
            out.append("</div>")
        else:
            out.append('<div class="sec">')
            out.append(f'<span class="lbl">{esc(blk["label"])}</span>')
            out.extend(para(p) for p in paras)
            out.append("</div>")
    out.append("</article>")
    return "\n".join(out)


def build_volume(vi):
    vm = vol_meta[vi]
    name = vm["name"]
    filename = vm["file"]
    prev_vm = vol_meta[vi - 1] if vi > 0 else None
    next_vm = vol_meta[vi + 1] if vi + 1 < len(vol_meta) else None
    url = f"{SITE_URL}{filename}"

    entries_html = []
    toc = ['<ol class="toc">']
    for e in vm["entries"]:
        title = e.get("title") or e.get("toc_title") or "（标题待补）"
        toc.append(f'<li><a href="#{e["anchor"]}">{esc(title)}</a></li>')
        entries_html.append(entry_html(e))
    toc.append("</ol>")

    prev_html = f'<a href="{prev_vm["file"]}">← {prev_vm["name"]}</a>' if prev_vm else "<span></span>"
    next_html = f'<a href="{next_vm["file"]}">{next_vm["name"]} →</a>' if next_vm else "<span></span>"

    body = f"""<body>
{SITE_NAV}

<main class="reader" id="top">
  <h2 class="vol-head">{name}</h2>
  <div class="vol-sub">原书第 {vm["first"]}–{vm["last"]} 页 · 共 {vm["count"]} 篇 · <a href="index.html#toc" style="color:var(--seal);text-decoration:none;">返回总目录</a></div>
  {''.join(toc)}
  {''.join(entries_html)}
  <nav class="vol-nav">
    {prev_html}
    <a href="index.html#toc">总目录</a>
    {next_html}
  </nav>
{FOOT}
</main>
</body>
</html>
"""
    doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
{head(f"{TITLE} · {name} · 在线阅读",
      f"《{TITLE}》{name}全文：原书第 {vm['first']}–{vm['last']} 页，共 {vm['count']} 篇。",
      url)}
{STYLE}
</head>
{body}"""
    path = os.path.join(OUTDIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(doc)
    print(filename, len(doc))


def main():
    build_index()
    for i in range(len(vol_meta)):
        build_volume(i)


main()
