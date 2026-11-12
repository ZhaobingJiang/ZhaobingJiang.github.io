# -*- coding: utf-8 -*-
"""Add 《歌舞团》 (Song and Dance Troupe) to the books listings and home pages.

The scanned 2002 novel by 赖俊熙 is newly published as a web edition under
books/gewutuan/. It becomes item 23 (appended, per the current convention) on
both the Chinese and the English books pages, and is announced on both home
pages.
"""
from pathlib import Path

ROOT = Path(r"D:\deepseek-harness\OpatiyaAgent\JiangZhaobing.github.io")

ZH_CARD = """        <article class="book-card" id="book-23">
          <figure class="book-figure">
            <img src="../books/gewutuan/cover.jpg?v=1" alt="《歌舞团》封面" width="640" height="960">
            <figcaption>2002 &middot; 五卷四十六节 &middot; 正文约二十三万六千字</figcaption>
          </figure>
          <div class="book-body">
            <div class="book-head">
              <span class="book-no">23</span>
              <span class="book-tag">全本整理 &middot; 长篇小说</span>
            </div>
            <h3 class="book-title">《歌舞团》</h3>
            <p class="book-meta">赖俊熙 著 &middot; 长篇小说 &middot; 中国大陆 &middot; 五卷四十六节 &middot; 正文约二十三万六千字 &middot; 德宏民族出版社 2002 年 11 月第 1 版 &middot; 网页版全文</p>
            <div class="book-links">
              <a class="bk-btn" href="../books/gewutuan/">网页版 &middot; 在线阅读全文</a>
            </div>
            <div class="book-intro">
              <p>N 市歌舞剧团团长邱彤将调省音乐学院，团长的位子还没有空出来，团里团外已经有许多人瞄上了。一把手调走，二把手本该顺理成章地顶上去，偏偏第一副团长高建年纪大了、又患糖尿病，第二副团长曹欣刚提起来不久，于是空出来的那半格，成了所有人眼里的机会。</p>
              <p>白玉婉是这个团里的舞蹈演员，人漂亮，心也活。她一边在排练场里争角色，一边在饭桌上、在领导家里为自己找路。文化局长王扶之握着剧目能不能投排、能不能上报调演的签字笔；剧作者白一凡和沈羽帆捧着自己写的本子，在评奖、改稿、换导演的一连串关卡里来回打转。一部戏从讨论会到舞台，要过多少人的手，就要看多少人的脸色。</p>
              <p>全书分五卷四十六节，从“部长儿媳”写到“完美境界”：争位子、抢本子、跑评奖、陪酒局、造舆论、拆台子，台上演的是戏，台下演的是人。</p>
              <p class="closing">一部揭文艺圈老底的浮世绘：台上台下的性与爱、权与色。</p>
            </div>
          </div>
        </article>

"""

EN_CARD = """        <article class="book-card" id="book-23">
          <figure class="book-figure">
            <img src="./gewutuan/cover.jpg?v=1" alt="Cover of Song and Dance Troupe (Gewutuan)" width="640" height="960">
            <figcaption>2002 &middot; Five volumes, forty-six sections &middot; About 236,000 Chinese characters</figcaption>
          </figure>
          <div class="book-body">
            <div class="book-head">
              <span class="book-no">23</span>
              <span class="book-tag">Novel &middot; complete text</span>
            </div>
            <h3 class="book-title">Song and Dance Troupe (Gewutuan): A Novel</h3>
            <p class="book-meta">Lai Junxi &middot; Novel &middot; Mainland China &middot; Five volumes, forty-six sections &middot; About 236,000 Chinese characters &middot; First edition, Dehong Nationalities Publishing House, November 2002 &middot; Web edition, full text<br>Chinese title: 《歌舞团》 &middot; Subtitle: 一部揭文艺圈老底的浮世绘 (<em>A Vanity Fair that Lays Bare the Arts World</em>)</p>
            <div class="book-links">
              <a class="bk-btn" href="./gewutuan/">Web edition &middot; read the full text</a>
            </div>
            <div class="book-intro">
              <p>Qiu Tong, head of the N-City Song and Dance Troupe, is being transferred to the provincial conservatory. His post is not yet empty, and people both inside and outside the troupe have already set their sights on it. When the top man leaves, the second in command should normally move up; but the first deputy, Gao Jian, is old and diabetic, and the second deputy, Cao Xin, was promoted only recently. That half step up becomes the opportunity everyone has been waiting for.</p>
              <p>Bai Yuwan is a dancer in the troupe, pretty and quick-witted. She fights for roles in the rehearsal hall and looks for a way up at dinner tables and in the homes of officials. Wang Fuzhi, head of the culture bureau, holds the pen that decides whether a play can be staged or submitted for a provincial festival; playwrights Bai Yifan and Shen Yufan carry their scripts through a gauntlet of prize juries, rewrites and changes of director. From the first script meeting to opening night, a play passes through many hands, and every hand wants to see its owner's face in it.</p>
              <p>In five volumes and forty-six sections, from “The Minister's Daughter-in-Law” to “Perfect Realm”: fighting for posts, fighting for scripts, chasing awards, drinking at banquets, shaping public opinion, pulling the rug out from under rivals. On stage they perform plays; off stage they perform themselves.</p>
              <p class="closing">A vanity fair that lays bare the arts world: sex and love, power and lust, on stage and off.</p>
            </div>
          </div>
        </article>

"""


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected 1 occurrence, found {count}")
    return text.replace(old, new)


def add_nav(text: str, anchor: str, entry: str) -> str:
    old = anchor + "\n    </nav>"
    return replace_once(text, old, anchor + "\n" + entry + "\n    </nav>", "nav")


def append_card(text: str, card: str) -> str:
    pos = text.rfind("</article>")
    if pos < 0:
        raise SystemExit("card: no </article> found")
    end = pos + len("</article>")
    return text[:end] + "\n\n" + card.rstrip("\n") + text[end:]


# --- zh/books.html ---------------------------------------------------------
p = ROOT / "zh" / "books.html"
t = p.read_text(encoding="utf-8")
t = add_nav(t, '      <a href="#book-22">22 暴富的反噬</a>',
            '      <a href="#book-23">23 歌舞团</a>')
t = replace_once(t, "以下二十二部作品全文公开", "以下二十三部作品全文公开", "zh count")
t = append_card(t, ZH_CARD)
p.write_text(t, encoding="utf-8")
print("zh/books.html ok", len(t))

# --- books/index.html ------------------------------------------------------
p = ROOT / "books" / "index.html"
t = p.read_text(encoding="utf-8")
t = add_nav(t, '      <a href="#book-22">22 The Backlash of Sudden Wealth</a>',
            '      <a href="#book-23">23 Song and Dance Troupe</a>')
t = replace_once(t, "All twenty-two complete works", "All twenty-three complete works", "en count")
t = append_card(t, EN_CARD)
p.write_text(t, encoding="utf-8")
print("books/index.html ok", len(t))

# --- zh/index.html ---------------------------------------------------------
p = ROOT / "zh" / "index.html"
t = p.read_text(encoding="utf-8")
t = replace_once(
    t,
    "（共 22 部：工程专著 2 部、长篇与古典文学等作品 20 部，均可在线阅读或下载）。",
    "（共 23 部：工程专著 2 部、长篇与古典文学等作品 21 部，均可在线阅读或下载）。",
    "zh home count",
)
t = replace_once(
    t,
    "        <li>《企业的辉煌与没落》",
    "        <li>《歌舞团》（赖俊熙 著，长篇小说，2002 年，五卷四十六节，正文约二十三万六千字，据德宏民族出版社 2002 年 11 月第 1 版整理）&mdash;\n"
    "          <a class=\"pub-dl\" href=\"../books/gewutuan/\">[在线阅读]</a></li>\n"
    "        <li>《企业的辉煌与没落》",
    "zh home list",
)
t = replace_once(
    t,
    '        <li><span class="item-date">[2026-11]</span>新书上线：纪实文学《暴富的反噬》',
    '        <li><span class="item-date">[2026-11]</span>长篇整理上线：赖俊熙《歌舞团》（五卷四十六节，约二十三万六千字，据德宏民族出版社 2002 年 11 月第 1 版扫描本整理）&mdash; <a href="../books/gewutuan/">在线阅读</a>。</li>\n'
    '        <li><span class="item-date">[2026-11]</span>新书上线：纪实文学《暴富的反噬》',
    "zh news",
)
p.write_text(t, encoding="utf-8")
print("zh/index.html ok", len(t))

# --- index.html ------------------------------------------------------------
p = ROOT / "index.html"
t = p.read_text(encoding="utf-8")
t = replace_once(
    t,
    "(22 complete works: 2 engineering monographs and 20 literary, classical and popular-science books, all available to read online or download).",
    "(23 complete works: 2 engineering monographs and 21 literary, classical and popular-science books, all available to read online or download).",
    "en home count",
)
t = replace_once(
    t,
    '        <li><em>Well Water Mirrors (Jingshui Zhaoren)</em>',
    '        <li><em>Song and Dance Troupe (Gewutuan)</em> by Lai Junxi (novel, 2002; five volumes and forty-six sections, about 236,000 Chinese characters; web edition from the first Dehong Nationalities Publishing House edition) &mdash;\n'
    '          <a class="pub-dl" href="./books/gewutuan/">[Read online]</a></li>\n'
    '        <li><em>Well Water Mirrors (Jingshui Zhaoren)</em>',
    "en home list",
)
t = replace_once(
    t,
    '<li><span class="item-date">[2026-11]</span> New book online: <em>The Backlash of Sudden Wealth</em>',
    '<li><span class="item-date">[2026-11]</span> Newly digitized: <em>Song and Dance Troupe (Gewutuan)</em> by Lai Junxi (five volumes and forty-six sections, about 236,000 Chinese characters; web edition from the 2002 Dehong Nationalities Publishing House first edition) &mdash; <a href="./books/gewutuan/">read online</a>.</li>\n'
    '        <li><span class="item-date">[2026-11]</span> New book online: <em>The Backlash of Sudden Wealth</em>',
    "en news",
)
p.write_text(t, encoding="utf-8")
print("index.html ok", len(t))
