# 生成脚本：books/luck-engineering/

把《运气工程学》的出版稿 `books/luck_engineering.docx` 生成网页版
`books/luck-engineering/`，版式与《不确定年代的生存经济学》网页版共用一套
（`tools/web-edition/`）。

## 重新生成

```sh
cd tools/luck-engineering
python 01_extract_docx.py      # DOCX -> docx_items.json（保留行内公式、加粗、插图位置）
python 03_extract_images.py    # 抽出 47 幅插图，按书里的图号命名（图 10-2 -> fig-10-2.jpg）
python 02_parse_book.py        # -> book_model.json（篇/章/节/章尾/附录 的结构化全文）
python 04_build_site.py        # -> books/luck-engineering/index.html
python 06_fidelity_check.py    # 逐段核对：书稿每一段、每个表格单元格都在网页里
```

`04_build_site.py` 会把 `tools/web-edition/` 的 `style.css` 与 `app.js` 复制到本书目录，
页面保持自包含，两个书页共用同一份版式源。

## 核对

```sh
python -m http.server 8099 --bind 127.0.0.1     # 在仓库根目录另开一个终端
python 05_verify_page.py       # 54 项：结构、公式、插图、表格、筛选、检索、深链、移动端、字阶
```

## 这本书特有的处理

- **行内公式**：书稿里 580 处公式是 OMML 对象，`paragraph.text` 读不到它们，
  所以 `01` 自己遍历段落子节点，把公式留在原位；另有 117 段把 LaTeX（`$\lambda_0$`）
  当普通文字留着，渲染器一并用下标/分式排出来。两处分数排成上下叠放。
- **加粗**：2492 个加粗 run（1709 段含加粗）在纯文本提取里会丢失，`01` 按 run 记录。
- **篇与章的归属**：出版文件把四个篇首页排在一起、后面才接十七章，位置判断会把所有章
  都算进最后一篇；归属取自每篇自己写的「本篇包含：- 第N章…」。第1章按书稿标注是导论，不入篇。
- **排版残留**：出版文件里有「篇首页（四篇导语）」「排版说明：本文件为四个篇首页的内容底稿」
  「导论（第1章，不入篇）」四处编辑痕迹（PDF 第 8、9 页也有），网页版不收录，
  `06_fidelity_check.py` 里列明为唯一的有意排除项，其余全部逐字保留。
- **正文里的〔待核…〕**：51 处作者自查标记属于出版内容，原样保留。

## 中间产物

`docx_items.json`、`book_model.json`、`images.json`、`shots/` 已在 `.gitignore` 中忽略。
