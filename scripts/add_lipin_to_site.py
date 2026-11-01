# -*- coding: utf-8 -*-
"""在个人主页加入《丽品金陵》：books 索引、中文书目页、首页与中文首页书目列表。"""
import io
import os

SITE = r"D:\deepseek-harness\OpatiyaAgent\JiangZhaobing.github.io"


def read(p):
    return io.open(os.path.join(SITE, p), encoding="utf-8").read()


def write(p, t):
    io.open(os.path.join(SITE, p), "w", encoding="utf-8", newline="\n").write(t)


def rep(t, old, new, count=1):
    n = t.count(old)
    assert n == count, "replace count %d != %d for %r" % (n, count, old[:60])
    return t.replace(old, new)


def insert_after_book11(t, card):
    anchor = '<article class="book-card" id="book-11">'
    i = t.index(anchor)
    j = t.index("</article>", i) + len("</article>")
    return t[:j] + "\n" + card + t[j:]


CARD_EN = """
        <article class="book-card" id="book-12">
          <figure class="book-figure">
            <img src="./lipin-jinling/cover.jpg?v=1" alt="Cover of Lipin Jinling" width="640" height="960">
            <figcaption>2026 &middot; Prologue, four volumes, thirty-two chapters, epilogue, with the source text</figcaption>
          </figure>
          <div class="book-body">
            <div class="book-head">
              <span class="book-no">12</span>
              <span class="book-tag">Historical novel</span>
            </div>
            <h3 class="book-title">Lipin Jinling (Beauties of Jinling): A Historical Novel</h3>
            <p class="book-meta">Zhaobing Jiang &middot; Historical novel &middot; 2026 &middot; Prologue, four volumes and thirty-two chapters, plus an epilogue &middot; About 231,000 Chinese characters &middot; Complete online<br>Chinese title: 《丽品金陵》 &middot; Subtitle: 秦淮旧院 · 十二钗传 &middot; Based on Yu Huai's <em>Banqiao Zaji</em> (c. 1690s), whose full text is appended</p>
            <div class="book-links">
              <a class="bk-btn" href="./lipin-jinling/">Web edition &middot; read the complete book online</a>
            </div>
            <div class="book-intro">
              <p>In the last years of the Ming the lantern boats on the Qinhuai never went dark. Twelve women left their names in the old quarter: Li Shiniang, Gu Mei, Dong Bai, Bian Sai, Ge Nen, Wang Yue, Kou Mei, Li Daniang, Dun Wen, Li Mei, Ma Jiao and Fan Jue. They wrote verses on tavern walls, painted orchids for a jug of wine, sang roles on the stage, and chose — some of them — how they would die.</p>
              <p>Then came 1644 and the fall of Nanjing. The lantern boats scattered, the painted towers were sealed: one married a merchant, one became a nun, one followed her husband into Fujian and died on the city wall, one ended up teaching songs to village girls by a market bridge. Thirty years later, in Suzhou, an old scholar who once wrote their verses, their manifestos and their accounts sits down under a lamp and writes their names back — this is Yu Huai's <em>Banqiao Zaji</em>, and this novel grows out of it.</p>
              <p>Four volumes — Lantern Boats, the Painted Tower, Fire and War, White Hair — interweave two timelines: 1690s Suzhou, where Yu Huai writes; and 1638–1670s, where the women and their scholars live and die. The prologue opens the box, the epilogue closes the album, and the full text of <em>Banqiao Zaji</em> is appended for comparison.</p>
              <p class="closing">Lanterns lit the night; the war took the rest.</p>
            </div>
          </div>
        </article>
"""

CARD_ZH = """
        <article class="book-card" id="book-12">
          <figure class="book-figure">
            <img src="../books/lipin-jinling/cover.jpg?v=1" alt="《丽品金陵》封面" width="640" height="960">
            <figcaption>2026 · 楔子＋四卷三十二章＋尾声（附原文）</figcaption>
          </figure>
          <div class="book-body">
            <div class="book-head">
              <span class="book-no">12</span>
              <span class="book-tag">长篇历史小说</span>
            </div>
            <h3 class="book-title">《丽品金陵》</h3>
            <p class="book-meta">江召兵 著 · 长篇历史小说 · 2026年 · 楔子＋四卷三十二章＋尾声 · 正文约二十三万一千字，另附《板桥杂记》原文四卷 · 已全部上线</p>
            <div class="book-links">
              <a class="bk-btn" href="../books/lipin-jinling/">网页版 · 在线阅读全文</a>
            </div>
            <div class="book-intro">
              <p>崇祯末年，金陵长板桥边，旧院灯船彻夜，眉楼里一轴兰画换一席酒。十二个女子在这里留下名字：李十娘、顾媚、董白、卞赛、葛嫩、王月、寇湄、李大娘、顿文、李媚、马娇、范珏。</p>
              <p>甲申国变，乙酉降城。灯船散了，眉楼封了。有人从良，有人出家，有人随夫入闽，死在城头；有人流落市桥，以教女娃唱曲为生。一个当年替她们写诗、作檄、记账的读书人余怀，活到了白头，在苏州的灯下把名字一页页写回来——这就是《板桥杂记》。</p>
              <p>四卷《灯船》《眉楼》《兵火》《白头》，现在线与过去线双线交织；楔子开箱，尾声合册，书末附《板桥杂记》原文四卷（序、雅游、丽品、轶事），未经改写，供对读。</p>
              <p class="closing">灯船照夜，眉楼藏画；兵火来时，各自白头。</p>
            </div>
          </div>
        </article>
"""

# ---------------- books/index.html ----------------
p = "books/index.html"
t = read(p)
t = rep(t, "All eleven works below are published in full", "All twelve works below are published in full")
t = rep(t,
        "and an adapted novel, <em>Rose Manor</em> (after Hai Cheng: prologue, nineteen chapters and an epilogue). All are free to read online in full.",
        "an adapted novel, <em>Rose Manor</em> (after Hai Cheng: prologue, nineteen chapters and an epilogue); and the latest, <em>Lipin Jinling</em>, a historical novel drawn from Yu Huai's <em>Banqiao Zaji</em> (prologue, four volumes and thirty-two chapters, an epilogue, with the full source text appended). All are free to read online in full.")
t = rep(t, '<a href="#book-11">11 Rose Manor</a>',
        '<a href="#book-11">11 Rose Manor</a>\n      <a href="#book-12">12 Lipin Jinling</a>')
t = insert_after_book11(t, CARD_EN)
write(p, t)
print("OK", p)

# ---------------- zh/books.html ----------------
p = "zh/books.html"
t = read(p)
t = rep(t, "以下十一部作品全文公开", "以下十二部作品全文公开")
t = rep(t,
        "与长篇改编小说《玫瑰山庄》（据海诚同名小说改编，楔子＋十九章＋尾声）。</p>",
        "与长篇改编小说《玫瑰山庄》（据海诚同名小说改编，楔子＋十九章＋尾声），以及据清·余怀《板桥杂记》敷演的长篇历史小说《丽品金陵》（楔子＋四卷三十二章＋尾声，附原文四卷）。</p>")
t = rep(t, '<a href="#book-11">11 玫瑰山庄</a>',
        '<a href="#book-11">11 玫瑰山庄</a>\n      <a href="#book-12">12 丽品金陵</a>')
t = insert_after_book11(t, CARD_ZH)
write(p, t)
print("OK", p)

# ---------------- index.html ----------------
p = "index.html"
t = read(p)
t = rep(t, "completed eight long-form and", "completed nine long-form and")
t = rep(t,
        "and <em>Ouyechong</em>, a rural novel. All are available to read",
        "and <em>Ouyechong</em>, a rural novel, and <em>Lipin Jinling</em>, a historical novel after Yu Huai's <em>Banqiao Zaji</em>. All are available to read")
t = rep(t,
        "(11 works in total: 2 engineering monographs and 9 long-form and popular-science books, all available to read online or download)",
        "(12 works in total: 2 engineering monographs and 10 long-form and popular-science books, all available to read online or download)")
t = rep(t,
        '<li><em>Rose Manor</em> (adapted novel, 2026, after Hai Cheng: prologue, nineteen chapters and an epilogue) — <a class="pub-dl" href="./books/meigui-shanzhuang/">[Read online]</a></li>',
        '<li><em>Rose Manor</em> (adapted novel, 2026, after Hai Cheng: prologue, nineteen chapters and an epilogue) — <a class="pub-dl" href="./books/meigui-shanzhuang/">[Read online]</a></li>\n        <li><em>Lipin Jinling</em> (historical novel, 2026, after Yu Huai\'s <em>Banqiao Zaji</em>: prologue, four volumes of thirty-two chapters and an epilogue, with the source text) — <a class="pub-dl" href="./books/lipin-jinling/">[Read online]</a></li>')
write(p, t)
print("OK", p)

# ---------------- zh/index.html ----------------
p = "zh/index.html"
t = read(p)
t = rep(t,
        "《未央》《人形》《欧冶冲》\n        《史上最美数学图形》",
        "《未央》《人形》《欧冶冲》《丽品金陵》\n        《史上最美数学图形》")
t = rep(t, "等长篇与科普作品八部", "等长篇与科普作品九部")
t = rep(t,
        "（共 10 部：工程专著 2 部、长篇与科普作品 8 部，均可在线阅读或下载）",
        "（共 11 部：工程专著 2 部、长篇与科普作品 9 部，均可在线阅读或下载）")
t = rep(t,
        '<li>《欧冶冲》（长篇乡土小说，2026年，楔子＋四卷六十四章，约二十四万字）—\n          <a class="pub-dl" href="../books/ouyechong/">[在线阅读]</a></li>',
        '<li>《欧冶冲》（长篇乡土小说，2026年，楔子＋四卷六十四章，约二十四万字）—\n          <a class="pub-dl" href="../books/ouyechong/">[在线阅读]</a></li>\n        <li>《丽品金陵》（长篇历史小说，据清·余怀《板桥杂记》敷演，2026年，楔子＋四卷三十二章＋尾声，附原文四卷，正文约二十三万一千字）—\n          <a class="pub-dl" href="../books/lipin-jinling/">[在线阅读]</a></li>')
write(p, t)
print("OK", p)
