# -*- coding: utf-8 -*-
"""Compose the new cover of 《账本》: Dreamina dawn loess art + PIL typography.

Input : D:\\tmp_bg\\zb_cover_v2\\083eb449-c941-4e17-bd36-f466b12eb159_image_1.png
Output: books/zhangben/cover.jpg (1600x2400), cover-card.jpg (640x960),
        cover_preview.png (800x1200)
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "books", "zhangben")
ART = r"D:\tmp_bg\zb_cover_v2\083eb449-c941-4e17-bd36-f466b12eb159_image_1.png"

W, H = 1600, 2400
SERIF_HEAVY = r"C:\Windows\Fonts\Source Han Serif SC Heavy (TrueType).ttf"
SONG = r"C:\Windows\Fonts\STSONG.TTF"
ZHONGSONG = r"C:\Windows\Fonts\STZHONGS.TTF"
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
    # crop 3:4 source to 2:3, keeping the full height and centring horizontally
    tw = int(art.height * 2 / 3)
    x0 = (art.width - tw) // 2
    art = art.crop((x0, 0, x0 + tw, art.height)).resize((W, H), Image.LANCZOS)
    base = art.convert("RGBA")

    # gentle bottom gradient so the ivory author/tagline stay legible
    grad = Image.new("L", (1, H), 0)
    for y in range(H):
        t = max(0.0, (y - H * 0.70) / (H * 0.30))
        grad.putpixel((0, y), int(125 * (t ** 1.3)))
    grad = grad.resize((W, H))
    shade = Image.new("RGBA", (W, H), (18, 12, 8, 255))
    base = Image.composite(shade, base, grad)

    d = ImageDraw.Draw(base)

    ink = (34, 27, 22, 255)
    brown = (74, 55, 42, 255)
    muted = (104, 80, 60, 255)
    gold = (154, 113, 66, 255)
    ivory = (247, 235, 214, 255)
    warm = (238, 220, 192, 255)

    # top label
    f_label = font(SONG, 36)
    tracked(d, (0, 112), "长篇小说", f_label, brown, tracking=14, center_x=W / 2)

    # title
    f_title = font(SERIF_HEAVY, 330)
    title = "账本"
    title_w = sum(d.textlength(ch, font=f_title) for ch in title) + 34 * (len(title) - 1)
    tx = (W - title_w) / 2
    ty = 190

    def draw_title(dd):
        dd.text((tx, ty), title, font=f_title, fill=(0, 0, 0, 255))

    base = shadow(base, draw_title, blur=16, alpha=110)
    d = ImageDraw.Draw(base)
    tracked(d, (0, ty), title, f_title, ink, tracking=34, center_x=W / 2)

    # thin gold rule
    d.line([(W / 2 - 230, 596), (W / 2 + 230, 596)], fill=(150, 108, 62, 210), width=3)

    # tagline in the subtitle position
    f_tag = font(KAI, 64)
    tag = "他把一辈子的账，记在骨头里"
    tracked(d, (0, 620), tag, f_tag, brown, tracking=3, center_x=W / 2)

    # author
    f_author = font(SONG, 70)
    author = "江召兵 著"
    ax = W / 2
    ay = 2058

    def draw_author(dd):
        dd.text((ax - 170, ay), author, font=f_author, fill=(0, 0, 0, 255))

    base = shadow(base, draw_author, blur=10, alpha=180)
    d = ImageDraw.Draw(base)
    tracked(d, (0, ay), author, f_author, ivory, tracking=8, center_x=ax)

    # small vermilion seal at the right of the author line
    seal = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    sd = ImageDraw.Draw(seal)
    sd.rounded_rectangle([4, 4, 123, 123], radius=14, fill=(156, 38, 34, 235))
    f_seal = font(ZHONGSONG, 84)
    bb = sd.textbbox((0, 0), "账", font=f_seal)
    sw, sh = bb[2] - bb[0], bb[3] - bb[1]
    sd.text(((128 - sw) / 2 - bb[0], (128 - sh) / 2 - bb[1]), "账", font=f_seal, fill=(247, 236, 216, 245))
    base.alpha_composite(seal, (1292, 2028))

    cover = base.convert("RGB")
    cover.save(os.path.join(OUT, "cover.jpg"), quality=93, optimize=True, progressive=True)

    card = cover.resize((640, 960), Image.LANCZOS)
    card.save(os.path.join(OUT, "cover-card.jpg"), quality=92, optimize=True, progressive=True)

    preview = cover.resize((800, 1200), Image.LANCZOS)
    preview.save(os.path.join(OUT, "cover_preview.png"), optimize=True)

    print("saved", os.path.join(OUT, "cover.jpg"), cover.size)


if __name__ == "__main__":
    main()
