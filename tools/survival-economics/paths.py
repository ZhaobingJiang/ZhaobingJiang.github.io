# -*- coding: utf-8 -*-
"""Shared paths for the Survival Economics web-edition pipeline.

The scripts live in <repo>/tools/survival-economics/ and write the published page
into <repo>/books/survival-economics/.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BOOKS = os.path.join(ROOT, "books")
DOCX = os.path.join(BOOKS, "survival_economics_uncertain_times_v3_illustrated.docx")
SITE = os.path.join(BOOKS, "survival-economics")
IMG = os.path.join(SITE, "img")
PAGE = os.path.join(SITE, "index.html")

ITEMS = os.path.join(HERE, "docx_items.json")
MODEL = os.path.join(HERE, "book_model.json")
IMAGES = os.path.join(HERE, "images.json")
