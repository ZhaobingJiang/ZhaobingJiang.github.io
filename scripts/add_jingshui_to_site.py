# -*- coding: utf-8 -*-
"""Append 《井水照人》 as book-19 to both book lists and update site counts."""
from pathlib import Path

ROOT = Path(r"D:\deepseek-harness\OpatiyaAgent\JiangZhaobing.github.io")

ZH_CARD = '''        <article class="book-card" id="book-19">
          <figure class="book-figure">
            <img src="../books/jingshui-zhaoren/cover-card.jpg?v=1" alt="《井水照人》封面" width="640" height="960">
            <figcaption>全书完成 · 楔子 + 三卷四十章</figcaption>
          </figure>
          <div class="book-body">
            <div class="book-head">
              <span class="book-no">19</span>
              <span class="book-tag">全书完成 · 长篇小说</span>
            </div>
            <h3 class="book-title">《井水照人》</h3>
            <p class="book-meta">江召兵 著 · 长篇小说 · 1986—2026 · 陵水 · 云州 · 淮东 · 楔子 + 三卷四十章 · 约二十五万字 · 全书完成（40/40 章）</p>
            <div class="book-links">
              <a class="bk-btn" href="../books/jingshui-zhaoren/read.html">网页版 · 在线阅读全文</a>
            </div>
            <div class="book-intro">
              <p>一九九三年夏天，程家圩旱了四十天。七岁的程见山掉进村口的老井，母亲把井绳放下去，他没抓住；货郎用一根扁担把他钩了上来。母亲打了他一耳光，又把他搂在怀里，说：井水照人，照见的是各人的心。</p>
              <p>这句话他记了一辈子。此后三十多年，他用分数、军装、婚姻和一间车间，一遍遍证明自己配得上：乡统考第一，县中第三名，二〇〇四年高考六百八十三分，全省第九百一十二名。成绩单被他撕了扔进灶膛，母亲从火里抢出来，一片片拼好，藏进樟木箱二十二年。</p>
              <p>他娶过云州城里的姑娘，婚礼三十桌，程家两桌；洞房夜他不行，房产证上没有他的名字，她宫外孕手术时他还在演习。离婚后他净身出户，只带走一箱书。再婚后有了一对龙凤胎。二〇二一年转业，二〇二三年辞职创业，做五轴联动数控机床。二〇二四年冬天，第一台机器试切成功，退休老总工蹲在车间门口哭了。</p>
              <p>二〇二六年春天，母亲脑溢血走了。他回到程家圩，打开那只樟木箱：焦了边的成绩单上，六百八十三分还在；背面是姐姐代写的“娘说收好”；箱子最底下，是母亲练了半年、歪歪扭扭写下的一个“山”字。</p>
              <p class="closing">他证明了一辈子，最后才发现，有些东西本来就不必证明。</p>
            </div>
          </div>
        </article>
'''

EN_CARD = '''        <article class="book-card" id="book-19">
          <figure class="book-figure">
            <img src="./jingshui-zhaoren/cover-card.jpg?v=1" alt="Cover of Well Water Mirrors (Jingshui Zhaoren)" width="640" height="960">
            <figcaption>Complete &middot; Prologue and three volumes, forty chapters</figcaption>
          </figure>
          <div class="book-body">
            <div class="book-head">
              <span class="book-no">19</span>
              <span class="book-tag">Novel &middot; complete</span>
            </div>
            <h3 class="book-title">Well Water Mirrors (Jingshui Zhaoren): A Novel</h3>
            <p class="book-meta">Zhaobing Jiang &middot; Novel &middot; 1986&ndash;2026 &middot; Lingshui &middot; Yunzhou &middot; Huaidong &middot; Prologue and three volumes, forty chapters &middot; About 250,000 Chinese characters &middot; Complete (40/40 chapters)<br>Chinese title: 《井水照人》 &middot; Subtitle: 井水照人，照见的是各人的心 (<em>Well water mirrors the heart of each who looks into it</em>)</p>
            <div class="book-links">
              <a class="bk-btn" href="./jingshui-zhaoren/read.html">Web edition &middot; read the full text</a>
            </div>
            <div class="book-intro">
              <p>In the summer of 1993 the village of Chengjiawei has gone forty days without rain. Seven-year-old Cheng Jianshan falls into the old well at the head of the village. His mother lowers the rope; he cannot hold on. A peddler hooks him out with a carrying pole.</p>
              <p>She slaps him, then holds him and says: well water mirrors the heart of each who looks into it. He remembers that sentence for the next thirty-three years. First place in the township exam, third in the county, 683 out of 750 in the 2004 college entrance exam. He tears the score sheet up and throws it into the stove; his mother pulls it out of the fire, pieces it together, wraps it in plastic and hides it in a camphor chest for twenty-two years.</p>
              <p>He marries a girl from the city; thirty tables at the wedding, two of them his. On their wedding night he cannot. Her name alone is on the deed. She has an ectopic pregnancy and surgery while he is on exercise; he learns last. Divorced, he leaves with one box of books. He marries again, has twins, leaves the army, and starts a company that builds five-axis CNC machine tools. In the winter of 2024 the first machine passes its test cut, and the retired chief engineer sits down at the workshop door and cries.</p>
              <p>In the spring of 2026 his mother dies of a cerebral haemorrhage. He goes back to Chengjiawei and opens the camphor chest: the scorched score sheet, the line his sister wrote for his mother &mdash; keep it safe &mdash; and, at the bottom, a crooked character his mother practised for half a year.</p>
              <p class="closing">He spent a lifetime proving himself, only to find that some things never needed proving.</p>
            </div>
          </div>
        </article>
'''


def insert_card(text, card):
    start = text.find('<article class="book-card" id="book-18">')
    assert start != -1, "book-18 card not found"
    end = text.find("</article>", start)
    assert end != -1
    end += len("</article>")
    return text[:end] + "\n\n" + card.rstrip("\n") + text[end:]


def add_nav(text, entry):
    marker = '<a href="#book-18">'
    idx = text.find(marker)
    assert idx != -1, "nav book-18 not found"
    line_end = text.find("\n", idx)
    return text[:line_end + 1] + entry + "\n" + text[line_end + 1:]


def patch_zh_intro(text):
    old1 = "以下十八部作品全文公开"
    new1 = "以下十九部作品全文公开"
    old2 = "其中包括已完稿的长篇小说《账本》《耿耿》与《寻找大佬》"
    new2 = "其中包括已完稿的长篇小说《账本》《耿耿》《寻找大佬》与《井水照人》"
    old3 = "以及长篇小说《耿耿》与《寻找大佬》。"
    new3 = "以及长篇小说《耿耿》《寻找大佬》与《井水照人》。"
    for o, n in [(old1, new1), (old2, new2), (old3, new3)]:
        assert o in text, o
        text = text.replace(o, n)
    return text


def patch_en_intro(text):
    old1 = "All eighteen complete works below"
    new1 = "All nineteen complete works below"
    old2 = "and <em>In Search of Patrons</em> (<em>Xunzhao Dalao</em>)."
    new2 = ("<em>In Search of Patrons</em> (<em>Xunzhao Dalao</em>) and "
            "<em>Well Water Mirrors</em> (<em>Jingshui Zhaoren</em>).")
    for o, n in [(old1, new1), (old2, new2)]:
        assert o in text, o
        text = text.replace(o, n)
    return text


def verify(path, total=19):
    text = Path(path).read_text(encoding="utf-8")
    ids = text.count('<article class="book-card" id="book-')
    navs = len(__import__("re").findall(r'<a href="#book-\d+">', text))
    nos = __import__("re").findall(r'<span class="book-no">(\d+)</span>', text)
    assert ids == total, (path, "cards", ids)
    assert navs == total, (path, "nav", navs)
    expected = ["%02d" % i for i in range(1, total + 1)]
    assert expected == [n.strip() for n in nos], (path, "nos", nos)
    print("verified", path, ids, navs)


def main():
    zh = ROOT / "zh/books.html"
    en = ROOT / "books/index.html"
    home = ROOT / "index.html"

    t = zh.read_text(encoding="utf-8")
    assert 'id="book-19"' not in t
    t = insert_card(t, ZH_CARD)
    t = add_nav(t, '      <a href="#book-19">19 井水照人</a>')
    t = patch_zh_intro(t)
    zh.write_text(t, encoding="utf-8")

    t = en.read_text(encoding="utf-8")
    assert 'id="book-19"' not in t
    t = insert_card(t, EN_CARD)
    t = add_nav(t, '      <a href="#book-19">19 Well Water Mirrors</a>')
    t = patch_en_intro(t)
    en.write_text(t, encoding="utf-8")

    t = home.read_text(encoding="utf-8")
    old = "(18 complete works: 2 engineering monographs and 16 literary, classical and popular-science books, all available to read online or download)."
    new = "(19 complete works: 2 engineering monographs and 17 literary, classical and popular-science books, all available to read online or download)."
    assert old in t
    home.write_text(t.replace(old, new), encoding="utf-8")

    verify(str(zh))
    verify(str(en))
    print("home updated")


if __name__ == "__main__":
    main()
