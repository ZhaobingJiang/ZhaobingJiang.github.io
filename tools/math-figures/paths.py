# -*- coding: utf-8 -*-
"""Shared paths for the Luck Engineering web-edition pipeline."""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BOOKS = os.path.join(ROOT, "books")
DOCX = os.path.join(BOOKS, "most_beautiful_math_figures_science_and_art.docx")
SITE = os.path.join(BOOKS, "math-figures")
IMG = os.path.join(SITE, "img")
PAGE = os.path.join(SITE, "index.html")

# 版式与交互层的唯一来源：构建时复制到每一本书自己的目录里
SHARED = os.path.join(ROOT, "tools", "web-edition")

ITEMS = os.path.join(HERE, "docx_items.json")
MODEL = os.path.join(HERE, "book_model.json")
IMAGES = os.path.join(HERE, "images.json")
