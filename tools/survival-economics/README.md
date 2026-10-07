# 生成脚本：books/survival-economics/

把书稿 `books/survival_economics_uncertain_times_v3_illustrated.docx` 生成网页版
`books/survival-economics/`（版式参照 [HowToLiveBetter](https://eternity4719.github.io/HowToLiveBetter/)）。

网页本身是纯静态的：`index.html` 已经包含全书正文，`app.js` 只负责筛选、检索与主题切换，
不生成任何正文；因此关掉 JavaScript 也读得到全文，搜索引擎也能直接抓取。

## 重新生成

书稿改动后，在仓库根目录下依次运行（Python 3.10+，需要 `python-docx`）：

```sh
cd tools/survival-economics
python 01_extract_docx.py      # DOCX -> docx_items.json（逐段录音，含图片位置）
python 02_parse_book.py        # -> book_model.json（篇/章/节/行动清单/附录 的结构化全文）
python 03_extract_images.py    # 抽出 10 幅插图到 books/survival-economics/img/
python 04_build_site.py        # -> books/survival-economics/index.html
python 06_fidelity_check.py    # 逐段核对：书稿里每一段、每一个表格单元格都在网页里
```

## 核对

```sh
python -m http.server 8099 --bind 127.0.0.1     # 在仓库根目录另开一个终端
python 05_verify_page.py       # Playwright：筛选、检索、深链、深色模式、移动端、入口链接、
                               #   正文与图片同宽、中文首行缩进（共 65 项）
python 07_compare_format.py    # 与参考站逐项比对版式令牌与关键尺寸
python 06_fidelity_check.py    # 逐段核对：书稿每一段、每个表格单元格都在网页里
python 08_dump_cards.py        # 导出每个单元的核心判断与三行说明，便于人工校对措辞
```

上线之后再跑一次线上冒烟（GitHub Pages 从这里访问首屏约 10 秒，脚本会重试并等
`document.readyState === 'complete'`——整本书是一个 HTML 文件，第一张卡片出现得比样式表早得多）：

```sh
python 09_verify_live.py       # 线上页面的 20 项检查，含上面两个排版回归
```

`05_verify_page.py`、`07_compare_format.py`、`09_verify_live.py` 需要本机已安装 Playwright
与 Chromium。

## 每个单元上显示什么

| 字段 | 来源 |
| --- | --- |
| 标题、编号 | 书稿的节标题（`X.Y　标题`） |
| 篇 | 上篇 / 中篇 / 下篇，取自书稿的篇分割 |
| 这一节给你什么 | 由节标题判定：含「行动指南」→可执行清单，含「理论透镜」→分析框架，含「国内民生关切」→看懂自家账本，其余→看懂变局机制 |
| 材料 | 由正文关键词判定：出现「诺贝尔/诺奖」→诺奖理论；出现百分比、万亿、统计局、同比等→官方数据；首段为年份或人物开场的叙事→案例故事；行动清单与附录B→行动工具 |
| 篇幅 | 按正文字数分档：≤1200 字「一坐」、1200–1800「一会儿」、>1800「需专注」 |
| 核心判断 | 该节第一段的第一句（超过 76 字时退到最近的语气停顿处） |
| 成本 / 结构 / 备注 | 由段落数、小标题数、表格数、本章行动条数与数据截止时间算出 |
| 来源与延伸 | 该章的「本章说明」+ 附录A 理论地图中标注本章的条目 + 附录C 中标注本章的延伸阅读 |

所有字段都由书稿本身推出，脚本不撰写任何书稿里没有的结论；`06_fidelity_check.py`
保证没有任何一段被丢掉。

## 排版约定

- **一个阅读栏宽**：`.doc`、章首插图、卡片、篇首横幅、正文段落全部是 900px；卡片与
  篇首横幅内部的文字按各自的内边距内缩（850px / 842px）。正文不再设 `max-width`，
  否则文字会比插图窄。
- **中文首行缩进**：书稿段落带 `class="bk"`（章首导语是 `.lede`，页面说明与篇首导语
  也缩进），由 `style.css` 统一 `text-indent:2em`，与其他中文页面一致。
  摘要式引文（`.human`）、成本/结构行（`.rows`）与编号行动条目不缩进——缩进会和
  引用框、列表标记打架。

## 中间产物

`docx_items.json`、`book_model.json`、`images.json`、`docx_report.txt`、`shots/`、
`cards_report.txt` 都是可重新生成的中间产物，已在 `.gitignore` 中忽略。
