# -*- coding: utf-8 -*-
"""生成《丽品金陵》单页在线阅读器：books/lipin-jinling/index.html

数据源：D:\\自主择业\\江召兵诗词\\丽品金陵
  14_楔子与尾声/楔子_花名册.md
  10_卷一/第01—08回.md
  11_卷二/第09—16回.md
  12_卷三/第17—24回.md
  13_卷四/第25—32回.md
  14_楔子与尾声/尾声_后之览者.md
  15_附录_板桥杂记原文/00_附录说明.md + 附录一至四（《板桥杂记》原文）
版式沿用同站《未央》阅读器（纸墨宋体 + 双栏目录 + 章节锚点）。
"""
import os
import re
import html as htmlmod
import shutil

SRC = r"D:\自主择业\江召兵诗词\丽品金陵"
OUT_DIR = r"D:\deepseek-harness\OpatiyaAgent\JiangZhaobing.github.io\books\lipin-jinling"
COVER_SRC = os.path.join(SRC, "封面", "cover.jpg")

CN = "〇一二三四五六七八九"


def esc(s):
    return htmlmod.escape(s, quote=False)


def inline(s):
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", s)
    return s


def md_to_html(body):
    """极简 Markdown → HTML：段落、引文（> 行做诗行）、分隔线、粗体。"""
    out, buf, verse, ul = [], [], [], []

    def flush_para():
        nonlocal buf
        if buf:
            out.append("<p>%s</p>" % inline("".join(buf).strip()))
            buf = []

    def flush_list():
        nonlocal ul
        if ul:
            out.append("<ul>" + "".join("<li>%s</li>" % x for x in ul) + "</ul>")
            ul = []

    def flush_verse():
        nonlocal verse
        if verse:
            out.append('<p class="verse">%s</p>' % "<br>".join(inline(v) for v in verse))
            verse = []

    for raw in body.split("\n"):
        s = raw.strip()
        if not s:
            flush_para()
            flush_verse()
            flush_list()
            continue
        if s in ("---", "***", "___"):
            flush_para()
            flush_verse()
            flush_list()
            out.append('<hr class="scene">')
            continue
        if s.startswith(">"):
            flush_para()
            flush_list()
            verse.append(s[1:].strip())
            continue
        if s.startswith("- "):
            flush_para()
            flush_verse()
            ul.append(inline(s[2:].strip()))
            continue
        if s.startswith("#"):
            flush_para()
            flush_verse()
            flush_list()
            continue
        flush_verse()
        flush_list()
        buf.append(s)
    flush_para()
    flush_verse()
    flush_list()
    return "\n".join(out)


def read_md(path):
    with open(path, encoding="utf-8-sig") as fh:
        text = fh.read().replace("\r\n", "\n")
    lines = text.split("\n")
    title = None
    while lines:
        s0 = lines[0].strip()
        if s0.startswith("# "):
            title = s0[2:].strip()
            lines.pop(0)
            break
        if not s0:
            lines.pop(0)
            continue
        break
    body = "\n".join(lines).strip()
    body = re.sub(r"\n*——第[一二三四五六七八九十百]+回\s*完\s*$", "", body)
    chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    return title or os.path.splitext(os.path.basename(path))[0], body, chars


def files_in(folder):
    d = os.path.join(SRC, folder)
    fs = [f for f in os.listdir(d) if f.endswith(".md") and re.match(r"第\d+回_", f)]
    fs.sort(key=lambda f: int(re.match(r"第(\d+)回", f).group(1)))
    return [os.path.join(d, f) for f in fs]


def collect():
    sections = []
    sec = {"label": "楔子", "items": []}
    p = os.path.join(SRC, "14_楔子与尾声", "楔子_花名册.md")
    t, b, c = read_md(p)
    sec["items"].append({"id": "ch-00", "toc": t, "title": t, "body": b, "kind": "chapter", "chars": c})
    sections.append(sec)

    vols = [
        ("卷一 · 灯船", "10_卷一"),
        ("卷二 · 眉楼", "11_卷二"),
        ("卷三 · 兵火", "12_卷三"),
        ("卷四 · 白头", "13_卷四"),
    ]
    n = 1
    for label, folder in vols:
        sec = {"label": label, "items": []}
        for p in files_in(folder):
            t, b, c = read_md(p)
            sec["items"].append({"id": "ch-%02d" % n, "toc": t, "title": t, "body": b, "kind": "chapter", "chars": c})
            n += 1
        sections.append(sec)

    sec = {"label": "尾声", "items": []}
    t, b, c = read_md(os.path.join(SRC, "14_楔子与尾声", "尾声_后之览者.md"))
    sec["items"].append({"id": "ch-33", "toc": t, "title": t, "body": b, "kind": "chapter", "chars": c})
    sections.append(sec)

    # 附录
    ap_dir = os.path.join(SRC, "15_附录_板桥杂记原文")
    sec = {"label": "附录 · 《板桥杂记》原文", "items": []}
    order = ["00_附录说明.md", "附录一_序.md", "附录二_雅游.md", "附录三_丽品.md", "附录四_轶事.md"]
    for i, f in enumerate(order):
        t, b, c = read_md(os.path.join(ap_dir, f))
        sec["items"].append({"id": "ap-%02d" % i, "toc": t, "title": t, "body": b, "kind": "appendix", "chars": c})
    sections.append(sec)
    return sections


def build():
    sections = collect()
    flat = []
    for sec in sections:
        for it in sec["items"]:
            flat.append(it)
    # 汉字统计
    body_chars = sum(it["chars"] for it in flat if it["kind"] == "chapter")
    ap_chars = sum(len(re.findall(r"[\u4e00-\u9fff]", it["body"])) for it in flat if it["kind"] == "appendix" and it["id"] != "ap-00")
    main_chars = body_chars + ap_chars
    wan = "%.1f" % (main_chars / 10000.0)
    body_wan = "%.1f" % (body_chars / 10000.0)

    # TOC
    toc_parts = []
    for sec in sections:
        toc_parts.append('<h3 class="vol-h">%s</h3>' % esc(sec["label"]))
        items = ['<li><a href="#%s">%s</a></li>' % (it["id"], esc(it["toc"])) for it in sec["items"]]
        toc_parts.append('<ol class="toc">' + "".join(items) + "</ol>")
    toc_html = "\n".join(toc_parts)

    # 正文
    arts = []
    chap_items = [it for it in flat if it["kind"] == "chapter"]
    idx = {it["id"]: i for i, it in enumerate(flat)}
    for i, it in enumerate(flat):
        prev_id = flat[i - 1]["id"] if i else None
        next_id = flat[i + 1]["id"] if i + 1 < len(flat) else None
        prev_link = '<a href="#%s">← 上一章</a>' % prev_id if prev_id else "<span></span>"
        next_link = '<a href="#%s">下一章 →</a>' % next_id if next_id else "<span></span>"
        pageno = "<span>%d / %d</span>" % (idx[it["id"]] + 1, len(flat))
        cls = "chapter appendix" if it["kind"] == "appendix" else "chapter"
        note = ""
        if it["kind"] == "appendix" and it["id"] != "ap-00":
            note = ('<div class="yuanwen-note"><b>原文附录</b> · 据清·三山余怀（字澹心）《板桥杂记》'
                    '，仅分段标点，未作删改。</div>')
        arts.append(
            '<article class="%s" id="%s">\n'
            '<h2 class="chapter-title">%s</h2>\n'
            "%s\n%s\n"
            '<nav class="chapter-nav">%s%s%s</nav>\n'
            "</article>" % (cls, it["id"], esc(it["title"]), note, md_to_html(it["body"]),
                            prev_link, "<a href=\"#toc\">回目录</a>", next_link)
        )
    arts_html = "\n".join(arts)

    html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>丽品金陵 · 长篇历史小说 · 江召兵</title>
<meta name="description" content="江召兵著长篇历史小说《丽品金陵》：以清·余怀《板桥杂记》为骨，写秦淮诸姬在明清易代中的命运，以及一个记录者的三十年。四卷三十二章，楔子、尾声，并附录《板桥杂记》原文四卷。全文免费在线阅读。">
<meta name="keywords" content="丽品金陵,江召兵,板桥杂记,余怀,秦淮,金陵,明清易代,秦淮八艳,历史小说,长篇在线阅读">
<meta name="author" content="江召兵">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
<meta name="theme-color" content="#fbfaf7">
<link rel="canonical" href="https://ZhaobingJiang.github.io/books/lipin-jinling/">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%238c2f24'/%3E%3Ctext x='32' y='45' font-size='34' text-anchor='middle' fill='white' font-family='serif'%3E%E4%B8%BD%3C/text%3E%3C/svg%3E">
<meta property="og:type" content="book">
<meta property="og:site_name" content="江召兵 · 专著">
<meta property="og:locale" content="zh_CN">
<meta property="og:url" content="https://ZhaobingJiang.github.io/books/lipin-jinling/">
<meta property="og:title" content="丽品金陵 · 长篇历史小说">
<meta property="og:description" content="灯船照夜，眉楼藏画；兵火来时，各自白头。四卷三十二章，附《板桥杂记》原文。">
<meta property="og:image" content="https://ZhaobingJiang.github.io/books/lipin-jinling/cover.jpg?v=3">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">
{"@context":"https://schema.org","@graph":[
{"@type":"Book","@id":"https://ZhaobingJiang.github.io/books/lipin-jinling/#book","name":"丽品金陵","alternateName":"秦淮旧院 · 十二钗传","url":"https://ZhaobingJiang.github.io/books/lipin-jinling/","inLanguage":"zh-CN","bookFormat":"https://schema.org/EBook","numberOfPages":33,"author":{"@type":"Person","name":"江召兵","url":"https://ZhaobingJiang.github.io/"},"abstract":"以清·余怀《板桥杂记》为骨，写秦淮诸姬在明清易代中的命运：十二主传、四卷三十二章、楔子与尾声，并附录《板桥杂记》原文四卷。","isAccessibleForFree":true},
{"@type":"WebSite","@id":"https://ZhaobingJiang.github.io/books/lipin-jinling/#website","url":"https://ZhaobingJiang.github.io/books/lipin-jinling/","name":"丽品金陵（网页版）","inLanguage":"zh-CN"}]}
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
  article.chapter p.verse { text-indent:0; text-align:center; color:#4a4640; }
  article.chapter hr.scene { border:0; margin:1.9rem auto; width:38%; border-top:1px solid var(--line); }
  article.appendix p { font-size:1.02rem; line-height:1.95; }
  .yuanwen-note { margin:0 0 1.2rem; padding:.7rem .9rem; background:#f6f4ef; border-left:3px solid var(--seal); border-radius:0 6px 6px 0; font-size:.9rem; color:#4a4640; line-height:1.8; }
  .yuanwen-note b { color:var(--seal); letter-spacing:.12rem; }
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
    <img class="web-cover" src="cover.jpg?v=3" alt="《丽品金陵》封面：江召兵著，长篇历史小说" width="640" height="960">
    <h1 class="t">丽 品 金 陵</h1>
    <div class="s">秦淮旧院 · 十二钗传</div>
    <div class="a">江召兵　著</div>
  </div>

  <div class="notice">
    <b>楔子＋四卷三十二章＋尾声 · 正文约 __BODYWAN__ 万字 · 附《板桥杂记》原文四卷 · 已完稿。</b>
    崇祯末年，金陵长板桥边，旧院灯船彻夜，眉楼里一轴兰画换一席酒。十二个女子在这里留下名字：李十娘、顾媚、董白、卞赛、葛嫩、王月、寇湄、李大娘、顿文、李媚、马娇、范珏。甲申国变，乙酉降城，灯船散了，眉楼封了——有人从良，有人出家，有人随夫入闽死在城头，有人流落市桥以教曲为生。三十年过去，一个当年在旧院替她们写诗、作檄、记账的读书人余怀，白发坐在苏州的灯下，一页页把名字写回来。书末附录《板桥杂记》原文四卷（序、雅游、丽品、轶事），未经改写，可与正文对读。
  </div>

  <section class="front">
    <h1>扉页</h1>
    <p class="center"><strong>丽 品 金 陵</strong></p>
    <p class="center">长篇历史小说</p>
    <p class="center">江召兵　著</p>
    <p class="verse">灯船照夜，眉楼藏画；</p>
    <p class="verse">兵火来时，各自白头。</p>
    <hr>
    <h2>内容简介</h2>
    <p>崇祯末年，金陵长板桥边，旧院灯船彻夜，眉楼里一轴兰画换一席酒。李十娘在梅轩前洗桐拭竹，顾眉生在迷楼里画兰，董小宛在影梅庵中熬药，卞玉京在虎丘弹琴；葛嫩梳着头许了一生，王月被一顶小轿抬进庐州，寇湄千金赎身匹马而归。这些人，都在这三十年里活过、写过、唱过。</p>
    <p>甲申国变，乙酉降城。灯船散了，眉楼封了。有人从良，有人出家，有人随夫入闽，死在城头；有人流落市桥，以教女娃唱曲为生。一个当年替她们写诗、作檄、记账的读书人，名叫余怀，活到了白头。康熙年间，他坐在苏州的灯下，一页一页把旧册翻开，把名字写回来——这就是《板桥杂记》。</p>
    <p>全书四卷《灯船》《眉楼》《兵火》《白头》，现在线与过去线双线交织：一条是 1690 年代苏州，余怀白发写书；一条是 1638 至 1670 年代，秦淮诸姬与诸名士的命运。楔子开箱，尾声合册，书末附《板桥杂记》原文四卷，供对读。</p>
    <h2>关于这本书</h2>
    <ul>
      <li><b>体量</b>：楔子＋四卷三十二章＋尾声，正文 __BODYCHARS__ 汉字（约 __BODYWAN__ 万字）；另附《板桥杂记》原文四卷（约 1.1 万字）。</li>
      <li><b>底本</b>：以清·三山余怀《板桥杂记》为骨——丽品三十五段立十二主传，雅游写旧院风物，轶事收诸姬余闻；原文不改写，全本附于书末。</li>
      <li><b>写法</b>：明清白话章回体，说书人程式齐备（话说、看官、正是、且听下回分解）；回目对仗，每回至少两处原文落点，直译、化用、点引并用。</li>
      <li><b>原句嵌入</b>：全书分散嵌入《板桥杂记》原句 66 处（楔子 2、卷一 16、卷二 16、卷三 16、卷四 15、尾声 1），以说书人引述、册页批注、人物口述、题壁画款、旧闻转述五种载体落地，与白话叙事咬合。</li>
      <li><b>读法</b>：可顺序通读，亦可按主传跳读（目录按卷分列）；卷四双线交替，现在线与过去线互为回声。</li>
    </ul>
    <h2>作者简介</h2>
    <p>江召兵，1979年3月生，湖南郴州永兴人，博士，教授，南京欧帕提亚信息科技有限公司创始人、董事长，兼任西北工业大学、南京航空航天大学、西安交通大学外聘导师。1998年至2008年就读于中国人民解放军理工大学，先后获应用气象学学士、流体力学硕士、桥梁与隧道工程博士学位；其后在上海交通大学从事博士后研究，并赴英国南安普顿大学访学。2017年自主择业，先后创办南京欧帕提亚信息科技有限公司、湖南云数仿真信息技术有限公司和南京驭风数智科技有限公司等。</p>
    <p>长期从事人工智能、流固耦合仿真、船舶与海洋工程及军事装备技术研究，主持国家自然科学基金面上项目等国家级项目 4 项、江苏省基金项目 1 项、科研院所外协项目 20 余项；参与南沙岛礁建设、大榭岛浮桥建设、舟山连岛大桥防撞系统等重大工程。出版专著《浮体和浮式多体系统流固耦合动力分析》《浮基多体系统水上展开的稳定性计算与试验》，发表论文 60 余篇；另著有《不确定年代的生存经济学》《史上最美数学图形》《运气工程学》，长篇小说《未央》《人形》《欧冶冲》《玫瑰山庄》，与这部据《板桥杂记》演义的长篇历史小说《丽品金陵》。</p>
  </section>

  <h2 class="section-h" id="toc">目录</h2>
__TOC__

__ARTS__

  <footer class="reader-foot">
    <p>《丽品金陵》· 江召兵 著 · 2026 年 · 全稿在线发布（楔子＋四卷三十二章＋尾声，附《板桥杂记》原文四卷，共约 __WAN__ 万字）。</p>
    <p>附录原文据清·余怀《板桥杂记》，仅分段标点，未作删改；本站内容仅供个人阅读与学习交流，如需转载或引用，请注明出处。</p>
  </footer>
</main>
  <script src="/assets/js/site-counter.js?v=3" defer></script>
</body>
</html>
"""
    html = (html
            .replace("__TOC__", toc_html)
            .replace("__ARTS__", arts_html)
            .replace("__BODYCHARS__", format(body_chars, ","))
            .replace("__BODYWAN__", body_wan)
            .replace("__APCHARS__", format(ap_chars, ","))
            .replace("__WAN__", wan))

    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, "index.html")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(html)
    if os.path.exists(COVER_SRC):
        shutil.copyfile(COVER_SRC, os.path.join(OUT_DIR, "cover.jpg"))
    print("sections=%d items=%d body_chars=%d ap_chars=%d total=%d" % (len(sections), len(flat), body_chars, ap_chars, main_chars))
    print("html bytes=%d -> %s" % (len(html.encode("utf-8")), out))


if __name__ == "__main__":
    build()





