# -*- coding: utf-8 -*-
"""Build the full-text web edition of 《账本》 from chapter markdown."""
from pathlib import Path
import re
import html

SRC = Path(r"D:\自主择业\江召兵诗词\chinese-novelist\20261103-2306-账本\chapters")
OUT = Path(r"D:\deepseek-harness\OpatiyaAgent\JiangZhaobing.github.io\books\zhangben\read.html")

VOLUMES = [
    ("卷一 · 空碗", 1, 10, "一九五三—一九六六"),
    ("卷二 · 泥土", 11, 20, "一九六六—一九七七"),
    ("卷三 · 两个世界", 21, 29, "一九七八—一九九二"),
    ("卷四 · 盛宴", 30, 40, "一九九三—二〇一二"),
    ("卷五 · 审计", 41, 46, "二〇一三—二〇二三"),
]


def inline(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    return text


def normalize_title(raw: str) -> str:
    raw = re.sub(r"\s+", " ", raw.strip())
    m = re.match(r"^第\s*([0-9]+|[一二三四五六七八九十百零〇]+)\s*章\s*(.*)$", raw)
    if m:
        num = m.group(1)
        prefix = f"第 {num} 章" if num.isdigit() else f"第{num}章"
        return f"{prefix}　{m.group(2).strip()}"
    return raw


def parse_chapter(path: Path):
    lines = path.read_text(encoding="utf-8").splitlines()
    title = normalize_title(lines[0].lstrip("#").strip())
    body = []
    i = 1
    first_body = True
    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip():
            i += 1
            continue
        if line.startswith("## "):
            body.append(f'<h3 class="sec">{inline(line[3:].strip())}</h3>')
            first_body = False
        elif line.startswith(">"):
            quote_lines = []
            while i < len(lines) and lines[i].startswith(">"):
                quote_lines.append(lines[i].lstrip(">").strip())
                i += 1
            body.append(
                '<blockquote>'
                + "".join(f"<p>{inline(q)}</p>" for q in quote_lines if q)
                + "</blockquote>"
            )
            first_body = False
            continue
        elif line.strip() == "---":
            body.append('<div class="sep"></div>')
            first_body = False
        else:
            text = line.strip()
            if first_body and re.fullmatch(r"[一二三四五六七八九〇零0-9—\-～~]+", text):
                body.append(f'<p class="era">{inline(text)}</p>')
            else:
                body.append(f"<p>{inline(text)}</p>")
            first_body = False
        i += 1
    return title, "\n".join(body)


toc_parts = []
article_parts = []
all_titles = {}

for vi, (vol_name, start, end, era) in enumerate(VOLUMES):
    toc_parts.append(f'<h3 class="vol-h">{vol_name} <span>{era}</span></h3>')
    toc_parts.append('<ol class="toc">')
    for n in range(start, end + 1):
        path = SRC / f"ch{n:02d}.md"
        title, body = parse_chapter(path)
        all_titles[n] = title
        toc_parts.append(f'<li><a href="#ch-{n:02d}">{title}</a></li>')
    toc_parts.append("</ol>")

for n in range(1, 47):
    path = SRC / f"ch{n:02d}.md"
    title, body = parse_chapter(path)
    prev_link = f'<a href="#ch-{n-1:02d}">← 上一章</a>' if n > 1 else '<span></span>'
    next_link = f'<a href="#ch-{n+1:02d}">下一章 →</a>' if n < 46 else '<span></span>'
    article_parts.append(
        f'<article class="chapter" id="ch-{n:02d}">\n'
        f'<h2 class="chapter-title">{title}</h2>\n'
        f'{body}\n'
        f'<div class="chapter-nav"><a href="#toc">目录</a>{prev_link}{next_link}</div>\n'
        f'</article>'
    )

toc_html = "\n".join(toc_parts)
articles_html = "\n\n".join(article_parts)

html_doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>账本 · 全文在线阅读 · 江召兵</title>
<meta name="description" content="江召兵长篇小说《账本》全文在线阅读：一个饥饿者的七十年。1953—2023，甘肃通渭。五卷四十六章，约三十一万字。">
<meta name="keywords" content="账本,江召兵,长篇小说,在线阅读,甘肃通渭,饥饿,心理小说">
<meta name="author" content="江召兵">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
<meta name="theme-color" content="#fbfaf7">
<link rel="canonical" href="https://ZhaobingJiang.github.io/books/zhangben/read.html">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%238e221c'/%3E%3Ctext x='32' y='45' font-size='32' text-anchor='middle' fill='white' font-family='serif'%3E%E8%B4%A6%3C/text%3E%3C/svg%3E">
<meta property="og:type" content="book">
<meta property="og:site_name" content="江召兵 · 专著">
<meta property="og:locale" content="zh_CN">
<meta property="og:url" content="https://ZhaobingJiang.github.io/books/zhangben/read.html">
<meta property="og:title" content="账本 · 全文在线阅读">
<meta property="og:description" content="一个饥饿者的七十年。1953—2023，甘肃通渭。五卷四十六章，约三十一万字，全文在线阅读。">
<meta property="og:image" content="https://ZhaobingJiang.github.io/books/zhangben/cover.jpg?v=2">
<meta name="twitter:card" content="summary_large_image">
<link rel="stylesheet" href="../../assets/css/style.css">
<style>
  :root {{ --ink:#1f2328; --muted:#5b6470; --line:#e3e6ea; --paper:#fbfaf7; --seal:#8e221c; }}
  body {{ background:var(--paper); color:var(--ink); }}
  .reader {{ max-width:46rem; margin:0 auto; padding:1.2rem 1.15rem 4rem; }}
  .book-head {{ text-align:center; padding:2.2rem 0 1.2rem; border-bottom:1px solid var(--line); }}
  .book-head .t {{ font-size:2.5rem; letter-spacing:.5rem; margin:0 0 .6rem; font-family:"Songti SC","SimSun",serif; }}
  .book-head .s {{ color:var(--muted); letter-spacing:.22rem; font-size:.95rem; }}
  .book-head .a {{ margin-top:.9rem; font-size:1.05rem; }}
  .web-cover {{ width:210px; height:auto; max-width:58%; display:block; margin:0 auto 1.2rem; border:1px solid var(--line); box-shadow:0 8px 22px rgba(0,0,0,.10); }}
  .notice {{ margin:1.2rem 0 0; padding:.9rem 1rem; background:#fff; border:1px solid var(--line); border-radius:8px; font-size:.92rem; color:var(--muted); line-height:1.75; }}
  .notice b {{ color:var(--ink); }}
  .read-top {{ display:flex; gap:.7rem; flex-wrap:wrap; justify-content:center; margin:1.2rem 0 0; }}
  .read-top a {{ display:inline-block; padding:.42rem .9rem; border:1px solid #d8c6b8; border-radius:999px; color:var(--seal); text-decoration:none; font-size:.9rem; }}
  h2.section-h {{ margin:2.4rem 0 1rem; font-size:1.15rem; letter-spacing:.1rem; padding-left:.6rem; border-left:4px solid var(--seal); }}
  h3.vol-h {{ margin:1.8rem 0 .5rem; font-size:1.02rem; letter-spacing:.12rem; color:var(--seal); }}
  h3.vol-h span {{ color:var(--muted); font-weight:400; letter-spacing:.06rem; margin-left:.6rem; font-size:.88rem; }}
  ol.toc {{ list-style:none; padding:0; margin:0 0 1.2rem; column-count:2; column-gap:2.4rem; }}
  ol.toc li {{ padding:.45rem .2rem; border-bottom:1px dashed var(--line); break-inside:avoid; font-size:.97rem; }}
  ol.toc a {{ color:var(--ink); text-decoration:none; }}
  ol.toc a:hover {{ color:var(--seal); }}
  article.chapter {{ margin:3rem 0 0; padding-top:.6rem; border-top:1px solid var(--line); }}
  .chapter-title {{ font-size:1.3rem; line-height:1.9; margin:.4rem 0 1.4rem; padding-bottom:.7rem; border-bottom:2px solid var(--ink); font-family:"Songti SC","SimSun",serif; letter-spacing:.04rem; }}
  article.chapter p {{ font-family:"Songti SC","SimSun",serif; font-size:1.06rem; line-height:2.05; text-indent:2em; margin:.7rem 0; }}
  article.chapter p.era {{ text-indent:0; text-align:center; color:var(--muted); font-family:"Kaiti SC","KaiTi",serif; font-size:.96rem; letter-spacing:.12rem; margin:.2rem 0 1.4rem; }}
  article.chapter p strong {{ font-weight:600; }}
  article.chapter blockquote {{ margin:1rem 0 1.2rem; padding:.65rem 1rem; border-left:3px solid #d8c6b8; background:#fff; color:#4a4f55; }}
  article.chapter blockquote p {{ text-indent:0; font-size:.97rem; line-height:1.9; margin:.25rem 0; }}
  article.chapter h3.sec {{ font-size:1.08rem; letter-spacing:.1rem; margin:1.8rem 0 .8rem; color:var(--seal); }}
  article.chapter .sep {{ height:.55rem; }}
  .chapter-nav {{ display:flex; justify-content:space-between; align-items:center; margin:2.2rem 0 0; padding-top:1rem; border-top:1px dashed var(--line); font-size:.92rem; gap:.6rem; }}
  .chapter-nav a {{ color:var(--seal); text-decoration:none; }}
  footer.reader-foot {{ margin-top:3rem; padding-top:1.2rem; border-top:1px solid var(--line); color:var(--muted); font-size:.86rem; line-height:1.8; }}
  @media (max-width:640px) {{ .book-head .t {{ font-size:2rem; letter-spacing:.3rem; }} ol.toc {{ column-count:1; }} article.chapter p {{ font-size:1.02rem; line-height:1.95; }} }}
</style>
</head>
<body>
<header class="site-header">
  <nav class="site-nav">
    <a href="../../" class="nav-link">首页</a>
    <a href="../../zh/books.html" class="nav-link">中文书籍</a>
    <a href="../" class="nav-link">Books</a>
  </nav>
</header>

<main class="reader">
  <div class="book-head">
    <img class="web-cover" src="cover.jpg?v=2" alt="《账本》封面：江召兵著，长篇小说" width="1600" height="2400">
    <h1 class="t">账　本</h1>
    <div class="s">一个饥饿者的七十年</div>
    <div class="a">江召兵　著</div>
  </div>

  <div class="notice">
    <b>五卷四十六章 · 约三十一万字 · 全书完</b><br>
    1953—2023，甘肃通渭。一个把每一笔得失都记在心里的人，最后发现自己欠下的那一笔算不清。本页为全文网页版，可从头读，也可从目录跳读。
  </div>
  <div class="read-top">
    <a href="index.html">作品页 · 梗概</a>
    <a href="#toc">目录</a>
    <a href="#ch-01">开始阅读</a>
  </div>

  <h2 class="section-h" id="toc">目录</h2>
  {toc_html}

  {articles_html}

  <footer class="reader-foot">
    <p>《账本》 · 江召兵 著 · 五卷四十六章 · 约三十一万字 · 全书完</p>
    <p><a href="index.html">返回作品页</a> · <a href="../../zh/books.html">返回中文书籍</a></p>
  </footer>
</main>
<script src="/assets/js/site-counter.js?v=3" defer></script>
</body>
</html>
"""

OUT.write_text(html_doc, encoding="utf-8")
print(f"Wrote {OUT} ({len(html_doc)} chars)")
print(f"Chapters: {len(all_titles)}")
