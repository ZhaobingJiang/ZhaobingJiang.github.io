# -*- coding: utf-8 -*-
"""Compose covers for 《井水照人》: dark ink water well with golden ripples."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT_DIR = Path(r"D:\deepseek-harness\OpatiyaAgent\JiangZhaobing.github.io\books\jingshui-zhaoren")
FONT_HEI = r"C:\Windows\Fonts\Source Han Serif SC Heavy (TrueType).ttf"
FONT_SONG = r"C:\Windows\Fonts\STSONG.TTF"
FONT_KAI = r"C:\Windows\Fonts\STKAITI.TTF"

W, H = 1600, 2400
IVORY = (240, 234, 220)
GOLD = (182, 148, 92)
MUTED = (168, 174, 170)


def lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def make_bg():
    top = (30, 44, 51)
    mid = (20, 31, 38)
    bottom = (9, 14, 18)
    img = Image.new("RGB", (W, H), bottom)
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / (H - 1)
        if t < 0.55:
            c = lerp(top, mid, t / 0.55)
        else:
            c = lerp(mid, bottom, (t - 0.55) / 0.45)
        d.line([(0, y), (W, y)], fill=c)
    return img


def vignette(img):
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([-W * 0.25, -H * 0.15, W * 1.25, H * 0.95], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(260))
    dark = Image.new("RGB", (W, H), (0, 0, 0))
    return Image.composite(img, dark, mask)


def ripples(img):
    """Concentric flattened ellipses, like rings on well water."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx, cy = W // 2, 1660
    rings = [(120, 34, 120), (220, 60, 100), (330, 88, 82), (450, 118, 64), (580, 150, 48),
             (720, 184, 34), (870, 220, 22)]
    for rx, ry, alpha in rings:
        d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], outline=(182, 148, 92, alpha), width=3)
    # still water reflection hint
    d.ellipse([cx - 90, cy - 24, cx + 90, cy + 24], outline=(240, 234, 220, 40), width=2)
    layer = layer.filter(ImageFilter.GaussianBlur(1.2))
    img = img.convert("RGBA")
    img.alpha_composite(layer)
    return img.convert("RGB")


def text_ls(img, xy, text, font, fill, ls):
    """Draw text with letter spacing; returns total width."""
    d = ImageDraw.Draw(img)
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill)
        bbox = d.textbbox((x, y), ch, font=font)
        x += (bbox[2] - bbox[0]) + ls
    return x


def centered_ls(img, cy, text, font, fill, ls):
    d = ImageDraw.Draw(img)
    width = 0
    for ch in text:
        bbox = d.textbbox((0, 0), ch, font=font)
        width += (bbox[2] - bbox[0]) + ls
    width -= ls
    text_ls(img, ((W - width) // 2, cy), text, font, fill, ls)
    return width


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    img = make_bg()
    img = ripples(img)
    img = vignette(img)

    f_label = ImageFont.truetype(FONT_SONG, 54)
    f_title = ImageFont.truetype(FONT_HEI, 312)
    f_tag = ImageFont.truetype(FONT_KAI, 64)
    f_author = ImageFont.truetype(FONT_SONG, 64)
    f_small = ImageFont.truetype(FONT_SONG, 38)

    # thin inner frame
    d = ImageDraw.Draw(img)
    d.rectangle([74, 74, W - 74, H - 74], outline=(182, 148, 92, 120), width=2)

    centered_ls(img, 250, "长 篇 小 说", f_label, MUTED, 18)

    # title
    title_y = 860
    centered_ls(img, title_y, "井水照人", f_title, IVORY, 46)

    # golden rule
    d = ImageDraw.Draw(img)
    d.line([(W // 2 - 190, 1290), (W // 2 + 190, 1290)], fill=(182, 148, 92), width=3)
    d.ellipse([W // 2 - 7, 1283, W // 2 + 7, 1297], fill=(182, 148, 92))

    centered_ls(img, 1350, "井水照人，照见的是各人的心。", f_tag, (222, 210, 188), 6)

    # author block
    centered_ls(img, 2080, "江 召 兵  著", f_author, IVORY, 10)
    centered_ls(img, 2200, "三卷四十章 · 一九八六—二〇二六", f_small, MUTED, 2)

    # seal
    seal = Image.new("RGBA", (150, 150), (0, 0, 0, 0))
    sd = ImageDraw.Draw(seal)
    sd.rectangle([6, 6, 144, 144], outline=(150, 62, 52, 235), width=6)
    f_seal = ImageFont.truetype(FONT_HEI, 92)
    bbox = sd.textbbox((0, 0), "井", font=f_seal)
    sd.text(((150 - (bbox[2] - bbox[0])) / 2 - bbox[0], (150 - (bbox[3] - bbox[1])) / 2 - bbox[1] + 6),
            "井", font=f_seal, fill=(150, 62, 52, 235))
    seal = seal.rotate(-6, expand=False, resample=Image.BICUBIC)
    img.paste(seal, (W - 250, H - 330), seal)

    img.save(OUT_DIR / "cover.jpg", quality=92)
    img.resize((640, 960), Image.LANCZOS).save(OUT_DIR / "cover-card.jpg", quality=90)
    img.resize((800, 1200), Image.LANCZOS).save(OUT_DIR / "cover_preview.png")
    print("saved", OUT_DIR)


if __name__ == "__main__":
    main()
