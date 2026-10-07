# -*- coding: utf-8 -*-
"""Dump every card's derived one-liner and rows so the wording can be reviewed."""
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from paths import HERE, PAGE
html = open(PAGE, encoding="utf-8").read()

cards = re.findall(
    r'<article class="card" id="([^"]+)".*?<h3>(.*?)</h3>.*?<p class="human">(.*?)</p>(.*?)</article>',
    html, re.S)
out = []
for cid, title, human, rest in cards:
    rows = re.findall(r'<div class="k">(.*?)</div><div class="v[^"]*">(.*?)</div>', rest, re.S)
    out.append(f"{cid:<10} {title}")
    out.append(f"           核心判断: {human}")
    for k, v in rows:
        out.append(f"           {k}: {v}")
open(os.path.join(HERE, "cards_report.txt"), "w", encoding="utf-8").write("\n".join(out))
print(f"{len(cards)} cards written to cards_report.txt")
long_human = [(cid, h) for cid, t, h, r in cards if len(h) > 70]
print(f"one-liners over 70 chars: {len(long_human)}")
for cid, h in long_human[:15]:
    print(f"  {cid}: {h}")
