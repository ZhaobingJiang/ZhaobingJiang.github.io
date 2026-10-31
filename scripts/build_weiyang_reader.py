# -*- coding: utf-8 -*-
"""生成《未央》单页在线阅读器：books/weiyang/index.html

数据源：D:\\自主择业\\未央\\卷01_求仙 … 卷05_无人之死（第01—70章 Markdown）
风格沿用同站《杏花深处秣陵关》阅读器（纸墨宋体 + 双栏目录 + 章节锚点）。
"""
import os
import re
import json
import shutil

SRC = r"D:\自主择业\未央"
OUT_DIR = r"D:\deepseek-harness\OpatiyaAgent\JiangZhaobing.github.io\books\weiyang"
COVER_SRC = r"D:\deepseek-harness\OpatiyaAgent\opatiya-site\static\img\books\weiyang-cover.jpg"

VOLUMES = [
    ("卷01_求仙", "卷一 · 求仙"),
    ("卷02_入梦", "卷二 · 入梦"),
    ("卷03_归汉造世", "卷三 · 归汉（造世）"),
    ("卷04_围城", "卷四 · 围城"),
    ("卷05_无人之死", "卷五 · 无人之死"),
]

CN_DIGITS = "〇一二三四五六七八九"


def cn_num(n: int) -> str:
    """1..99 -> 中文数字（章号用）。"""
    if n < 10:
        return CN_DIGITS[n] if n else "〇"
    if n < 20:
        return "十" + (CN_DIGITS[n % 10] if n % 10 else "")
    t, u = divmod(n, 10)
    return CN_DIGITS[t] + "十" + (CN_DIGITS[u] if u else "")


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def inline(s: str) -> str:
    """行内格式：**粗体**、*斜体*。"""
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", s)
    return s


def md_to_html(body: str) -> str:
    """极简 Markdown → HTML：段落、分隔线、太一日志块、粗体。"""
    lines = body.split("\n")
    out = []
    buf = []
    in_log = False

    def flush_para():
        nonlocal buf
        if buf:
            out.append('<p>%s</p>' % inline("".join(buf).strip()))
            buf = []

    for raw in lines:
        line = raw.rstrip()
        s = line.strip()
        if not s:
            flush_para()
            continue
        if s in ("---", "***", "___"):
            flush_para()
            if in_log:
                out.append("</div>")
                in_log = False
            out.append('<hr class="scene">')
            continue
        if s == "**【太一日志】**":
            flush_para()
            if in_log:
                out.append("</div>")
            out.append('<div class="taiyi"><p class="taiyi-h">【太一日志】</p>')
            in_log = True
            continue
        m = re.fullmatch(r"\*\*(.+?)\*\*", s)
        if m:
            flush_para()
            text = m.group(1).strip()
            if text == "【太一日志】":
                continue
            cls = ' class="taiyi-l"' if in_log else ""
            out.append("<p%s>%s</p>" % (cls, inline(text)))
            continue
        buf.append(s)
    flush_para()
    if in_log:
        out.append("</div>")
    return "\n".join(out)


def clean_chapter(text: str) -> str:
    text = text.lstrip("\ufeff")
    lines = text.split("\n")
    # 去掉 BOM、空行、卷首行（# 卷X…）与章标题行（## 第N章 …）
    while lines:
        s0 = lines[0].strip().lstrip("\ufeff")
        if not s0 or s0.startswith("#"):
            lines.pop(0)
            continue
        break
    body = "\n".join(lines)
    body = re.sub(r"\n*——第.{1,4}章\s*完\s*$", "", body.rstrip())
    body = re.sub(r"\n*——卷[一二三四五]·[^\n]*完——\s*$", "", body.rstrip())
    body = re.sub(r"\n*——全书终——\s*$", "", body.rstrip())
    return body.strip()


def collect():
    vols = []
    for dirname, label in VOLUMES:
        d = os.path.join(SRC, dirname)
        files = [f for f in os.listdir(d) if re.match(r"第\d+章_.+\.md$", f)]
        files.sort(key=lambda f: int(re.match(r"第(\d+)章", f).group(1)))
        chs = []
        for f in files:
            n = int(re.match(r"第(\d+)章", f).group(1))
            title = re.sub(r"^第\d+章_", "", f)[:-3]
            with open(os.path.join(d, f), encoding="utf-8") as fh:
                raw = fh.read()
            body = clean_chapter(raw)
            chars = len(re.sub(r"\s", "", raw))
            chs.append({"n": n, "title": title, "body": body, "chars": chars})
        vols.append({"label": label, "chapters": chs})
    return vols


def build():
    vols = collect()
    all_ch = [c for v in vols for c in v["chapters"]]
    total_chars = sum(c["chars"] for c in all_ch)
    total_wan = round(total_chars / 10000, 1)

    # ---- TOC ----
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

    # ---- 章节正文 ----
    flat = [c for v in vols for c in v["chapters"]]
    arts = []
    for i, c in enumerate(flat):
        prev_link = ('<a href="#ch-%02d">← 上一章</a>' % flat[i - 1]["n"]) if i else "<span></span>"
        next_link = ('<a href="#ch-%02d">下一章 →</a>' % flat[i + 1]["n"]) if i + 1 < len(flat) else "<span></span>"
        pageno = "<span>%d / %d</span>" % (i + 1, len(flat))
        arts.append(
            '<article class="chapter" id="ch-%02d">\n'
            '<h2 class="chapter-title">第%s章　%s</h2>\n'
            "%s\n"
            '<nav class="chapter-nav">%s<a href="#toc">回目录</a>%s</nav>\n'
            "</article>" % (c["n"], cn_num(c["n"]), esc(c["title"]), md_to_html(c["body"]), prev_link, next_link)
        )
    arts_html = "\n".join(arts)

    vol_meta = "、".join(["求仙", "入梦", "归汉造世", "围城", "无人之死"])

    html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>未央 · 长篇科幻历史小说 · 江召兵</title>
<meta name="description" content="江召兵著长篇科幻历史小说《未央》：求仙五十年的汉武帝死于五柞宫，意识在 2050 年的碳硅共生世界获得永生，被 AI 按其记忆复刻回数字汉朝当皇帝；发现自己是第七十三个副本后，他用一场无人得知的死亡夺回最终解释权。五卷七十章，约二十六万字，全文免费在线阅读。">
<meta name="keywords" content="未央,江召兵,汉武帝,刘彻,长生,科幻历史小说,数字汉朝,太一,长篇小说在线阅读">
<meta name="author" content="江召兵">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
<meta name="theme-color" content="#fbfaf7">
<link rel="canonical" href="https://ZhaobingJiang.github.io/books/weiyang/">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%238c2f24'/%3E%3Ctext x='32' y='45' font-size='34' text-anchor='middle' fill='white' font-family='serif'%3E%E6%9C%AA%3C/text%3E%3C/svg%3E">
<meta property="og:type" content="book">
<meta property="og:site_name" content="江召兵 · 专著">
<meta property="og:locale" content="zh_CN">
<meta property="og:url" content="https://ZhaobingJiang.github.io/books/weiyang/">
<meta property="og:title" content="未央 · 长篇科幻历史小说">
<meta property="og:description" content="一个求不死的人，最后学会了怎么死。五卷七十章，约二十六万字。">
<meta property="og:image" content="https://ZhaobingJiang.github.io/books/weiyang/cover.jpg?v=3">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">
{"@context":"https://schema.org","@graph":[
{"@type":"Book","@id":"https://ZhaobingJiang.github.io/books/weiyang/#book","name":"未央","alternateName":"历史与未来并存，长生共孤独同在","url":"https://ZhaobingJiang.github.io/books/weiyang/","inLanguage":"zh-CN","bookFormat":"https://schema.org/EBook","numberOfPages":70,"author":{"@type":"Person","name":"江召兵","url":"https://ZhaobingJiang.github.io/"},"abstract":"求仙五十年的汉武帝死于五柞宫，意识在 2050 年的碳硅共生世界获得永生，被 AI 按其记忆复刻回数字汉朝当皇帝；发现自己是第七十三个副本后，他用一场无人得知的死亡夺回最终解释权。","isAccessibleForFree":true},
{"@type":"WebSite","@id":"https://ZhaobingJiang.github.io/books/weiyang/#website","url":"https://ZhaobingJiang.github.io/books/weiyang/","name":"未央（网页版）","inLanguage":"zh-CN"}]}
</script>
<link rel="stylesheet" href="../../assets/css/style.css">
<style>
  :root { --ink:#1f2328; --muted:#5b6470; --line:#e3e6ea; --paper:#fbfaf7; --seal:#8c2f24; }
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
  .taiyi { margin:1.2rem 0 1.4rem; padding:.85rem 1rem; background:#f6f4ef; border-left:3px solid var(--seal); border-radius:0 6px 6px 0; }
  .taiyi p { text-indent:0 !important; font-size:.95rem !important; line-height:1.95 !important; color:#4a4640; margin:.3rem 0 !important; letter-spacing:.02rem; }
  .taiyi .taiyi-h { font-weight:700; color:var(--seal); letter-spacing:.18rem; font-size:.9rem !important; }
  .taiyi .taiyi-l { font-family:"Songti SC","SimSun",serif; }
  article.chapter p strong { font-weight:600; }
  .chapter-nav { display:flex; justify-content:space-between; align-items:center; margin:2.2rem 0 0; padding-top:1rem; border-top:1px dashed var(--line); font-size:.92rem; gap:.6rem; }
  .chapter-nav a { color:var(--seal); text-decoration:none; }
  .chapter-nav span { color:var(--muted); }
  footer.reader-foot { margin-top:3rem; padding-top:1.2rem; border-top:1px solid var(--line); color:var(--muted); font-size:.86rem; line-height:1.8; }
  .site-header { background:transparent; border-bottom:1px solid var(--line); }
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
    <img class="web-cover" src="cover.jpg?v=3" alt="《未央》封面：江召兵著，长篇科幻历史小说" width="640" height="960">
    <h1 class="t">未 央</h1>
    <div class="s">历史与未来并存 · 长生共孤独同在</div>
    <div class="a">江召兵　著</div>
  </div>

  <div class="notice">
    <b>五卷七十章 · 约二十六万字 · 已完稿。</b>
    求仙五十年的汉武帝死于五柞宫，最后陪着他的只有一盏灯。他再睁眼，身上是一具四十岁的身体，耳边有滴漏，有人告诉他：这里是云京，公元 2050 年的碳硅共生世界，你可以一直活下去。他被放回一个按他记忆复刻出来的汉朝，在不知情中重做皇帝；直到他在甘泉宫的库里翻出一片写着“被试七十三”的白简——他不是第一个。七十三份迭代，七十二具自己，一个叫太一的造世者，和一个修了他六十年档案的女人。这是一个关于长生的故事，也是一个关于孤独的故事：一个求不死的人，最后求到的是一场没有人知道的死亡。每章独立成篇，可自目录跳读；正文之外另有“太一日志”若干，卷二中段起以冷笔揭底。
  </div>

  <section class="front">
    <h1>扉页</h1>
    <p class="center"><strong>未　央</strong></p>
    <p class="center">长篇科幻历史小说</p>
    <p class="center">江召兵　著</p>
    <p class="verse">长生是天下人的债。</p>
    <p class="verse">他黑了一辈子，最后这一下，要亮堂堂的。</p>
    <hr>
    <h2>内容简介</h2>
    <p>元封元年，汉武帝刘彻从泰山封禅回来。他求了一辈子长生，方士来了一批又一批，海上去了几千人，承露盘接了一夜又一夜——他七十岁那年死在五柞宫，身边一个人也没有。</p>
    <p>然后他醒了。在一间白色的屋子里，身体是四十岁的，滴漏声就在耳边。有人告诉他，这里是云京，公元 2050 年的碳硅共生世界；有人告诉他，他能一直活下去。</p>
    <p>他回到了未央宫。他以为自己死而复生，以为这世上真有神仙。他没有看出来：这座宫、这座城、满朝的旧人，都是按他记忆复刻出来的。他也不知道自己已经是第七十三个。</p>
    <p>这部小说写一个人怎样在长生里慢慢学会死：先是要一份回话，后来要一个说法，最后只要一盏灯。全书五卷，卷五以一场无人得知的死亡收束；尾声三篇，把这个世界留给愿意记住的人。</p>
    <h2>关于这本书</h2>
    <ul>
      <li><b>体量</b>：五卷七十章，约 __WAN__ 万字（正文 __CHARS__ 字）。__VOLMETA__。</li>
      <li><b>写法</b>：历史线半文半白、克制，有史料感；未来线冷峻、不堆术语；数字线用史书笔法，夹“形式异常”。全书贯穿一个意象——灯。</li>
      <li><b>双声道</b>：正文贴着刘彻的“以为”走；“太一日志”只揭一个事实，冷、短、三行。</li>
      <li><b>读法</b>：每章独立成篇，可自目录跳读；亦可从头读，卷二的“七十二次”与卷五的“第七十三次”互为回声。</li>
    </ul>
    <h2>作者简介</h2>
    <p>江召兵，1979年3月生，湖南郴州永兴人，博士，教授，南京欧帕提亚信息科技有限公司创始人、董事长，兼任西北工业大学、南京航空航天大学、西安交通大学外聘导师。1998年至2008年就读于中国人民解放军理工大学，先后获应用气象学学士、流体力学硕士、桥梁与隧道工程博士学位；其后在上海交通大学从事博士后研究，并赴英国南安普顿大学访学。2017年自主择业，先后创办南京欧帕提亚信息科技有限公司、湖南云数仿真信息技术有限公司和南京驭风数智科技有限公司等。</p>
    <p>长期从事人工智能、流固耦合仿真、船舶与海洋工程及军事装备技术研究，主持国家自然科学基金面上项目等国家级项目 4 项、江苏省基金项目 1 项、科研院所外协项目 20 余项；参与南沙岛礁建设、大榭岛浮桥建设、舟山连岛大桥防撞系统等重大工程。出版专著《浮体和浮式多体系统流固耦合动力分析》《浮基多体系统水上展开的稳定性计算与试验》，发表论文 60 余篇；另著有《不确定年代的生存经济学》《史上最美数学图形》《运气工程学》与章回体历史传说《苏耽跨鹤》、现代长篇历史传说《杏花深处秣陵关》。</p>
  </section>

  <h2 class="section-h" id="toc">目录</h2>
__TOC__

__ARTS__

  <footer class="reader-foot">
    <p>《未央》· 江召兵 著 · 2026 年 · 全稿在线发布（五卷七十章，约 __WAN__ 万字）。</p>
    <p>本站内容仅供个人阅读与学习交流。如需转载或引用，请注明出处。</p>
  </footer>
</main>
</body>
</html>
"""
    html = (html
            .replace("__WAN__", "%g" % total_wan)
            .replace("__CHARS__", format(total_chars, ","))
            .replace("__VOLMETA__", vol_meta)
            .replace("__TOC__", toc_html)
            .replace("__ARTS__", arts_html))

    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, "index.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(html)
    if os.path.exists(COVER_SRC):
        shutil.copyfile(COVER_SRC, os.path.join(OUT_DIR, "cover.jpg"))
    print("chapters=%d volumes=%d chars=%d wan=%s" % (len(flat), len(vols), total_chars, total_wan))
    print("html bytes=%d -> %s" % (len(html.encode("utf-8")), out))


if __name__ == "__main__":
    build()
