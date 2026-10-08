# -*- coding: utf-8 -*-
"""Walk a DOCX into a block list, keeping inline equations and images in place.

python-docx's paragraph.text concatenates only w:r runs, so every inline equation
(the manuscript holds 580 of them) would vanish and leave a hole in the sentence.
This reader walks the paragraph's own children in document order and emits text,
math and image markers exactly where the manuscript puts them.
"""
import json
import os
import sys

import docx
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import DOCX, ITEMS  # noqa: E402

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
M = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"


def math_children(el):
    """Flatten one OMML expression into [str | {'sub':(base,sub)} | {'frac':(num,den)}]."""
    out = []
    for child in el:
        tag = child.tag.replace(M, "")
        if tag == "r":
            out.append("".join(t.text or "" for t in child.findall(f"{M}t")))
        elif tag == "sSub":
            base, sub = child.find(f"{M}e"), child.find(f"{M}sub")
            out.append({"sub": [math_children(base), math_children(sub)]})
        elif tag == "sSup":
            base, sup = child.find(f"{M}e"), child.find(f"{M}sup")
            out.append({"sup": [math_children(base), math_children(sup)]})
        elif tag == "f":
            num, den = child.find(f"{M}num"), child.find(f"{M}den")
            out.append({"frac": [math_children(num), math_children(den)]})
        elif tag in ("oMath", "oMathPara", "e", "num", "den", "sub", "sup", "d", "rad",
                     "func", "nary", "acc", "bar", "groupChr", "limLow", "limUpp", "sPre",
                     "sSubSup", "box", "borderBox", "phant"):
            out.extend(math_children(child))
        else:
            out.extend(math_children(child))
    return out


def run_flags(r):
    """Bold/italic of one w:r; w:b with val 0/false/off means explicitly off."""
    out = {"b": False, "i": False}
    rPr = r.find(f"{W}rPr")
    if rPr is None:
        return out
    for key, tag in (("b", f"{W}b"), ("i", f"{W}i")):
        el = rPr.find(tag)
        if el is not None and el.get(f"{W}val") not in ("0", "false", "off"):
            out[key] = True
    return out


def add_text(nodes, v, b=False, i=False):
    if not v:
        return
    last = nodes[-1] if nodes else None
    if last and last["t"] == "text" and last.get("b") == b and last.get("i") == i:
        last["v"] += v
    else:
        nodes.append({"t": "text", "v": v, "b": b, "i": i})


def inline_of(p):
    """Inline nodes of a paragraph: text (with bold/italic), math and images, in order."""
    nodes = []

    def walk(el):
        for child in el:
            tag = child.tag
            if tag == f"{W}r":
                flags = run_flags(child)
                for sub in child:
                    if sub.tag == f"{W}t":
                        add_text(nodes, sub.text or "", flags["b"], flags["i"])
                    elif sub.tag == f"{W}br":
                        add_text(nodes, "\n")
                    elif sub.tag == f"{W}tab":
                        add_text(nodes, "\t")
                    elif sub.tag in (f"{W}drawing", f"{W}pict", f"{W}object"):
                        nodes.append({"t": "img"})
            elif tag == f"{M}oMath":
                nodes.append({"t": "math", "v": math_children(child)})
            elif tag in (f"{W}hyperlink", f"{W}smartTag", f"{W}sdt", f"{W}sdtContent",
                         f"{W}ins", f"{W}del"):
                walk(child)
            elif tag in (f"{W}bookmarkStart", f"{W}bookmarkEnd", f"{W}pPr", f"{W}rPr",
                         f"{W}proofErr", f"{W}commentRangeStart", f"{W}commentRangeEnd"):
                continue
            else:
                walk(child)

    walk(p)
    return nodes


def text_of(nodes):
    """Plain text of an inline list; equations become [Sym] so nothing is lost silently."""
    out = []
    for n in nodes:
        if n["t"] == "text":
            out.append(n["v"])
        elif n["t"] == "math":
            out.append("⟨math⟩")
        elif n["t"] == "img":
            out.append("⟨img⟩")
    return "".join(out)


def iter_blocks(parent):
    for child in parent.element.body.iterchildren():
        if child.tag == f"{W}p":
            yield Paragraph(child, parent)
        elif child.tag == f"{W}tbl":
            yield Table(child, parent)


def main():
    doc = docx.Document(DOCX)
    items = []
    for block in iter_blocks(doc):
        if isinstance(block, Paragraph):
            nodes = inline_of(block._p)
            items.append({
                "kind": "p",
                "style": block.style.name if block.style is not None else "",
                "nodes": nodes,
                "text": text_of(nodes).strip(),
                "img": any(n["t"] == "img" for n in nodes),
            })
        else:
            rows = []
            for row in block.rows:
                cells = []
                for c in row.cells:
                    nodes = []
                    for para in c.paragraphs:
                        ns = inline_of(para._p)
                        if not text_of(ns).strip() and not any(n["t"] == "img" for n in ns):
                            continue
                        if nodes:
                            nodes.append({"t": "text", "v": " ", "b": False, "i": False})
                        nodes.extend(ns)
                    cells.append(nodes)
                rows.append(cells)
            items.append({"kind": "table", "rows": rows})

    json.dump(items, open(ITEMS, "w", encoding="utf-8"), ensure_ascii=False)
    n_p = sum(1 for i in items if i["kind"] == "p")
    n_math = sum(1 for i in items if i["kind"] == "p" for n in i["nodes"] if n["t"] == "math")
    n_img = sum(1 for i in items if i["kind"] == "p" and i["img"])
    n_tab = sum(1 for i in items if i["kind"] == "table")
    chars = sum(len(i["text"]) for i in items if i["kind"] == "p")
    print(f"paragraphs={n_p} tables={n_tab} images={n_img} inline-equations={n_math}")
    print(f"body chars={chars:,}")
    print(f"-> {ITEMS}")


if __name__ == "__main__":
    sys.exit(main())
