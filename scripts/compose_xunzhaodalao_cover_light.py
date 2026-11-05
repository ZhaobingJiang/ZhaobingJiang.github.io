# -*- coding: utf-8 -*-
"""Compose the cover of 《寻找大佬》: Dreamina dusk loess art + PIL typography.

Typography:
  长篇小说 / 寻找大佬 / 屈原《离骚》句（路漫漫其修远兮，吾将上下而求索）
  / 阿德勒《自卑与超越》句（生活的意义在于对别人发生兴趣以及互助合作）/ 江召兵 著

Input : d:\\tmp_bg\\xzdl_cover\\fa705eba-0e06-4f50-85b3-35fc3ed7716f_image_1.png
Output: books/xunzhaodalao/cover.jpg (1600x2400), cover-card.jpg (640x960),
        cover_preview.png (800x1200)
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "books", "xunzhaodalao")
if len(sys.argv) > 2:
    OUT = sys.argv[2]
ART = r"D:\tmp_bg\xzdl_cover\fa705eba-0e06-4f50-85b3-35fc3ed7716f_image_1.png"
if len(sys.argv) > 1:
    ART = sys.argv[1]

W, H = 1600, 2400
SERIF_HEAVY = r"C:\Windows\Fonts\Source Han Serif SC Heavy (TrueType).ttf"
SONG = r"C:\Windows\Fonts\STSONG.TTF"
KAI = r"C:\Windows\Fonts\STKAITI.TTF"

POEM = "路漫漫其修远兮，吾将上下而求索。"
POEM_SRC = "—— 屈原《离骚》"
PSY = "生活的意义在于对别人发生兴趣以及互助合作。"
PSY_SRC = "—— 阿德勒《自卑与超越》"


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
    style = sys.argv[3] if len(sys.argv) > 3 else "light"
    art = Image.open(ART).convert("RGB")
    # source is already 2:3; crop defensively then resize
    tw = int(art.height * 2 / 3)
    x0 = (art.width - tw) // 2
    art = art.crop((x0, 0, x0 + tw, art.height)).resize((W, H), Image.LANCZOS)
    base = art.convert("RGBA")

    # bottom gradient so quotes and author stay legible
    grad = Image.new("L", (1, H), 0)
    for y in range(H):
        t = max(0.0, (y - H * 0.58) / (H * 0.42))
        grad.putpixel((0, y), int(178 * (t ** 1.2)))
    grad = grad.resize((W, H))
    shade = Image.new("RGBA", (W, H), (14, 16, 26, 255))
    base = Image.composite(shade, base, grad)

    if style == "dark":
        # subtle top gradient for the small label
        grad2 = Image.new("L", (1, H), 0)
        for y in range(H):
            t = max(0.0, (H * 0.18 - y) / (H * 0.18))
            grad2.putpixel((0, y), int(90 * (t ** 1.2)))
        grad2 = grad2.resize((W, H))
        shade2 = Image.new("RGBA", (W, H), (14, 16, 26, 255))
        base = Image.composite(shade2, base, grad2)

    ivory = (247, 240, 228, 255)
    warm = (232, 219, 200, 238)
    soft = (214, 203, 186, 215)
    gold = (182, 142, 90, 235)
    if style == "light":
        label_col = (56, 68, 78, 240)
        title_col = (24, 32, 40, 255)
        poem_col = (38, 50, 60, 255)
        poem_src_col = (86, 98, 108, 240)
        title_shadow = (250, 250, 244, 120)
        poem_shadow = (250, 250, 244, 100)
    else:
        label_col = soft
        title_col = ivory
        poem_col = warm
        poem_src_col = (232, 223, 208, 235)
        title_shadow = (20, 14, 10, 255)
        poem_shadow = (6, 8, 16, 215)

    # ---- top label ----
    f_label = font(SONG, 40)
    shadow(base, lambda dd: tracked(dd, (0, 146), "长篇小说", f_label, (12, 14, 22, 210) if style == "dark" else (250, 250, 244, 200), tracking=20, center_x=W / 2),
           blur=10, alpha=120)
    d = ImageDraw.Draw(base)
    tracked(d, (0, 146), "长篇小说", f_label, label_col, tracking=20, center_x=W / 2)

    # ---- title ----
    f_title = font(SERIF_HEAVY, 292)
    def draw_title(dd):
        tracked(dd, (0, 252), "寻找大佬", f_title, title_shadow, tracking=40, center_x=W / 2)

    base = shadow(base, draw_title, blur=22, alpha=175 if style == "dark" else 110)
    d = ImageDraw.Draw(base)
    tracked(d, (0, 252), "寻找大佬", f_title, title_col, tracking=40, center_x=W / 2)

    # ---- classical poem line under the title ----
    f_poem = font(KAI, 54)
    shadow(base, lambda dd: tracked(dd, (0, 642), POEM, f_poem, poem_shadow, tracking=8, center_x=W / 2),
           blur=9, alpha=130)
    d = ImageDraw.Draw(base)
    tracked(d, (0, 642), POEM, f_poem, poem_col, tracking=8, center_x=W / 2)

    f_src = font(SONG, 30)
    shadow(base, lambda dd: tracked(dd, (0, 718), POEM_SRC, f_src, (6, 8, 16, 210), tracking=6, center_x=W / 2),
           blur=11, alpha=185)
    d = ImageDraw.Draw(base)
    tracked(d, (0, 718), POEM_SRC, f_src, poem_src_col, tracking=6, center_x=W / 2)

    # ---- Adler line, bottom ----
    f_psy = font(KAI, 42)
    shadow(base, lambda dd: tracked(dd, (0, 2050), PSY, f_psy, (6, 8, 16, 220), tracking=3, center_x=W / 2),
           blur=8, alpha=130)
    d = ImageDraw.Draw(base)
    tracked(d, (0, 2050), PSY, f_psy, (232, 221, 203, 232), tracking=3, center_x=W / 2)

    f_psy_src = font(SONG, 27)
    shadow(base, lambda dd: tracked(dd, (0, 2106), PSY_SRC, f_psy_src, (6, 8, 16, 210), tracking=5, center_x=W / 2),
           blur=7, alpha=115)
    d = ImageDraw.Draw(base)
    tracked(d, (0, 2106), PSY_SRC, f_psy_src, (228, 219, 204, 232), tracking=5, center_x=W / 2)

    # ---- author ----
    f_author = font(SONG, 46)
    shadow(base, lambda dd: tracked(dd, (0, 2228), "江召兵　著", f_author, (8, 10, 18, 220), tracking=10, center_x=W / 2), blur=8, alpha=120)
    d = ImageDraw.Draw(base)
    tracked(d, (0, 2228), "江召兵　著", f_author, ivory, tracking=10, center_x=W / 2)

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


