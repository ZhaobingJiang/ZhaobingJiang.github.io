# 两个网页版共用同一份版式与交互

`style.css` 与 `app.js` 是《不确定年代的生存经济学》和《运气工程学》两个网页版
唯一的版式来源。各书的生成脚本在构建时把它们复制到自己的目录
（`books/<书>/style.css`、`app.js`），所以每个页面仍然自包含、URL 不变，
同时不存在两份会各自漂移的样式副本。

改版式只改这里，然后重新构建受影响的书：

```sh
cd tools/survival-economics && python 04_build_site.py
cd tools/luck-engineering    && python 04_build_site.py
```

两边都会打印 `copied style.css from tools/web-edition/`；把它们和 `index.html`
一起提交即可。核对时 `05_verify_page.py` 会断言页面里的 `app.js` 与这里的源文件一致。

## 页面需要满足的结构约定

`app.js` 不认识具体是哪一本书，只按下面的标记工作：

- `#list .card`，属性 `data-ch` `data-part` `data-kind` `data-mats`（`|` 连接）
  `data-len` `data-flag` `data-table` `data-search`
- `#list .sec-block[data-ch]`，内部 `.shown .k` 是计数
- `#list .part[data-part]`：篇首横幅，随本篇是否还有可见单元显隐
- `#f-ch [data-v]` 章节按钮，每个后面紧跟自己的 `.toc-sub[data-for]` 面板
  （面板里 `a[data-go]` 是目录项，`.toc-none` 是空结果提示）
- `[data-dim="part|kind|mat|len"] [data-v]` 筛选按钮/标签
- `#f-flag`、`#f-table` 两个开关，`#q` 搜索框，`#cnt` 计数，`#empty` 空状态，
  `#reset`/`#reset2` 清空，`#theme` 主题，`#menu`/`#backdrop` 移动端抽屉

`app.js` 在筛选器装配完成后给 `<html>` 打 `data-ready="1"`；外部核对应当等这个标记，
不要等 `readyState`——整本书是一个几百 KB 的 HTML，首屏卡片出现得比样式表早得多。

## 字阶

`--fs` 是正文（书稿段落）字号，阅读区其余字号都由它加减得出，改这一个值即可整体缩放。
顶栏与侧栏是导航，保持参考站的紧凑尺寸，不随 `--fs` 变化。
