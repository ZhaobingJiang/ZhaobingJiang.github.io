# 生成脚本：books/math-figures/

把《史上最美数学图形：科学与艺术的结合》的出版稿
`books/most_beautiful_math_figures_science_and_art.docx` 生成网页版
`books/math-figures/`，与另外两本专著共用 `tools/web-edition/` 的版式与交互。

## 重新生成

```sh
cd tools/math-figures
python 01_extract_docx.py      # DOCX -> docx_items.json（保留行内公式、加粗、插图位置）
python 03_extract_images.py    # 抽出 149 幅图形：封面、7 幅篇首、50 幅章首、91 幅节内插图
python 02_parse_book.py        # -> book_model.json
python 04_build_site.py        # -> books/math-figures/index.html
python 06_fidelity_check.py    # 逐段核对：书稿每一段、每个表格单元格都在网页里
```

## 这本书的结构

标题层是 `Heading 1`（序章 + 七篇 + 五十章 + 尾声 + 附录，共 60 条），
每一章下面固定六节 `Heading 2`：引子之问、图形导览、数学原理、设计应用、数学家故事、点评。
**一节课一张卡片**，共 307 张；六个反复出现的节名正好成为页面的「这一节给你什么」筛选维度——
选「设计应用」就是一次看完五十个图形在真实设计里的用法，选「数学家故事」就是一部人物小传。

- 书籍目录（`toc 1` 样式，60 行，含原书页码）收进页脚的折叠块，不丢内容也不与侧栏重复。
- 篇首横幅带该篇的题记与导语；章首图形由标题渲染，正文里不再重复同一张。
- 图片命名跟随书里的位置：`fig-cover` / `fig-part N` / `fig-ch NN` / `fig-<章>-<n>`。
- 这本书的出版稿没有编辑残留，`06_fidelity_check.py` 的排除列表为空，正文全部收录。

## 核对

```sh
python -m http.server 8099 --bind 127.0.0.1     # 在仓库根目录另开一个终端
python 05_verify_page.py       # 52 项：结构、图形、公式、六个节名筛选、检索、深链、移动端、字阶
```
