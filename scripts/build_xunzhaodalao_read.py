# -*- coding: utf-8 -*-
"""Build the full-text web edition of 《寻找大佬》 from chapter markdown."""
from pathlib import Path
import re
import html

SRC = Path(r"D:\自主择业\江召兵诗词\chinese-novelist\20261105-寻找大佬\章节")
OUT = Path(r"D:\deepseek-harness\OpatiyaAgent\JiangZhaobing.github.io\books\xunzhaodalao\read.html")

SLUG = "xunzhaodalao"
TITLE = "寻找大佬"
SUBTITLE = "路漫漫其修远兮，吾将上下而求索。"
WORDS = "约三十五万字"

# (volume title, era, first chapter number, last chapter number); chapter 0 is the 楔子
VOLUMES = [
    ("卷一 · 泥", "一九八九—二〇〇一", 1, 7),
    ("卷二 · 阶梯", "二〇〇一—二〇一〇", 8, 16),
    ("卷三 · 高处", "二〇一〇—二〇一九", 17, 24),
    ("卷四 · 江湖", "二〇一九—二〇二三", 25, 34),
    ("卷五 · 托举", "二〇二三—二〇二六", 35, 40),
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


def collect_files():
    """Return {chapter_no: path} using filenames and the leading H1."""
    files = {}
    for path in sorted(SRC.glob("第*章-*.md")):
        m = re.match(r"第(\d{2})章-", path.name)
        if m:
            files[int(m.group(1))] = path
    return files


def parse_chapter(path: Path):
    lines = path.read_text(encoding="utf-8").splitlines()
    title = normalize_title(lines[0].lstrip("#").strip())
    body = []
    for line in lines[1:]:
        text = line.strip()
        if not text:
            continue
        body.append(f"<p>{inline(text)}</p>")
    return title, "\n".join(body)


FILES = collect_files()
NUMBERS = sorted(FILES)
assert NUMBERS == list(range(0, 41)), NUMBERS

toc_parts = ['<h3 class="vol-h">楔子 <span>一九八九—二〇二六</span></h3>', '<ol class="toc">']
title0, _ = parse_chapter(FILES[0])
toc_parts.append(f'<li><a href="#ch-00">{title0}</a></li>')
toc_parts.append("</ol>")

for vol_name, era, start, end in VOLUMES:
    toc_parts.append(f'<h3 class="vol-h">{vol_name} <span>{era}</span></h3>')
    toc_parts.append('<ol class="toc">')
    for n in range(start, end + 1):
        title, _ = parse_chapter(FILES[n])
        toc_parts.append(f'<li><a href="#ch-{n:02d}">{title}</a></li>')
    toc_parts.append("</ol>")

article_parts = []
for idx, n in enumerate(NUMBERS):
    title, body = parse_chapter(FILES[n])
    prev_link = (
        f'<a href="#ch-{NUMBERS[idx - 1]:02d}">← 上一章</a>' if idx > 0 else "<span></span>"
    )
    next_link = (
        f'<a href="#ch-{NUMBERS[idx + 1]:02d}">下一章 →</a>' if idx < len(NUMBERS) - 1 else "<span></span>"
    )
    article_parts.append(
        f'<article class="chapter" id="ch-{n:02d}">\n'
        f'<h2 class="chapter-title">{title}</h2>\n'
        f"{body}\n"
        f'<div class="chapter-nav"><a href="#toc">目录</a>{prev_link}{next_link}</div>\n'
        f"</article>"
    )

toc_html = "\n".join(toc_parts)
articles_html = "\n\n".join(article_parts)

html_doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{TITLE} · 全文在线阅读 · 江召兵</title>
<meta name="description" content="江召兵长篇小说《{TITLE}》全文在线阅读：1989—2026，从陈家坳到MIT。五卷四十章，{WORDS}，全书完成。">
<meta name="keywords" content="{TITLE},江召兵,长篇小说,在线阅读,寒门,自卑与超越,阿德勒,成长小说">
<meta name="author" content="江召兵">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
<meta name="theme-color" content="#fbfaf7">
<link rel="canonical" href="https://ZhaobingJiang.github.io/books/{SLUG}/read.html">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%2333405a'/%3E%3Ctext x='32' y='45' font-size='32' text-anchor='middle' fill='white' font-family='serif'%3E%E6%89%BE%3C/text%3E%3C/svg%3E">
<meta property="og:type" content="book">
<meta property="og:site_name" content="江召兵 · 专著">
<meta property="og:locale" content="zh_CN">
<meta property="og:url" content="https://ZhaobingJiang.github.io/books/{SLUG}/read.html">
<meta property="og:title" content="{TITLE} · 全文在线阅读">
<meta property="og:description" content="1989—2026，从陈家坳到MIT。五卷四十章，{WORDS}，全文在线阅读。">
<meta property="og:image" content="https://ZhaobingJiang.github.io/books/{SLUG}/cover.jpg?v=4">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"Book","name":"{TITLE}","url":"https://ZhaobingJiang.github.io/books/{SLUG}/","inLanguage":"zh-CN","bookFormat":"https://schema.org/EBook","author":{{"@type":"Person","name":"江召兵","url":"https://ZhaobingJiang.github.io/"}},"numberOfPages":40,"bookEdition":"网页版","isAccessibleForFree":true,"creativeWorkStatus":"全书完成"}}
</script>
<link rel="stylesheet" href="../../assets/css/style.css">
<style>
  :root {{ --ink:#1f2328; --muted:#5b6470; --line:#e3e6ea; --paper:#fbfaf7; --seal:#33405a; }}
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
  .read-top a {{ display:inline-block; padding:.42rem .9rem; border:1px solid #c9cdd6; border-radius:999px; color:var(--seal); text-decoration:none; font-size:.9rem; }}
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
  article.chapter p strong {{ font-weight:600; }}
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
    <img class="web-cover" src="cover.jpg?v=4" alt="《{TITLE}》封面：江召兵著，长篇小说" width="1600" height="2400">
    <h1 class="t">寻找大佬</h1>
    <div class="s">{SUBTITLE}</div>
    <div class="a">江召兵　著</div>
  </div>

  <div class="notice">
    <b>五卷四十章 · {WORDS} · 全书完成</b><br>
    1989—2026。一个从黄土坡上走出来的少年，用三十七年寻找能拉他一把的人；等他站到最亮的地方，一个学生问他：您是怎么找到大佬的？
  </div>
  <div class="read-top">
    <a href="index.html">作品页 · 梗概</a>
    <a href="#toc">目录</a>
    <a href="#ch-00">开始阅读</a>
  </div>

  <h2 class="section-h" id="toc">目录</h2>
  {toc_html}

  {articles_html}

  <footer class="reader-foot">
    <p>《{TITLE}》 · 江召兵 著 · 五卷四十章 · {WORDS} · 全书完</p>
    <p><a href="index.html">返回作品页</a> · <a href="../../zh/books.html">返回中文书籍</a></p>
  </footer>
</main>
<script src="/assets/js/site-counter.js?v=3" defer></script>
</body>
</html>
"""

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(html_doc, encoding="utf-8")
print(f"Wrote {OUT} ({len(html_doc)} chars)")
print(f"Chapters: {len(NUMBERS)}")
