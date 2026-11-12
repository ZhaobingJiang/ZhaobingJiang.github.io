# -*- coding: utf-8 -*-
"""Add 《明清艳情词曲全编》 to the books listings and home pages.

The scanned 1995 anthology (Guangzhou Publishing House) is published as a
four-page web edition under books/mingqing-yanqing-ciqu/. It becomes item 24
(appended, per the current convention) on both the Chinese and the English
books pages, and is announced on both home pages.
"""
from pathlib import Path

ROOT = Path(r"D:\deepseek-harness\OpatiyaAgent\JiangZhaobing.github.io")

ZH_CARD = """        <article class="book-card" id="book-24">
          <figure class="book-figure">
            <img src="../books/mingqing-yanqing-ciqu/cover.jpg?v=1" alt="《明清艳情词曲全编》封面" width="640" height="960">
            <figcaption>1995 &middot; 上中下三卷 &middot; 一千二百二十篇 &middot; 约七十九万字</figcaption>
          </figure>
          <div class="book-body">
            <div class="book-head">
              <span class="book-no">24</span>
              <span class="book-tag">全本整理 &middot; 古典词曲</span>
            </div>
            <h3 class="book-title">《明清艳情词曲全编》</h3>
            <p class="book-meta">〔明〕冯梦龙 〔清〕华广生 原著 &middot; 花子金 编著 &middot; 古典词曲 &middot; 中国 &middot; 明代—清代 &middot; 上中下三卷 &middot; 一千二百二十篇 &middot; 约七十九万字 &middot; 广州出版社 1995 年 7 月第 1 版 &middot; 网页版全文</p>
            <div class="book-links">
              <a class="bk-btn" href="../books/mingqing-yanqing-ciqu/">网页版 &middot; 在线阅读全文</a>
            </div>
            <div class="book-intro">
              <p>明代时调小曲与清代曲词，从冯梦龙所辑《挂枝儿》《山歌》，到华广生所辑曲词，再到明清杂剧传奇中析出的曲白片段，凡写男女情爱、风月场中悲欢者，多在其中。原书由花子金编选，1995 年由广州出版社出版，上中下三卷，共一千二百二十篇；据书末后记，底本采自上海古籍出版社《冯梦龙全集》《明清民歌时调集》。</p>
              <p>每篇先列曲文，或附冯梦龙批语；其后依次为「现代语译」「注释」「评析」：译语把方言、隐语、双关一一说破，注释考订名物与俗语，评析把一首小曲放回它的时代与情境里，指出它写得好在哪里、俗在哪里、真在哪里。</p>
              <p>这些曲子唱偷情、相思、负心、吃醋、劝嫁、骂媒，也唱市井生计与世态炎凉。它们不是文人案头的雅词，而是明清两代人说过、唱过的情话与怨语；今天读来，仍能听见那点活气。</p>
              <p class="closing">一部明清民间情歌的总集：艳而不讳，俗而见真。</p>
            </div>
          </div>
        </article>

"""

EN_CARD = """        <article class="book-card" id="book-24">
          <figure class="book-figure">
            <img src="./mingqing-yanqing-ciqu/cover.jpg?v=1" alt="Cover of Amorous Ci and Qu of the Ming and Qing" width="640" height="960">
            <figcaption>1995 &middot; Three volumes &middot; 1,220 pieces &middot; About 790,000 Chinese characters</figcaption>
          </figure>
          <div class="book-body">
            <div class="book-head">
              <span class="book-no">24</span>
              <span class="book-tag">Classical anthology &middot; complete text</span>
            </div>
            <h3 class="book-title">Amorous Ci and Qu of the Ming and Qing (Mingqing Yanqing Ciqu Quanbian)</h3>
            <p class="book-meta">Feng Menglong (Ming) and Hua Guangsheng (Qing) &middot; compiled by Hua Zijin &middot; Classical ci and qu &middot; China &middot; Ming&ndash;Qing dynasties &middot; Three volumes &middot; 1,220 pieces &middot; About 790,000 Chinese characters &middot; First edition, Guangzhou Publishing House, July 1995 &middot; Web edition, full text<br>Chinese title: 《明清艳情词曲全编》 &middot; Subtitle: 白话注释 &middot; 现代赏析 (<em>Vernacular Notes and Modern Appreciation</em>)</p>
            <div class="book-links">
              <a class="bk-btn" href="./mingqing-yanqing-ciqu/">Web edition &middot; read the full text</a>
            </div>
            <div class="book-intro">
              <p>Ming and Qing popular songs, from the collections of Feng Menglong to those of Hua Guangsheng, together with songs and dialogue extracted from Ming&ndash;Qing drama. Compiled by Hua Zijin and published by Guangzhou Publishing House in 1995 in three volumes, the anthology holds 1,220 pieces; according to its afterword, the texts were selected from the Shanghai Classics Publishing House editions of the <em>Complete Works of Feng Menglong</em> and <em>Ming and Qing Folk Songs and Popular Tunes</em>.</p>
              <p>Each piece gives the song first, sometimes with Feng Menglong&rsquo;s marginal note, then a modern Chinese translation, notes and an appreciation: the translation unpacks dialect, slang and double meanings; the notes gloss objects and idioms; the appreciation restores the song to its time and setting.</p>
              <p>These songs sing of stolen love, longing, betrayal, jealousy, forced marriage and matchmakers&rsquo; greed, and of the hard business of everyday life. They are not scholar&rsquo;s verse but the endearments and complaints of ordinary people in the Ming and Qing; read today, their vitality still comes through.</p>
              <p class="closing">A Ming&ndash;Qing folk songbook: frank about desire, true to the vernacular.</p>
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
t = add_nav(t, '      <a href="#book-23">23 歌舞团</a>',
            '      <a href="#book-24">24 艳情词曲全编</a>')
t = replace_once(t, "以下二十三部作品全文公开", "以下二十四部作品全文公开", "zh count")
t = replace_once(
    t,
    "此外，本页收录赖俊熙 2002 年长篇小说《歌舞团》的整理本，据德宏民族出版社 2002 年 11 月第 1 版扫描本排校。",
    "此外，本页收录赖俊熙 2002 年长篇小说《歌舞团》的整理本，据德宏民族出版社 2002 年 11 月第 1 版扫描本排校；"
    "并收录花子金编选《明清艳情词曲全编》的整理本，据广州出版社 1995 年 7 月第 1 版扫描本排校。",
    "zh intro",
)
t = append_card(t, ZH_CARD)
p.write_text(t, encoding="utf-8")
print("zh/books.html ok", len(t))

# --- books/index.html ------------------------------------------------------
p = ROOT / "books" / "index.html"
t = p.read_text(encoding="utf-8")
t = add_nav(t, '      <a href="#book-23">23 Song and Dance Troupe</a>',
            '      <a href="#book-24">24 Ming&ndash;Qing Ci and Qu</a>')
t = replace_once(t, "All twenty-three complete works", "All twenty-four complete works", "en count")
t = replace_once(
    t,
    "This page also carries a newly digitized web edition of Lai Junxi&rsquo;s 2002 novel <em>Song and Dance Troupe</em> (<em>Gewutuan</em>), set from the first Dehong Nationalities Publishing House edition.",
    "This page also carries a newly digitized web edition of Lai Junxi&rsquo;s 2002 novel <em>Song and Dance Troupe</em> (<em>Gewutuan</em>), set from the first Dehong Nationalities Publishing House edition, "
    "as well as <em>Amorous Ci and Qu of the Ming and Qing</em> (<em>Mingqing Yanqing Ciqu Quanbian</em>), compiled by Hua Zijin and set from the first Guangzhou Publishing House edition of 1995.",
    "en intro",
)
t = append_card(t, EN_CARD)
p.write_text(t, encoding="utf-8")
print("books/index.html ok", len(t))

# --- zh/index.html ---------------------------------------------------------
p = ROOT / "zh" / "index.html"
t = p.read_text(encoding="utf-8")
t = replace_once(
    t,
    "（共 23 部：工程专著 2 部、长篇与古典文学等作品 21 部，均可在线阅读或下载）。",
    "（共 24 部：工程专著 2 部、长篇与古典文学等作品 22 部，均可在线阅读或下载）。",
    "zh home count",
)
t = replace_once(
    t,
    "        <li>《企业的辉煌与没落》",
    "        <li>《明清艳情词曲全编》（〔明〕冯梦龙 〔清〕华广生 原著，花子金 编著，古典词曲，1995 年，上中下三卷，一千二百二十篇，约七十九万字，据广州出版社 1995 年 7 月第 1 版整理）&mdash;\n"
    "          <a class=\"pub-dl\" href=\"../books/mingqing-yanqing-ciqu/\">[在线阅读]</a></li>\n"
    "        <li>《企业的辉煌与没落》",
    "zh home list",
)
t = replace_once(
    t,
    '        <li><span class="item-date">[2026-11]</span>长篇整理上线：赖俊熙《歌舞团》',
    '        <li><span class="item-date">[2026-11]</span>古典词曲整理上线：花子金编选《明清艳情词曲全编》（上中下三卷，一千二百二十篇，约七十九万字，据广州出版社 1995 年 7 月第 1 版扫描本整理）&mdash; <a href="../books/mingqing-yanqing-ciqu/">在线阅读</a>。</li>\n'
    '        <li><span class="item-date">[2026-11]</span>长篇整理上线：赖俊熙《歌舞团》',
    "zh news",
)
p.write_text(t, encoding="utf-8")
print("zh/index.html ok", len(t))

# --- index.html ------------------------------------------------------------
p = ROOT / "index.html"
t = p.read_text(encoding="utf-8")
t = replace_once(
    t,
    "(23 complete works: 2 engineering monographs and 21 literary, classical and popular-science books, all available to read online or download).",
    "(24 complete works: 2 engineering monographs and 22 literary, classical and popular-science books, all available to read online or download).",
    "en home count",
)
t = replace_once(
    t,
    '        <li><em>Well Water Mirrors (Jingshui Zhaoren)</em>',
    '        <li><em>Amorous Ci and Qu of the Ming and Qing (Mingqing Yanqing Ciqu Quanbian)</em>, compiled by Hua Zijin from Feng Menglong and Hua Guangsheng (classical ci and qu, 1995; three volumes, 1,220 pieces, about 790,000 Chinese characters; web edition from the first Guangzhou Publishing House edition) &mdash;\n'
    '          <a class="pub-dl" href="./books/mingqing-yanqing-ciqu/">[Read online]</a></li>\n'
    '        <li><em>Well Water Mirrors (Jingshui Zhaoren)</em>',
    "en home list",
)
t = replace_once(
    t,
    '<li><span class="item-date">[2026-11]</span> Newly digitized: <em>Song and Dance Troupe (Gewutuan)</em>',
    '<li><span class="item-date">[2026-11]</span> Newly digitized: <em>Amorous Ci and Qu of the Ming and Qing</em> (<em>Mingqing Yanqing Ciqu Quanbian</em>), compiled by Hua Zijin from Feng Menglong and Hua Guangsheng (three volumes, 1,220 pieces, about 790,000 Chinese characters; web edition from the 1995 Guangzhou Publishing House first edition) &mdash; <a href="./books/mingqing-yanqing-ciqu/">read online</a>.</li>\n'
    '        <li><span class="item-date">[2026-11]</span> Newly digitized: <em>Song and Dance Troupe (Gewutuan)</em>',
    "en news",
)
p.write_text(t, encoding="utf-8")
print("index.html ok", len(t))
