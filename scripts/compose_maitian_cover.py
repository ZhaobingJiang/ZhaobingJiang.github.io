# -*- coding: utf-8 -*-
"""Compose the cover of 《麦田怪圈》: Dreamina art + PIL typography.
Outputs: cover.jpg (640x960) and cover_preview.png (1280x1920).
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ART = r"D:\自主择业\江召兵诗词\麦田怪圈小说\封面\cover_art.png"
W, H = 1280, 1920

SERIF_HEAVY = r"C:\Windows\Fonts\Source Han Serif SC Heavy (TrueType).ttf"
SERIF = r"C:\Windows\Fonts\NotoSerifSC-VF.ttf"
SONG = r"C:\Windows\Fonts\STSONG.TTF"
SANS = r"C:\Windows\Fonts\msyh.ttc"


def font(path, size):
    return ImageFont.truetype(path, size)


def tracked_text(draw, xy, text, fnt, fill, tracking=0, anchor_center_x=None):
    """Draw text with letter spacing; optionally centered on x."""
    widths = [draw.textlength(ch, font=fnt) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x, y = xy
    if anchor_center_x is not None:
        x = anchor_center_x - total / 2
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += w + tracking
    return total


def shadow_layer(size, draw_fn, blur=10, alpha=150):
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    draw_fn(d)
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    # darken alpha
    r, g, b, a = layer.split()
    a = a.point(lambda v: int(v * alpha / 255))
    return Image.merge("RGBA", (r, g, b, a))


def main():
    art = Image.open(ART).convert("RGB")
    # cover art is 2:3 already (3328x4992)
    art = art.resize((W, H), Image.LANCZOS)
    base = art.convert("RGBA")

    # gentle dark vignette at bottom for tagline legibility
    grad = Image.new("L", (1, H), 0)
    for y in range(H):
        t = max(0.0, (y - H * 0.72) / (H * 0.28))
        grad.putpixel((0, y), int(110 * (t ** 1.2)))
    grad = grad.resize((W, H))
    black = Image.new("RGBA", (W, H), (10, 8, 6, 255))
    base = Image.composite(black, base, grad.point(lambda v: v))

    d = ImageDraw.Draw(base)

    ink = (26, 19, 13, 255)
    deep = (42, 30, 20, 255)
    gold = (120, 92, 54, 255)
    ivory = (246, 234, 208, 255)
    muted = (226, 208, 178, 255)

    # ---- top label ----
    f_label = font(SONG, 32)
    tracked_text(d, (0, 88), "长 篇 小 说", f_label, ivory, tracking=8, anchor_center_x=W / 2)

    # ---- title (2 lines, big serif, ivory on dark cloud) ----
    f_title = font(SERIF_HEAVY, 152)
    title_lines = ["麦田", "怪圈"]
    y = 132
    for line in title_lines:
        tw = sum(d.textlength(ch, font=f_title) for ch in line) + 10 * (len(line) - 1)
        tx = (W - tw) / 2

        def draw_title(dd, line=line, tx=tx, y=y):
            dd.text((tx, y), line, font=f_title, fill=(0, 0, 0, 255))

        base = Image.alpha_composite(base, shadow_layer((W, H), draw_title, blur=14, alpha=210))
        d = ImageDraw.Draw(base)
        tracked_text(d, (0, y), line, f_title, (250, 240, 218, 255), tracking=10, anchor_center_x=W / 2)
        y += 190

    # thin rule
    d.line([(W / 2 - 140, y + 10), (W / 2 + 140, y + 10)], fill=(236, 222, 196, 220), width=2)

    # ---- author ----
    f_author = font(SONG, 40)
    ax_text = "江 召 兵 著"

    def draw_author(dd):
        dd.text((W / 2 - 120, y + 40), ax_text, font=f_author, fill=(0, 0, 0, 255))

    base = Image.alpha_composite(base, shadow_layer((W, H), draw_author, blur=9, alpha=220))
    d = ImageDraw.Draw(base)
    tracked_text(d, (0, y + 40), ax_text, f_author, (244, 232, 208, 255), tracking=10, anchor_center_x=W / 2)

    # ---- bottom tagline ----
    f_tag = font(SERIF, 54)
    f_small = font(SONG, 30)
    tag = "麦子会记住。人不会。"
    tw = sum(d.textlength(ch, font=f_tag) for ch in tag) + 2 * (len(tag) - 1)
    tx, ty = (W - tw) / 2, 1662

    def draw_tag(dd):
        dd.text((tx, ty), tag, font=f_tag, fill=(8, 6, 4, 255))

    base = Image.alpha_composite(base, shadow_layer((W, H), draw_tag, blur=8, alpha=170))
    d = ImageDraw.Draw(base)
    tracked_text(d, (0, ty), tag, f_tag, ivory, tracking=2, anchor_center_x=W / 2)

    sub = "十二年后，麦田里长出一张脸"
    f_sub = font(SONG, 32)
    tracked_text(d, (0, ty + 82), sub, f_sub, muted, tracking=3, anchor_center_x=W / 2)

    # save
    out = base.convert("RGB")
    out.save(os.path.join(HERE, "cover_preview.png"))
    out.resize((640, 960), Image.LANCZOS).save(os.path.join(HERE, "cover.jpg"), quality=92, optimize=True)
    print("saved cover.jpg and cover_preview.png")


if __name__ == "__main__":
    main()
