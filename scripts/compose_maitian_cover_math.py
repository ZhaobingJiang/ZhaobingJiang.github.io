# -*- coding: utf-8 -*-
"""Compose the math-themed cover of 《麦田怪圈》: Dreamina crop-circle art + PIL typography.
Outputs: cover.jpg (640x960) and cover_preview.png (1280x1920).
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ART = r"D:\自主择业\江召兵诗词\麦田怪圈小说\封面\cover_art_math.png"
W, H = 1280, 1920

SERIF_HEAVY = r"C:\Windows\Fonts\Source Han Serif SC Heavy (TrueType).ttf"
SERIF = r"C:\Windows\Fonts\NotoSerifSC-VF.ttf"
SONG = r"C:\Windows\Fonts\STSONG.TTF"
SANS = r"C:\Windows\Fonts\msyh.ttc"


def font(path, size):
    return ImageFont.truetype(path, size)


def tracked_text(draw, xy, text, fnt, fill, tracking=0, center_x=None,
                 stroke_width=0, stroke_fill=None):
    widths = [draw.textlength(ch, font=fnt) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x, y = xy
    if center_x is not None:
        x = center_x - total / 2
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, font=fnt, fill=fill,
                  stroke_width=stroke_width, stroke_fill=stroke_fill)
        x += w + tracking
    return total


def shadow(size, draw_fn, blur=12, alpha=210):
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(layer))
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    r, g, b, a = layer.split()
    a = a.point(lambda v: int(v * alpha / 255))
    return Image.merge("RGBA", (r, g, b, a))


def gradient_mask(w, h, y0, y1, strength, invert=False):
    g = Image.new("L", (1, h), 0)
    for y in range(h):
        t = (y - y0) / max(1, (y1 - y0))
        t = min(1.0, max(0.0, t))
        if invert:
            t = 1 - t
        g.putpixel((0, y), int(strength * (t ** 1.25)))
    return g.resize((w, h))


def main():
    art = Image.open(ART).convert("RGB")
    # 2:3 art already; crop slightly to 2:3 then resize
    aw, ah = art.size
    target = W / H
    if aw / ah > target:
        nw = int(ah * target)
        art = art.crop(((aw - nw) // 2, 0, (aw - nw) // 2 + nw, ah))
    art = art.resize((W, H), Image.LANCZOS).convert("RGBA")

    # top dark gradient for title, bottom for tagline
    top = Image.new("RGBA", (W, H), (8, 6, 4, 255))
    art = Image.composite(top, art, gradient_mask(W, H, 0, int(H * 0.30), 190, invert=True))
    bottom = Image.new("RGBA", (W, H), (8, 6, 4, 255))
    art = Image.composite(bottom, art, gradient_mask(W, H, int(H * 0.74), H, 165))

    base = art
    d = ImageDraw.Draw(base)

    ivory = (246, 236, 214, 255)
    muted = (222, 206, 178, 232)
    faint = (228, 214, 188, 190)

    # ---- top label ----
    f_label = font(SONG, 30)
    tracked_text(d, (0, 92), "悬 疑 长 篇 小 说", f_label, muted, tracking=10, center_x=W / 2)

    # ---- title（四字单行）----
    f_title = font(SERIF_HEAVY, 205)
    title = "麦田怪圈"
    title_tracking = 12
    tw = sum(d.textlength(ch, font=f_title) for ch in title) + title_tracking * (len(title) - 1)
    tx = (W - tw) / 2
    ty = 150
    base = Image.alpha_composite(base, shadow((W, H), lambda dd, tx=tx, ty=ty: dd.text((tx + 5, ty + 7), title, font=f_title, fill=(0, 0, 0, 255)), blur=20, alpha=235))
    d = ImageDraw.Draw(base)
    tracked_text(d, (0, ty), title, f_title, ivory, tracking=title_tracking, center_x=W / 2,
                 stroke_width=2, stroke_fill=(26, 16, 10, 255))

    # ---- author（加大、下移；黑色字，浅色麦田上对比清晰）----
    f_author = font(SONG, 70)
    ay = 606
    author = "江 召 兵 著"
    aw = sum(d.textlength(ch, font=f_author) for ch in author)
    base = Image.alpha_composite(base, shadow((W, H), lambda dd: dd.text(((W - aw) / 2 + 2, ay + 4), author, font=f_author, fill=(0, 0, 0, 255)), blur=10, alpha=110))
    d = ImageDraw.Draw(base)
    tracked_text(d, (0, ay), author, f_author, (20, 14, 9, 255), tracking=2, center_x=W / 2)

    # ---- math annotations ----
    f_math = font(SERIF, 28)
    f_math_small = font(SERIF, 22)
    naive = (242, 230, 208, 240)

    def ann(x, y, text, fnt, fill, tracking=1, right_align=False):
        nonlocal base, d
        w = sum(d.textlength(ch, font=fnt) for ch in text) + tracking * (len(text) - 1)
        xx = (W - 78 - w) if right_align else x
        base = Image.alpha_composite(base, shadow((W, H), lambda dd: dd.text((xx, y), text, font=fnt, fill=(0, 0, 0, 255)), blur=8, alpha=190))
        d = ImageDraw.Draw(base)
        tracked_text(d, (xx, y), text, fnt, fill, tracking=tracking)

    ann(78, 905, "φ = (1+√5)/2 ≈ 1.618", f_math, naive)
    ann(78, 947, "黄金比 · 螺旋线", f_math_small, (226, 212, 186, 225), tracking=3)
    ann(0, 905, "π ≈ 3.1415926", f_math, naive, right_align=True)
    ann(0, 947, "圆周 · 无穷", f_math_small, (226, 212, 186, 225), tracking=3, right_align=True)

    # fibonacci line above tagline
    f_fib = font(SERIF, 26)
    fib = "1 · 1 · 2 · 3 · 5 · 8 · 13 · 21"
    base = Image.alpha_composite(base, shadow((W, H), lambda dd: dd.text((0, 1540), fib, font=f_fib, fill=(0, 0, 0, 255)), blur=8, alpha=170))
    d = ImageDraw.Draw(base)
    tracked_text(d, (0, 1540), fib, f_fib, (238, 224, 198, 235), tracking=8, center_x=W / 2)

    # ---- tagline ----
    f_tag = font(SERIF, 46)
    tag = "所有的圆，都指向一个被藏起来的答案。"
    tw = sum(d.textlength(ch, font=f_tag) for ch in tag) + 1 * (len(tag) - 1)
    tx, ty = (W - tw) / 2, 1625
    base = Image.alpha_composite(base, shadow((W, H), lambda dd, tx=tx, ty=ty, tag=tag: dd.text((tx, ty), tag, font=f_tag, fill=(0, 0, 0, 255)), blur=10, alpha=200))
    d = ImageDraw.Draw(base)
    tracked_text(d, (0, ty), tag, f_tag, ivory, tracking=1, center_x=W / 2)

    f_sub = font(SONG, 29)
    tracked_text(d, (0, ty + 78), "π · φ · 斐波那契数列 —— 麦田用它写了一个名字", f_sub, (232, 218, 192, 240), tracking=3, center_x=W / 2)

    out = base.convert("RGB")
    out.save(os.path.join(HERE, "cover_preview.png"))
    out.resize((640, 960), Image.LANCZOS).save(os.path.join(HERE, "cover.jpg"), quality=92, optimize=True)
    print("saved cover.jpg and cover_preview.png")


if __name__ == "__main__":
    main()
