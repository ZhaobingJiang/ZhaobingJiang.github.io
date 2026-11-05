# -*- coding: utf-8 -*-
"""Compose the cover of 《寻找大佬》: Dreamina dusk loess art + PIL typography.

Input : d:\\tmp_bg\\xzdl_cover\\fa705eba-0e06-4f50-85b3-35fc3ed7716f_image_1.png
Output: books/xunzhaodalao/cover.jpg (1600x2400), cover-card.jpg (640x960),
        cover_preview.png (800x1200)
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "books", "xunzhaodalao")
ART = r"D:\tmp_bg\xzdl_cover\fa705eba-0e06-4f50-85b3-35fc3ed7716f_image_1.png"

W, H = 1600, 2400
SERIF_HEAVY = r"C:\Windows\Fonts\Source Han Serif SC Heavy (TrueType).ttf"
SONG = r"C:\Windows\Fonts\STSONG.TTF"
KAI = r"C:\Windows\Fonts\STKAITI.TTF"


def font(path, size):
    return ImageFont.truetype(path, size)


def tracked(draw, xy, text, fnt, fill, tracking=0, center_x=None):
    widths = [draw.textlength(ch, font=fnt) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x, y = xy
    if center_x is not None:
        x = center_x - total / 2
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += w + tracking
    return total


def shadow(base, draw_fn, blur=12, alpha=150, color=(20, 14, 10, 255)):
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    draw_fn(d)
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    r, g, b, a = layer.split()
    a = a.point(lambda v: int(v * alpha / 255))
    return Image.alpha_composite(base, Image.merge("RGBA", (r, g, b, a)))


def main():
    art = Image.open(ART).convert("RGB")
    # source is already 2:3; crop defensively then resize
    tw = int(art.height * 2 / 3)
    x0 = (art.width - tw) // 2
    art = art.crop((x0, 0, x0 + tw, art.height)).resize((W, H), Image.LANCZOS)
    base = art.convert("RGBA")

    # bottom gradient so the tagline and author stay legible
    grad = Image.new("L", (1, H), 0)
    for y in range(H):
        t = max(0.0, (y - H * 0.60) / (H * 0.40))
        grad.putpixel((0, y), int(168 * (t ** 1.25)))
    grad = grad.resize((W, H))
    shade = Image.new("RGBA", (W, H), (14, 16, 26, 255))
    base = Image.composite(shade, base, grad)

    # subtle top gradient for the small label
    grad2 = Image.new("L", (1, H), 0)
    for y in range(H):
        t = max(0.0, (H * 0.18 - y) / (H * 0.18))
        grad2.putpixel((0, y), int(90 * (t ** 1.2)))
    grad2 = grad2.resize((W, H))
    shade2 = Image.new("RGBA", (W, H), (14, 16, 26, 255))
    base = Image.composite(shade2, base, grad2)

    ivory = (247, 240, 228, 255)
    warm = (232, 219, 200, 235)
    soft = (214, 203, 186, 220)
    gold = (176, 136, 84, 255)

    d = ImageDraw.Draw(base)

    # top label
    f_label = font(SONG, 40)
    shadow(base, lambda dd: tracked(dd, (0, 150), "长篇小说", f_label, (12, 14, 22, 210), tracking=20, center_x=W / 2),
           blur=10, alpha=120)
    d = ImageDraw.Draw(base)
    tracked(d, (0, 150), "长篇小说", f_label, soft, tracking=20, center_x=W / 2)

    # title: 4 characters, heavy serif, wide tracking
    f_title = font(SERIF_HEAVY, 292)
    def draw_title(dd):
        tracked(dd, (0, 258), "寻找大佬", f_title, ivory, tracking=40, center_x=W / 2)

    base = shadow(base, draw_title, blur=22, alpha=170)
    d = ImageDraw.Draw(base)
    draw_title(d)

    # subtitle
    f_sub = font(KAI, 62)
    shadow(base, lambda dd: tracked(dd, (0, 648), "一个寒门子弟的三十七年", f_sub, (10, 12, 20, 210), tracking=12, center_x=W / 2),
           blur=10, alpha=130)
    d = ImageDraw.Draw(base)
    tracked(d, (0, 648), "一个寒门子弟的三十七年", f_sub, warm, tracking=12, center_x=W / 2)

    # thin rule under the subtitle
    d.line([(W / 2 - 150, 745), (W / 2 + 150, 745)], fill=(176, 136, 84, 200), width=3)

    # tagline, two lines, small kaiti
    f_tag = font(KAI, 56)
    tag1 = "我找的不是大佬，"
    tag2 = "是一个能替我爹还手的人。"
    shadow(base, lambda dd: tracked(dd, (0, 1985), tag1, f_tag, (8, 10, 18, 220), tracking=6, center_x=W / 2), blur=8, alpha=120)
    shadow(base, lambda dd: tracked(dd, (0, 2075), tag2, f_tag, (8, 10, 18, 220), tracking=6, center_x=W / 2), blur=8, alpha=120)
    d = ImageDraw.Draw(base)
    tracked(d, (0, 1985), tag1, f_tag, (228, 216, 198, 225), tracking=6, center_x=W / 2)
    tracked(d, (0, 2075), tag2, f_tag, (228, 216, 198, 225), tracking=6, center_x=W / 2)

    # author
    f_author = font(SONG, 46)
    shadow(base, lambda dd: tracked(dd, (0, 2218), "江召兵　著", f_author, (8, 10, 18, 220), tracking=10, center_x=W / 2), blur=8, alpha=120)
    d = ImageDraw.Draw(base)
    tracked(d, (0, 2218), "江召兵　著", f_author, ivory, tracking=10, center_x=W / 2)

    os.makedirs(OUT, exist_ok=True)
    cover = base.convert("RGB")
    cover.save(os.path.join(OUT, "cover.jpg"), quality=90, optimize=True)
    cover.resize((640, 960), Image.LANCZOS).save(os.path.join(OUT, "cover-card.jpg"), quality=88, optimize=True)
    cover.resize((800, 1200), Image.LANCZOS).save(os.path.join(OUT, "cover_preview.png"))
    for name in ("cover.jpg", "cover-card.jpg", "cover_preview.png"):
        p = os.path.join(OUT, name)
        print(name, os.path.getsize(p))


if __name__ == "__main__":
    main()
