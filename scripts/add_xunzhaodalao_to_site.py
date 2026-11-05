# -*- coding: utf-8 -*-
"""Add 《寻找大佬》 (In Search of Patrons) to the books index, Chinese books page and home page.

The new novel (completed 2026-11-05) becomes item 03 in both book listings;
old items 03-17 shift to 04-18, preserving the reverse-chronological order
claimed by the page text.
"""
import re
from pathlib import Path

ROOT = Path(r"D:\deepseek-harness\OpatiyaAgent\JiangZhaobing.github.io")

EN_NAV = [
    ("1", "Floating-Base Multi-Body"),
    ("2", "Fluid&ndash;Structure Interaction"),
    ("3", "In Search of Patrons"),
    ("4", "Su Dan"),
    ("5", "Mathematical Figures"),
    ("6", "Engineering of Luck"),
    ("7", "Survival Economics"),
    ("8", "Apricot Blossoms"),
    ("9", "Weiyang"),
    ("10", "Renxing"),
    ("11", "Ouyechong"),
    ("12", "Rose Manor"),
    ("13", "Lipin Jinling"),
    ("14", "Taoli Zhixia"),
    ("15", "Crop Circle"),
    ("16", "The Ledger"),
    ("17", "Yulizi (annotated)"),
    ("18", "Genggeng"),
]

ZH_NAV = [
    ("1", "浮基多体系统"),
    ("2", "浮体流固耦合"),
    ("3", "寻找大佬"),
    ("4", "苏耽跨鹤"),
    ("5", "数学图形"),
    ("6", "运气工程学"),
    ("7", "生存经济学"),
    ("8", "杏花深处秣陵关"),
    ("9", "未央"),
    ("10", "人形"),
    ("11", "欧冶冲"),
    ("12", "玫瑰山庄"),
    ("13", "丽品金陵"),
    ("14", "桃李之下"),
    ("15", "麦田怪圈"),
    ("16", "账本"),
    ("17", "郁离子 注疏"),
    ("18", "耿耿"),
]

EN_CARD = """        <article class="book-card" id="book-3">
          <figure class="book-figure">
            <img src="./xunzhaodalao/cover-card.jpg?v=1" alt="Cover of In Search of Patrons (Xunzhao Dalao)" width="640" height="960">
            <figcaption>Complete &middot; Prologue and five volumes, forty chapters</figcaption>
          </figure>
          <div class="book-body">
            <div class="book-head">
              <span class="book-no">3</span>
              <span class="book-tag">Novel &middot; complete</span>
            </div>
            <h3 class="book-title">In Search of Patrons (Xunzhao Dalao): A Novel</h3>
            <p class="book-meta">Zhaobing Jiang &middot; Novel &middot; 1989&ndash;2026 &middot; Chenjia&rsquo;ao &middot; Hangzhou &middot; Boston &middot; Prologue and five volumes, forty chapters &middot; About 350,000 Chinese characters &middot; Complete (40/40 chapters)<br>Chinese title: 《寻找大佬》 &middot; Subtitle: 一个寒门子弟的三十七年 (<em>A Poor Boy&rsquo;s Thirty-Seven Years</em>)</p>
            <div class="book-links">
              <a class="bk-btn" href="./xunzhaodalao/read.html">Web edition &middot; read the full text</a>
            </div>
            <div class="book-intro">
              <p>On the fifteenth of the first lunar month, 1989, seven-year-old Chen Zhiqiang rides his father&rsquo;s shoulders to watch the village <em>shehuo</em> parade. After the crowd disperses, his father is slapped by a richer villager over the irrigation water. The boy hides behind the door and says nothing.</p>
              <p>That slap stays with him for thirty-seven years. A village teacher gives him a torn <em>Xinhua Dictionary</em>, missing the page for <em>lao</em> &mdash; the word for a big man, someone who can get things done. A village secretary writes six characters on the flyleaf of a notebook: remember kindness, not names. A professor gives him a key to a lab; a general sets a family dinner; an advisor at Stanford tells him he is not short of intelligence but of a problem. One by one he finds the people who can pull him up &mdash; and one by one he turns them into entries.</p>
              <p>County exam, engineering school, a state research institute, Purdue, Stanford, MIT, a start-up in Hangzhou. Every step upward changes the face of his inferiority: the computer he cannot switch on, the toast he cannot make, the accent they laugh at, the paper rejected seven times, the investor who asks &ldquo;why you?&rdquo;</p>
              <p>In September 2026, in a lecture hall at MIT, a doctoral student asks him: &ldquo;How did you find your patrons?&rdquo; Standing on the stage, he sees the boy behind the door in 1989.</p>
              <p class="closing">He was not looking for a patron. He was looking for someone to hit back for his father.</p>
            </div>
          </div>
        </article>

"""

ZH_CARD = """        <article class="book-card" id="book-3">
          <figure class="book-figure">
            <img src="../books/xunzhaodalao/cover-card.jpg?v=1" alt="《寻找大佬》封面" width="640" height="960">
            <figcaption>全书完成 · 楔子 + 五卷四十章</figcaption>
          </figure>
          <div class="book-body">
            <div class="book-head">
              <span class="book-no">3</span>
              <span class="book-tag">全书完成 · 长篇小说</span>
            </div>
            <h3 class="book-title">《寻找大佬》</h3>
            <p class="book-meta">江召兵 著 · 长篇小说 · 1989—2026 · 陈家坳 · 杭州 · 波士顿 · 楔子 + 五卷四十章 · 约三十五万字 · 全书完成（40/40 章）</p>
            <div class="book-links">
              <a class="bk-btn" href="../books/xunzhaodalao/read.html">网页版 · 在线阅读全文</a>
            </div>
            <div class="book-intro">
              <p>一九八九年正月十五，陈家坳。七岁的陈志强骑在父亲肩上看社火。散场后，父亲因渠水的事，被赵德贵扇了一耳光。他躲在门后，没敢出声。</p>
              <p>这一耳光他记了三十七年。村小教师张守义送他一本缺了“佬”字页的旧《新华字典》，村支书何庆丰在灶房里给他一本深蓝硬壳笔记本，扉页写“记恩，不记人”；周启山给他实验室的钥匙，韩振邦摆过一桌家宴，安德森在斯坦福告诉他：你缺的不是聪明，是一个问题。他一路考出去——县状元、汉江理工、东江科技、普渡硕士、斯坦福博士、MIT 博士后，再回国创业。</p>
              <p>可每往上走一步，自卑就换一副面孔：大学报到那天他不会开电脑；工作第一顿饭不会敬酒；到了美国，口语被人笑；进了顶尖实验室，总觉得自己是混进来的；公司融资，投资人问他“凭什么是你”。他把每一个帮过他的人记在本子上，也把每一份人情折算成数字，藏在心里。</p>
              <p>二〇二六年九月，MIT 报告厅。一个博士生问他：“您是怎么找到大佬的？”他站在台上，突然看见一九八九年门后的那个自己。</p>
              <p class="closing">他找的不是靠山，是一个能替他父亲还手的人。</p>
            </div>
          </div>
        </article>

"""


def renumber_cards(text: str) -> str:
    """Shift ids and visible numbers 3..17 to 4..18 (descending to avoid collisions)."""
    for n in range(17, 2, -1):
        text = text.replace(f'id="book-{n}"', f'id="book-{n + 1}"')
        text = text.replace(f'<span class="book-no">{n}</span>', f'<span class="book-no">{n + 1}</span>')
    return text


def rebuild_nav(text: str, aria: str, entries) -> str:
    start_pat = re.compile(
        r'(<nav class="book-toc" aria-label="' + re.escape(aria) + r'">\n)(.*?)(\n    </nav>)',
        re.S,
    )
    m = start_pat.search(text)
    assert m, "nav block not found"
    lines = [f'      <a href="#book-{n}">{n.zfill(2)} {title}</a>' for n, title in entries]
    return text[: m.start(2)] + "\n".join(lines) + text[m.end(2):]


def insert_card(text: str, card: str) -> str:
    m = re.search(r'<article class="book-card" id="book-2">.*?</article>', text, re.S)
    assert m, "book-2 card not found"
    return text[: m.end()] + "\n\n" + card + text[m.end():]


def up_en_index():
    p = ROOT / "books" / "index.html"
    t = p.read_text(encoding="utf-8")
    t = renumber_cards(t)
    t = rebuild_nav(t, "Books", EN_NAV)
    t = insert_card(t, EN_CARD)
    t = t.replace(
        "All seventeen complete works below are published in full",
        "All eighteen complete works below are published in full",
    )
    t = t.replace(
        "including the complete novels <em>The Ledger</em> (<em>Zhangben</em>) and <em>Genggeng</em> (<em>Unforgotten</em>)",
        "including the complete novels <em>The Ledger</em> (<em>Zhangben</em>), <em>Genggeng</em> (<em>Unforgotten</em>) and <em>In Search of Patrons</em> (<em>Xunzhao Dalao</em>)",
    )
    t = t.replace(
        "the suspense novel <em>Crop Circle</em>; and the novel <em>Genggeng</em> (<em>Unforgotten</em>).",
        "the suspense novel <em>Crop Circle</em>; the novel <em>Genggeng</em> (<em>Unforgotten</em>); and the coming-of-age novel <em>In Search of Patrons</em> (<em>Xunzhao Dalao</em>).",
    )
    p.write_text(t, encoding="utf-8")
    print("books/index.html", len(t))


def up_zh_index():
    p = ROOT / "zh" / "books.html"
    t = p.read_text(encoding="utf-8")
    t = renumber_cards(t)
    t = rebuild_nav(t, "作品目录", ZH_NAV)
    t = insert_card(t, ZH_CARD)
    t = t.replace("以下十七部作品全文公开", "以下十八部作品全文公开")
    t = t.replace(
        "其中包括已完稿的长篇小说《账本》与《耿耿》，均可在线阅读全文。",
        "其中包括已完稿的长篇小说《账本》《耿耿》与《寻找大佬》，均可在线阅读全文。",
    )
    t = t.replace(
        "以及长篇小说《耿耿》。",
        "以及长篇小说《耿耿》与《寻找大佬》。",
    )
    p.write_text(t, encoding="utf-8")
    print("zh/books.html", len(t))


def up_home():
    p = ROOT / "index.html"
    t = p.read_text(encoding="utf-8")
    t = t.replace(
        "(17 complete works: 2 engineering monographs and 15 literary, classical and popular-science books, all available to read online or download).",
        "(18 complete works: 2 engineering monographs and 16 literary, classical and popular-science books, all available to read online or download).",
    )
    t = t.replace(
        "and <em>Genggeng (Unforgotten)</em>, a rural novel spanning 1976&ndash;2031. All are available to read",
        "and <em>Genggeng (Unforgotten)</em>, a rural novel spanning 1976&ndash;2031, and <em>In Search of Patrons (Xunzhao Dalao)</em>, a novel of a poor boy&rsquo;s thirty-seven years. All are available to read",
    )
    new_item = (
        '        <li><em>In Search of Patrons (Xunzhao Dalao)</em> (novel, complete, 1989&ndash;2026, '
        "from a village in the Loess Plateau to MIT; prologue and five volumes, forty chapters, "
        'about 350,000 Chinese characters) —\n'
        '          <a class="pub-dl" href="./books/xunzhaodalao/read.html">[Read online]</a></li>\n'
    )
    anchor = '      <ul class="item-list">\n        <li><em>Genggeng (Unforgotten)</em>'
    assert anchor in t
    t = t.replace(anchor, '      <ul class="item-list">\n' + new_item + '        <li><em>Genggeng (Unforgotten)</em>')
    p.write_text(t, encoding="utf-8")
    print("index.html", len(t))


def verify():
    for name, path in (("books/index.html", ROOT / "books" / "index.html"), ("zh/books.html", ROOT / "zh" / "books.html")):
        t = path.read_text(encoding="utf-8")
        ids = re.findall(r'id="book-(\d+)"', t)
        navs = re.findall(r'href="#book-(\d+)"', t)
        nos = re.findall(r'<span class="book-no">(\d+)</span>', t)
        print(name, "ids", ids, "nav", navs, "nos", nos)
        assert ids == [str(i) for i in range(1, 19)], ids
        assert navs == [str(i) for i in range(1, 19)], navs
        assert nos == [str(i) for i in range(1, 19)], nos


if __name__ == "__main__":
    up_en_index()
    up_zh_index()
    up_home()
    verify()
    print("OK")
