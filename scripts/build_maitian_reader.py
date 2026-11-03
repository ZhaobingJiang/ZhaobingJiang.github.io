# -*- coding: utf-8 -*-
"""生成《麦田怪圈》单页在线阅读器：books/maitian-guiquan/index.html

数据源：D:\\自主择业\\江召兵诗词\\麦田怪圈小说\\书稿\\第01—40章 Markdown
风格沿用同站《未央》《丽品金陵》阅读器（纸墨宋体 + 双栏目录 + 章节锚点）。
"""
import os
import re

SRC = r"D:\自主择业\江召兵诗词\麦田怪圈小说\书稿"
OUT_DIR = r"D:\deepseek-harness\OpatiyaAgent\JiangZhaobing.github.io\books\maitian-guiquan"

VOLUMES = [
    ("bofang", "卷一 · 播种", 1, 12),
    ("chousui", "卷二 · 抽穗", 13, 27),
    ("shouge", "卷三 · 收割", 28, 40),
]

CN_DIGITS = "〇一二三四五六七八九"


def cn_num(n: int) -> str:
    if n < 10:
        return CN_DIGITS[n] if n else "〇"
    if n < 20:
        return "十" + (CN_DIGITS[n % 10] if n % 10 else "")
    t, u = divmod(n, 10)
    return CN_DIGITS[t] + "十" + (CN_DIGITS[u] if u else "")


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def inline(s: str) -> str:
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", s)
    return s


def md_to_html(body: str) -> str:
    """Markdown → HTML：段落、场景分隔线、插页块（【插页·…】＋引用行）。"""
    out = []
    buf = []
    quote = []
    in_insert = False
    in_quote = False

    def flush_para():
        nonlocal buf
        if buf:
            out.append("<p>%s</p>" % inline("".join(buf).strip()))
            buf = []

    def flush_quote():
        nonlocal quote
        if quote:
            text = "<br>".join(inline(q) for q in quote if q.strip())
            if text:
                out.append('<p class="insert-l">%s</p>' % text)
            quote = []

    for raw in body.split("\n"):
        s = raw.strip()
        if not s:
            flush_para()
            if in_quote:
                flush_quote()
                in_quote = False
            continue

        m = re.fullmatch(r"【(.+?)】", s)
        if m:
            flush_para()
            flush_quote()
            in_quote = False
            if in_insert:
                out.append("</div>")
            label = m.group(1)
            out.append('<div class="insert"><p class="insert-h">【%s】</p>' % esc(label))
            in_insert = True
            continue

        if s in ("---", "***", "___"):
            flush_para()
            flush_quote()
            in_quote = False
            if in_insert:
                out.append("</div>")
                in_insert = False
            out.append('<hr class="scene">')
            continue

        if s.startswith(">"):
            flush_para()
            in_quote = True
            quote.append(s.lstrip("> ").strip())
            continue

        if in_quote:
            flush_quote()
            in_quote = False

        if in_insert:
            out.append("</div>")
            in_insert = False
        buf.append(s)

    flush_para()
    flush_quote()
    if in_insert:
        out.append("</div>")
    return "\n".join(out)


def clean_chapter(text: str) -> str:
    text = text.lstrip("\ufeff")
    lines = text.split("\n")
    while lines:
        s0 = lines[0].strip().lstrip("\ufeff")
        if not s0 or s0.startswith("#"):
            lines.pop(0)
            continue
        break
    body = "\n".join(lines)
    body = re.sub(r"\n*——第.{1,4}章\s*完\s*$", "", body.rstrip())
    body = re.sub(r"\n*——全书终——\s*$", "", body.rstrip())
    return body.strip()


def collect():
    vols = []
    for _, label, lo, hi in VOLUMES:
        chs = []
        for n in range(lo, hi + 1):
            hits = [f for f in os.listdir(SRC) if re.match(r"第%02d章_" % n, f)]
            if not hits:
                raise FileNotFoundError("missing chapter %02d" % n)
            fn = hits[0]
            title = re.sub(r"^第\d+章_", "", fn)[:-3]
            with open(os.path.join(SRC, fn), encoding="utf-8") as fh:
                raw = fh.read()
            body = clean_chapter(raw)
            chars = len(re.sub(r"\s", "", raw))
            chs.append({"n": n, "title": title, "body": body, "chars": chars})
        vols.append({"label": label, "chapters": chs})
    return vols


def build():
    vols = collect()
    flat = [c for v in vols for c in v["chapters"]]
    total_chars = sum(c["chars"] for c in flat)
    total_wan = round(total_chars / 10000, 1)

    toc_parts = []
    for v in vols:
        toc_parts.append('<h3 class="vol-h">%s</h3>' % esc(v["label"]))
        items = []
        for c in v["chapters"]:
            items.append(
                '<li><a href="#ch-%02d">第%s章　%s</a></li>'
                % (c["n"], cn_num(c["n"]), esc(c["title"]))
            )
        toc_parts.append('<ol class="toc">' + "".join(items) + "</ol>")
    toc_html = "\n".join(toc_parts)

    arts = []
    for i, c in enumerate(flat):
        prev_link = ('<a href="#ch-%02d">← 上一章</a>' % flat[i - 1]["n"]) if i else "<span></span>"
        next_link = ('<a href="#ch-%02d">下一章 →</a>' % flat[i + 1]["n"]) if i + 1 < len(flat) else "<span></span>"
        arts.append(
            '<article class="chapter" id="ch-%02d">\n'
            '<h2 class="chapter-title">第%s章　%s</h2>\n'
            "%s\n"
            '<nav class="chapter-nav">%s<a href="#toc">回目录</a>%s</nav>\n'
            "</article>" % (c["n"], cn_num(c["n"]), esc(c["title"]), md_to_html(c["body"]), prev_link, next_link)
        )
    arts_html = "\n".join(arts)

    html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>麦田怪圈 · 悬疑长篇小说 · 江召兵</title>
<meta name="description" content="江召兵著悬疑长篇小说《麦田怪圈》：二〇一二年，记者林深报道了一桩麦田怪圈的骗局；同年，十五岁的姜小穗失踪。十二年后，她的父亲用两种麦子种出一张六十米的人脸，只为让林深重新看一眼当年那张航拍照片。三卷四十章，约十七万字，全文免费在线阅读。">
<meta name="keywords" content="麦田怪圈,江召兵,悬疑小说,长篇小说,柳洼村,姜小穗,林深,在线阅读">
<meta name="author" content="江召兵">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
<meta name="theme-color" content="#fbfaf7">
<link rel="canonical" href="https://ZhaobingJiang.github.io/books/maitian-guiquan/">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%237a5a2e'/%3E%3Ctext x='32' y='44' font-size='30' text-anchor='middle' fill='white' font-family='serif'%3E%E9%BA%A6%3C/text%3E%3C/svg%3E">
<meta property="og:type" content="book">
<meta property="og:site_name" content="江召兵 · 专著">
<meta property="og:locale" content="zh_CN">
<meta property="og:url" content="https://ZhaobingJiang.github.io/books/maitian-guiquan/">
<meta property="og:title" content="麦田怪圈 · 悬疑长篇小说">
<meta property="og:description" content="十二年后，麦田里长出一张脸。三卷四十章，约十七万字。">
<meta property="og:image" content="https://ZhaobingJiang.github.io/books/maitian-guiquan/cover.jpg?v=1">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">
{"@context":"https://schema.org","@graph":[
{"@type":"Book","@id":"https://ZhaobingJiang.github.io/books/maitian-guiquan/#book","name":"麦田怪圈","alternateName":"十二年后，麦田里长出一张脸","url":"https://ZhaobingJiang.github.io/books/maitian-guiquan/","inLanguage":"zh-CN","bookFormat":"https://schema.org/EBook","numberOfPages":40,"author":{"@type":"Person","name":"江召兵","url":"https://ZhaobingJiang.github.io/"},"abstract":"二〇一二年，记者林深报道了一桩麦田怪圈的骗局；同年，十五岁的姜小穗失踪。十二年后，她的父亲用两种麦子种出一张六十米的人脸，只为让林深重新看一眼当年那张航拍照片。","isAccessibleForFree":true},
{"@type":"WebSite","@id":"https://ZhaobingJiang.github.io/books/maitian-guiquan/#website","url":"https://ZhaobingJiang.github.io/books/maitian-guiquan/","name":"麦田怪圈（网页版）","inLanguage":"zh-CN"}]}
</script>
<link rel="stylesheet" href="../../assets/css/style.css">
<style>
  :root { --ink:#1f2328; --muted:#5b6470; --line:#e3e6ea; --paper:#fbfaf7; --seal:#7a5a2e; }
  body { background:var(--paper); color:var(--ink); }
  .reader { max-width: 46rem; margin: 0 auto; padding: 1.2rem 1.15rem 4rem; }
  .book-head { text-align:center; padding: 2.2rem 0 1.2rem; border-bottom:1px solid var(--line); }
  .book-head .t { font-size: 2.5rem; letter-spacing: .5rem; margin: 0 0 .6rem; font-family: "Songti SC","SimSun",serif; }
  .book-head .s { color:var(--muted); letter-spacing:.22rem; font-size:.95rem; }
  .book-head .a { margin-top: .9rem; font-size:1.05rem; }
  .web-cover { width: 210px; height: auto; max-width: 58%; display:block; margin: 0 auto 1.2rem; border:1px solid var(--line); box-shadow: 0 8px 22px rgba(0,0,0,.10); }
  .notice { margin:1.2rem 0 0; padding:.9rem 1rem; background:#fff; border:1px solid var(--line); border-radius:8px; font-size:.92rem; color:var(--muted); line-height:1.75; }
  .notice b { color:var(--ink); }
  .front { margin: 2rem 0; padding: 1.4rem 1.5rem; background:#fff; border:1px solid var(--line); border-radius:10px; }
  .front h1 { font-size:1.05rem; letter-spacing:.15rem; margin:.2rem 0 1rem; }
  .front h2 { font-size:1rem; margin:1.5rem 0 .6rem; }
  .front p { line-height:1.95; text-indent:2em; margin:.55rem 0; }
  .front p.verse { text-indent:0; text-align:center; color:var(--muted); font-family:"Kaiti SC","KaiTi",serif; }
  .front p.center { text-indent:0; text-align:center; margin:.7rem 0; letter-spacing:.1em; }
  .front ul { margin:.4rem 0 .4rem 1.2rem; padding:0; }
  .front li { line-height:1.9; font-size:.97rem; }
  h2.section-h { margin:2.4rem 0 1rem; font-size:1.15rem; letter-spacing:.1rem; padding-left:.6rem; border-left:4px solid var(--seal); }
  h3.vol-h { margin:1.8rem 0 .5rem; font-size:1.02rem; letter-spacing:.12rem; color:var(--seal); }
  ol.toc { list-style:none; padding:0; margin:0; column-count:2; column-gap:2.4rem; }
  ol.toc li { padding:.45rem .2rem; border-bottom:1px dashed var(--line); break-inside:avoid; font-size:.97rem; }
  ol.toc a { color:var(--ink); text-decoration:none; }
  ol.toc a:hover { color:var(--seal); }
  article.chapter { margin:3rem 0 0; padding-top:.6rem; border-top:1px solid var(--line); }
  .chapter-title { font-size:1.3rem; line-height:1.9; margin:.4rem 0 1.4rem; padding-bottom:.7rem; border-bottom:2px solid var(--ink); font-family:"Songti SC","SimSun",serif; letter-spacing:.04rem; }
  article.chapter p { font-family:"Songti SC","SimSun",serif; font-size:1.06rem; line-height:2.05; text-indent:2em; margin:.7rem 0; }
  article.chapter hr.scene { border:0; margin:1.9rem auto; width:38%; border-top:1px solid var(--line); }
  .insert { margin:1.2rem 0 1.4rem; padding:.85rem 1rem; background:#f6f4ef; border-left:3px solid var(--seal); border-radius:0 6px 6px 0; }
  .insert p { text-indent:0 !important; font-size:.95rem !important; line-height:1.95 !important; color:#4a4640; margin:.3rem 0 !important; letter-spacing:.02rem; }
  .insert .insert-h { font-weight:700; color:var(--seal); letter-spacing:.18rem; font-size:.9rem !important; }
  .insert .insert-l { font-family:"Songti SC","SimSun",serif; }
  article.chapter p strong { font-weight:600; }
  .chapter-nav { display:flex; justify-content:space-between; align-items:center; margin:2.2rem 0 0; padding-top:1rem; border-top:1px dashed var(--line); font-size:.92rem; gap:.6rem; }
  .chapter-nav a { color:var(--seal); text-decoration:none; }
  .chapter-nav span { color:var(--muted); }
  footer.reader-foot { margin-top:3rem; padding-top:1.2rem; border-top:1px solid var(--line); color:var(--muted); font-size:.86rem; line-height:1.8; }
  @media (max-width:640px) { .book-head .t { font-size:2rem; letter-spacing:.3rem; } ol.toc { column-count:1; } article.chapter p { font-size:1.02rem; line-height:1.95; } }
</style>
</head>
<body>
<header class="site-header">
  <nav class="site-nav">
    <a href="../../" class="nav-link">首页</a>
    <a href="../" class="nav-link">专著与书稿</a>
    <a href="../../zh/books.html" class="nav-link">中文书籍</a>
  </nav>
</header>

<main class="reader">
  <div class="book-head">
    <img class="web-cover" src="cover.jpg?v=1" alt="《麦田怪圈》封面：江召兵著，悬疑长篇小说" width="640" height="960">
    <h1 class="t">麦 田 怪 圈</h1>
    <div class="s">十二年后，麦田里长出一张脸</div>
    <div class="a">江召兵　著</div>
  </div>

  <div class="notice">
    <b>三卷四十章 · 约 __WAN__ 万字 · 已完稿。</b>
    二〇一二年，记者林深在柳洼村报道了一桩麦田怪圈的骗局：四个少年用木板压出一张“外星人的脸”。同年夏天，十五岁的姜小穗失踪。十二年后，她的父亲姜守田用两种成熟期不同的麦子，在自家地里种出一张六十米的人脸；无人机拍到它，全网都说是神迹。林深回到村里，才认出这不是压出来的圈，是种出来的——而老人要的不是神迹，是让他重新看一眼当年那张航拍照片：照片里的假怪圈外，还站着一个人。三卷四十章，两条时间线，一桩被麦田替人保守了十二年的谋杀。
  </div>

  <section class="front">
    <h1>扉页</h1>
    <p class="center"><strong>麦　田　怪　圈</strong></p>
    <p class="center">悬疑长篇小说</p>
    <p class="center">江召兵　著</p>
    <p class="verse">麦子会记住。人不会。</p>
    <p class="verse">他种的不是圈，是一个让所有人重新看一眼的借口。</p>
    <hr>
    <h2>内容简介</h2>
    <p>二〇一二年六月，平川县柳洼村的麦田里“长”出一张外星人的脸。实习记者林深跟着老摄影记者刘振山赶到村里，写下《谁在麦田里撒谎》，拿了奖，转了正。几天后，村里十五岁的女孩姜小穗失踪，案子悬了十二年。</p>
    <p>二〇二四年六月，一张六十米长的人脸出现在同一片麦田里。主播白露的无人机视频一夜爆火，专家、艺术家、教派、官员、资本轮番进场，都说这圈是自己的。只有林深看出：麦子没有倒，是种的——用两种成熟期相差七天的麦子，按一张铅笔画的轮廓错期播种，长出来就是一张脸。</p>
    <p>种圈的人是姜小穗的父亲姜守田。他种了三年，失败两次，只为一件事：让林深回来，重新看一遍二〇一二年六月十九日下午他拍下的那张航拍照片。照片里，假怪圈外三十米，站着一个穿红背心的人，脚边是新土。</p>
    <p>本书以林深的第一人称回望写成，双时间线交替推进：二〇一二年那个夏天，与二〇二四年那场全网围观。每一章后附一页“伪文献”——日记、直播文字稿、实验记录、讯问笔录、信件、作文批语——让那些不被听见的人自己开口。</p>
    <h2>关于这本书</h2>
    <ul>
      <li><b>体量</b>：三卷四十章，约 __WAN__ 万字（正文 __CHARS__ 字）。卷一播种（一至十二章）、卷二抽穗（十三至二十七章）、卷三收割（二十八至四十章）。</li>
      <li><b>结构</b>：双时间线（二〇一二／二〇二四）＋每章一页伪文献插页；五层反转，最后一层落在“报道者本人也参与了掩埋”。</li>
      <li><b>人物</b>：八位女性角色——姜小穗、沈栀、白露、苏晚、刘桂兰、陈玉兰、张秀芹、方韵——其中五人是推动主线转折的核心人物。</li>
      <li><b>写法</b>：克制、白描、多用物证与农事细节；不写鬼，不写神，只写人怎样替自己圆一个谎，又怎样被一个父亲用麦子逼着把谎说完。</li>
    </ul>
    <h2>作者简介</h2>
    <p>江召兵，1979年3月生，湖南郴州永兴人，博士，教授，南京欧帕提亚信息科技有限公司创始人、董事长，兼任西北工业大学、南京航空航天大学、西安交通大学外聘导师。1998年至2008年就读于中国人民解放军理工大学，先后获应用气象学学士、流体力学硕士、桥梁与隧道工程博士学位；其后在上海交通大学从事博士后研究，并赴英国南安普顿大学访学。2017年自主择业，先后创办南京欧帕提亚信息科技有限公司、湖南云数仿真信息技术有限公司和南京驭风数智科技有限公司等。</p>
    <p>长期从事人工智能、流固耦合仿真、船舶与海洋工程及军事装备技术研究，主持国家自然科学基金面上项目等国家级项目 4 项、江苏省基金项目 1 项、科研院所外协项目 20 余项；参与南沙岛礁建设、大榭岛浮桥建设、舟山连岛大桥防撞系统等重大工程。出版专著《浮体和浮式多体系统流固耦合动力分析》《浮基多体系统水上展开的稳定性计算与试验》，发表论文 60 余篇；另著有《不确定年代的生存经济学》《史上最美数学图形》《运气工程学》与章回体历史传说《苏耽跨鹤》、现代长篇历史传说《杏花深处秣陵关》等。</p>
  </section>

  <h2 class="section-h" id="toc">目录</h2>
__TOC__

__ARTS__

  <footer class="reader-foot">
    <p>《麦田怪圈》· 江召兵 著 · 2026 年 · 全稿在线发布（三卷四十章，约 __WAN__ 万字）。</p>
    <p>本站内容仅供个人阅读与学习交流。如需转载或引用，请注明出处。</p>
  </footer>
</main>
</body>
</html>
"""
    html = (html
            .replace("__WAN__", "%g" % total_wan)
            .replace("__CHARS__", format(total_chars, ","))
            .replace("__TOC__", toc_html)
            .replace("__ARTS__", arts_html))

    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, "index.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(html)
    print("chapters=%d chars=%d wan=%s" % (len(flat), total_chars, total_wan))
    print("html bytes=%d -> %s" % (len(html.encode("utf-8")), out))


if __name__ == "__main__":
    build()
