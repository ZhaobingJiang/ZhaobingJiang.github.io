# -*- coding: utf-8 -*-
"""Render the reading edition of 《歌舞团》 as a single-page HTML file."""
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = r"D:\deepseek-harness\OpatiyaAgent\JiangZhaobing.github.io"
OUT = os.path.join(SITE, "books", "gewutuan", "index.html")

with open(os.path.join(ROOT, "book.json"), encoding="utf-8") as f:
    BOOK = json.load(f)

SITE_URL = "https://ZhaobingJiang.github.io/books/gewutuan/"
TITLE = "歌舞团"
SUBTITLE = "一部揭文艺圈老底的浮世绘 · 台上台下的性与爱、权与色"
AUTHOR = "赖俊熙"

VOL_LABEL = {"卷一": "卷一", "卷二": "卷二", "卷三": "卷三", "卷四": "卷四", "卷五": "卷五"}

# section number by order
sections = BOOK["sections"]
for i, s in enumerate(sections, 1):
    s["no"] = i
    s["anchor"] = f"sec-{i:02d}"

total_chars = sum(len(p) for p in BOOK["preface"]) + sum(
    len(p) for s in sections for p in s["paras"]
)
wan = round(total_chars / 10000, 1)


def esc(t):
    return html.escape(t, quote=False)


def para_html(p):
    p = esc(p)
    p = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", p)
    return f"<p>{p}</p>"


# ---------------------------------------------------------------- head
head = f"""<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{TITLE} · 长篇小说 · {AUTHOR}</title>
<meta name="description" content="{AUTHOR}长篇小说《歌舞团》：五卷四十六节，约 {wan} 万字。N 市歌舞剧团团长调任在即，团长的位子空了出来——排练、评奖、调演、饭局之间，一场关于权与色的浮世绘。全书免费在线阅读。">
<meta name="keywords" content="歌舞团,{AUTHOR},长篇小说,文艺圈,官场,权色,在线阅读,全文">
<meta name="author" content="{AUTHOR}">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
<meta name="theme-color" content="#fbfaf7">
<link rel="canonical" href="{SITE_URL}">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%238c2f24'/%3E%3Ctext x='32' y='45' font-size='32' text-anchor='middle' fill='white' font-family='serif'%3E%E6%AD%8C%3C/text%3E%3C/svg%3E">
<meta property="og:type" content="book">
<meta property="og:site_name" content="江召兵 · 专著">
<meta property="og:locale" content="zh_CN">
<meta property="og:url" content="{SITE_URL}">
<meta property="og:title" content="{TITLE} · 长篇小说">
<meta property="og:description" content="五卷四十六节，约 {wan} 万字。台上台下的性与爱、权与色，一部揭文艺圈老底的浮世绘。全书免费在线阅读。">
<meta property="og:image" content="{SITE_URL}cover.jpg?v=1">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">
{{"@context":"https://schema.org","@graph":[
{{"@type":"Book","@id":"{SITE_URL}#book","name":"{TITLE}","url":"{SITE_URL}","inLanguage":"zh-CN","bookFormat":"https://schema.org/EBook","numberOfPages":437,"author":{{"@type":"Person","name":"{AUTHOR}"}},"publisher":{{"@type":"Organization","name":"德宏民族出版社"}},"datePublished":"2002-11","isbn":"7-80525-682-9","abstract":"N 市歌舞剧团团长调任在即，团长的位子空了出来。排练、评奖、调演、饭局与床笫之间，一部写文艺圈内幕的长篇小说。","isAccessibleForFree":true}},
{{"@type":"WebSite","@id":"{SITE_URL}#website","url":"{SITE_URL}","name":"歌舞团（网页版）","inLanguage":"zh-CN"}}]}}
</script>
<link rel="stylesheet" href="../../assets/css/style.css">"""

# ---------------------------------------------------------------- style
style = """<style>
  :root { --ink:#1f2328; --muted:#5b6470; --line:#e3e6ea; --paper:#fbfaf7; --seal:#8c2f24; }
  body { background:var(--paper); color:var(--ink); }
  .reader { max-width:46rem; margin:0 auto; padding:1.2rem 1.15rem 4rem; }
  .book-head { text-align:center; padding:2.2rem 0 1.2rem; border-bottom:1px solid var(--line); }
  .book-head .t { font-size:2.5rem; letter-spacing:.5rem; margin:0 0 .6rem; font-family:"Songti SC","SimSun",serif; }
  .book-head .s { color:var(--muted); letter-spacing:.12rem; font-size:.95rem; line-height:1.7; }
  .book-head .a { margin-top:.9rem; font-size:1.05rem; }
  .web-cover { width:210px; height:auto; max-width:58%; display:block; margin:0 auto 1.2rem; border:1px solid var(--line); box-shadow:0 8px 22px rgba(0,0,0,.10); }
  .notice { margin:1.2rem 0 0; padding:.9rem 1rem; background:#fff; border:1px solid var(--line); border-radius:8px; font-size:.92rem; color:var(--muted); line-height:1.75; }
  .notice b { color:var(--ink); }
  .read-top { display:flex; gap:.7rem; flex-wrap:wrap; justify-content:center; margin:1.2rem 0 0; }
  .read-top a { display:inline-block; padding:.42rem .9rem; border:1px solid #d8c6b8; border-radius:999px; color:var(--seal); text-decoration:none; font-size:.9rem; }
  section.front { margin:1.6rem 0 0; padding:1.2rem 1.15rem; background:#fff; border:1px solid var(--line); border-radius:8px; }
  section.front h1 { font-size:1.15rem; letter-spacing:.1rem; text-align:center; margin:.2rem 0 1rem; color:var(--muted); font-weight:600; }
  section.front h2 { font-size:1.05rem; letter-spacing:.08rem; margin:1.4rem 0 .6rem; padding-left:.55rem; border-left:3px solid var(--seal); }
  section.front p { font-family:"Songti SC","SimSun",serif; font-size:.98rem; line-height:1.95; margin:.55rem 0; text-indent:2em; }
  section.front p.center { text-indent:0; text-align:center; margin:.25rem 0; }
  section.front p.verse { text-indent:0; text-align:center; color:var(--muted); font-family:"Kaiti SC","KaiTi",serif; font-size:.92rem; margin:.6rem 0; }
  section.front hr { border:0; border-top:1px dashed var(--line); margin:1.1rem 0; }
  h2.section-h { margin:2.4rem 0 1rem; font-size:1.15rem; letter-spacing:.1rem; padding-left:.6rem; border-left:4px solid var(--seal); }
  ol.toc { list-style:none; padding:0; margin:0 0 1.2rem; column-count:2; column-gap:2.4rem; }
  ol.toc > li { padding:.45rem .2rem; border-bottom:1px dashed var(--line); break-inside:avoid; font-size:.97rem; }
  ol.toc a { color:var(--ink); text-decoration:none; }
  ol.toc a:hover { color:var(--seal); }
  ol.toc li.toc-part { border-bottom:0; padding-bottom:.1rem; }
  ol.toc li.toc-part > a { color:var(--seal); font-weight:600; letter-spacing:.12rem; }
  ol.toc ul.toc-sub { list-style:none; margin:.15rem 0 .6rem; padding:0 0 0 .2rem; }
  ol.toc ul.toc-sub li { padding:.3rem 0; border-bottom:1px dotted var(--line); font-size:.94rem; }
  h2.vol-head { text-align:center; font-size:1.45rem; letter-spacing:.7rem; margin:3.4rem 0 1.2rem; padding:.5rem 0; color:var(--seal); border-top:1px solid var(--line); border-bottom:1px solid var(--line); font-family:"Songti SC","SimSun",serif; }
  article.chapter { margin:2.6rem 0 0; padding-top:.6rem; }
  .chapter-title { font-size:1.3rem; line-height:1.9; margin:.4rem 0 1.4rem; padding-bottom:.7rem; border-bottom:2px solid var(--ink); font-family:"Songti SC","SimSun",serif; letter-spacing:.04rem; }
  article.chapter p { font-family:"Songti SC","SimSun",serif; font-size:1.06rem; line-height:2.05; text-indent:2em; margin:.7rem 0; }
  article.chapter p.era { text-indent:0; text-align:center; color:var(--muted); font-family:"Kaiti SC","KaiTi",serif; font-size:.96rem; letter-spacing:.12rem; margin:.2rem 0 1.4rem; }
  .chapter-nav { display:flex; justify-content:space-between; align-items:center; margin:2.2rem 0 0; padding-top:1rem; border-top:1px dashed var(--line); font-size:.92rem; gap:.6rem; }
  .chapter-nav a { color:var(--seal); text-decoration:none; }
  footer.reader-foot { margin-top:3rem; padding-top:1.2rem; border-top:1px solid var(--line); color:var(--muted); font-size:.86rem; line-height:1.8; }
  @media (max-width:640px) {
    .book-head .t { font-size:2rem; letter-spacing:.3rem; }
    ol.toc { column-count:1; }
    article.chapter p { font-size:1.02rem; line-height:1.95; }
  }
</style>"""

# ---------------------------------------------------------------- body
parts = []
parts.append(
    f"""<body>
<header class="site-header">
  <nav class="site-nav">
    <a href="../../" class="nav-link">首页</a>
    <a href="../" class="nav-link">专著与书稿</a>
    <a href="../../zh/books.html" class="nav-link">中文书籍</a>
  </nav>
</header>

<main class="reader" id="top">
  <div class="book-head">
    <img class="web-cover" src="cover.jpg?v=1" alt="《歌舞团》封面：赖俊熙著，德宏民族出版社" width="640" height="960">
    <h1 class="t">{TITLE}</h1>
    <div class="s">{SUBTITLE}</div>
    <div class="a">{AUTHOR}　著</div>
  </div>

  <div class="notice">
    <b>五卷四十六节 · 约 {total_chars / 10000:.1f} 万字 · 据德宏民族出版社 2002 年 11 月第 1 版扫描本整理。</b>
    团长的位子空出来以后，排练场、评委会、酒席与卧室都成了同一张牌桌。全书免费在线阅读。
  </div>

  <div class="read-top">
    <a href="#preface">作者序</a>
    <a href="#toc">目录</a>
    <a href="#sec-01">开始阅读</a>
  </div>

  <section class="front">
    <h1>扉页</h1>
    <p class="center"><strong>歌　舞　团</strong></p>
    <p class="center">长篇小说</p>
    <p class="center">{AUTHOR}　著</p>
    <p class="center">德宏民族出版社</p>
    <hr>
    <h2>内容简介</h2>
    <p>N 市歌舞剧团团长邱彤将调省音乐学院，团长的位子还没有空出来，团里团外已经有许多人瞄上了。一把手调走，二把手本该顺理成章地顶上去，偏偏第一副团长高建年纪大了、又患糖尿病，第二副团长曹欣刚提起来不久，于是空出来的那半格，成了所有人眼里的机会。</p>
    <p>白玉婉是这个团里的舞蹈演员，人漂亮，心也活。她一边在排练场里争角色，一边在饭桌上、在领导家里为自己找路。文化局长王扶之握着剧目能不能投排、能不能上报调演的签字笔；剧作者白一凡和沈羽帆捧着自己写的本子，在评奖、改稿、换导演的一连串关卡里来回打转。一部戏从讨论会到舞台，要过多少人的手，就要看多少人的脸色。</p>
    <p>全书分五卷四十六节，从“部长儿媳”写到“完美境界”：争位子、抢本子、跑评奖、陪酒局、造舆论、拆台子，台上演的是戏，台下演的是人。作者以冷峻的白描写文艺圈内外的权力与欲望，也写一群人在其中如何一步步变得不像自己。</p>
    <hr>
    <h2>出版信息</h2>
    <p class="center">著　　者　{AUTHOR}</p>
    <p class="center">责任编辑　思继春</p>
    <p class="center">封面设计　刘梁伟</p>
    <p class="center">出版发行　德宏民族出版社</p>
    <p class="center">2002 年 11 月第 1 版　2002 年 11 月第 1 次印刷</p>
    <p class="center">印张 15　字数 280 千　定价 19.80 元</p>
    <p class="center">ISBN 7-80525-682-9 / I · 120</p>
    <hr>
    <h2>整理说明</h2>
    <p>本网页版据德宏民族出版社 2002 年 11 月第 1 版扫描本整理。原书无电子文本，全书由扫描页逐页识别、校订后重新排版；扫描页上的污损、断笔与装订阴影处按上下文补正，个别字词仍可能有疏漏，读者发现后欢迎指正。</p>
    <p>原书目录只标卷次与节题，本版按原书卷次、节次与先后顺序编排，未增删正文内容；仅对明显的标点、断行与异体字作了规范化处理。</p>
  </section>

  <h2 class="section-h" id="toc">目录</h2>"""
)

# ---- TOC
toc = ['<ol class="toc">']
toc.append('<li><a href="#preface">作者序</a></li>')
for vi, (vol, items) in enumerate(BOOK["toc"], 1):
    toc.append(f'<li class="toc-part"><a href="#vol-{vi}">{vol}</a><ul class="toc-sub">')
    for title, _page in items:
        sec = next(s for s in sections if s["vol"] == vol and s["title"] == title)
        toc.append(f'<li><a href="#{sec["anchor"]}">{esc(title)}</a></li>')
    toc.append("</ul></li>")
toc.append("</ol>")
parts.append("\n".join(toc))

# ---- preface
parts.append(
    '<article class="chapter" id="preface">\n<h2 class="chapter-title">作者序</h2>'
)
parts.extend(para_html(p) for p in BOOK["preface"])
parts.append(
    '<nav class="chapter-nav"><span></span><a href="#toc">回目录</a>'
    '<a href="#sec-01">下一篇 →</a></nav>\n</article>'
)

# ---- volumes and sections
flat = []
vol_index = {}
for s in sections:
    if s["vol"] not in vol_index:
        vol_index[s["vol"]] = len(vol_index) + 1
    flat.append(s)

for i, s in enumerate(flat):
    if i == 0 or flat[i - 1]["vol"] != s["vol"]:
        v = vol_index[s["vol"]]
        parts.append(f'<h2 class="vol-head" id="vol-{v}">{s["vol"]}</h2>')
    prev_anchor = flat[i - 1]["anchor"] if i > 0 else "preface"
    prev_txt = flat[i - 1]["title"] if i > 0 else "作者序"
    if i + 1 < len(flat):
        nxt_anchor, nxt_txt = flat[i + 1]["anchor"], flat[i + 1]["title"]
    else:
        nxt_anchor, nxt_txt = None, None
    parts.append(f'<article class="chapter" id="{s["anchor"]}">')
    parts.append(f'<h2 class="chapter-title">{esc(s["title"])}</h2>')
    parts.extend(para_html(p) for p in s["paras"])
    next_link = (
        f'<a href="#{nxt_anchor}">下一篇 →</a>' if nxt_anchor else "<span></span>"
    )
    parts.append(
        f'<nav class="chapter-nav"><a href="#{prev_anchor}">← 上一篇</a>'
        f'<a href="#toc">回目录</a>{next_link}</nav>\n</article>'
    )

parts.append(
    f"""<footer class="reader-foot">
    <p>《歌舞团》· {AUTHOR} 著 · 德宏民族出版社 2002 年 11 月第 1 版 · 五卷四十六节 · 约 {total_chars / 10000:.1f} 万字 · 网页版在线发布。</p>
    <p>原著版权归作者及德宏民族出版社所有。本网页版据扫描本整理排版，仅供个人阅读与学习交流，不作商业用途；整理稿中的疏漏以原著为准。</p>
  </footer>
</main>
</body>
</html>
"""
)

doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
{head}
{style}
</head>
{''.join(parts)}
"""

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(doc)
print(f"wrote {OUT}  bytes={len(doc.encode('utf-8'))}  sections={len(sections)} chars={total_chars}")
