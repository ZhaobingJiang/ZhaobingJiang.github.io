#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验全站访问量统计的完整性，防止后续改版丢失历史访问量或漏接页面。

口径：首页页脚显示 = 历史基数 BASELINE（2189，2026-10-21 前的累计）
      + Vercount 全站 PV（每个页面加载上报一次，任意页面访问都会累加）。

校验项：
1. assets/js/site-counter.js 的 BASELINE 存在且不小于 2189（只能调大）。
2. 所有 HTML 页面都引用 site-counter.js，且版本号（?v=N）全站一致。
3. 中英文首页都保留 #visit-counter 与 data-base，且 data-base 与 BASELINE 一致。

本地运行：python3 scripts/verify_visit_counter.py
CI：.github/workflows/visit-counter-guard.yml 在 push / PR 时运行本脚本。
"""
import re
import sys
from pathlib import Path

MIN_BASELINE = 2189
ROOT = Path(__file__).resolve().parents[1]

errors = []

counter_js = ROOT / "assets/js/site-counter.js"
if not counter_js.is_file():
    errors.append("assets/js/site-counter.js 缺失（历史访问量将无法统计）")
    js = ""
    js_base = MIN_BASELINE
else:
    js = counter_js.read_text(encoding="utf-8")
    match = re.search(r"var\s+BASELINE\s*=\s*(\d+)", js)
    if not match:
        errors.append("assets/js/site-counter.js: BASELINE 常量缺失（历史访问量会丢失）")
        js_base = MIN_BASELINE
    else:
        js_base = int(match.group(1))
        if js_base < MIN_BASELINE:
            errors.append(
                f"assets/js/site-counter.js: BASELINE={js_base} 小于最小要求 {MIN_BASELINE}（历史访问量只能调大）"
            )
    if "events.vercount.one" not in js:
        errors.append("assets/js/site-counter.js: 未找到 Vercount（events.vercount.one）上报逻辑")

pages = sorted(p for p in ROOT.rglob("*.html") if ".git" not in p.parts)
missing = []
duplicated = []
versions = set()
for page in pages:
    text = page.read_text(encoding="utf-8", errors="ignore")
    refs = re.findall(r"site-counter\.js\?v=(\d+)", text)
    if not refs:
        missing.append(page.relative_to(ROOT).as_posix())
    elif len(refs) > 1:
        duplicated.append(page.relative_to(ROOT).as_posix())
    versions.update(refs)

if missing:
    errors.append(
        f"{len(missing)} 个 HTML 页面缺少访问量统计脚本: " + ", ".join(missing[:10])
    )
if duplicated:
    errors.append(
        f"{len(duplicated)} 个 HTML 页面重复引用访问量统计脚本: " + ", ".join(duplicated[:10])
    )
if len(versions) > 1:
    errors.append("全站 site-counter.js 的 ?v= 版本号不一致: " + ", ".join(sorted(versions)))

for rel in ("index.html", "zh/index.html"):
    page = ROOT / rel
    if not page.is_file():
        errors.append(f"{rel} 缺失")
        continue
    text = page.read_text(encoding="utf-8")
    if 'id="visit-counter"' not in text:
        errors.append(f"{rel}: 缺少 #visit-counter 元素（访问量无处显示）")
    base_match = re.search(r'id="visit-counter"[^>]*data-base="(\d+)"', text)
    if not base_match:
        errors.append(f"{rel}: 缺少 data-base（历史基数兜底值）")
    elif int(base_match.group(1)) != js_base:
        errors.append(
            f"{rel}: data-base={base_match.group(1)} 与脚本 BASELINE={js_base} 不一致"
        )

if errors:
    for err in errors:
        print(f"::error::{err}")
    sys.exit(1)

print(
    f"visit counter integrity: OK  (pages={len(pages)}, baseline={js_base}, version={','.join(sorted(versions))})"
)
