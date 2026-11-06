# -*- coding: utf-8 -*-
"""Compose the cover art for 井水照人 from a Dreamina-generated background.

Input: _tmp_cover_art/art2.png (3328x4992 ink-wash well and moon)
Outputs (books/jingshui-zhaoren/):
  cover.jpg         1600x2400
  cover-card.jpg     640x960
  cover_preview.png  800x1200
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "_tmp_cover_art" / "art2.png"
OUT = ROOT / "books" / "jingshui-zhaoren"
OUT.mkdir(parents=True, exist_ok=True)

W, H = 1600, 2400

FONT_TITLE = r"C:\Windows\Fonts\Source Han Serif SC Heavy (TrueType).ttf"
FONT_SERIF = r"C:\Windows\Fonts\STSONG.TTF"
FONT_KAI = r"C:\Windows\Fonts\STKAITI.TTF"

IVORY = (243, 236, 221)
GOLD = (196, 160, 96)
MUTED = (198, 186, 162)
SEAL_RED = (143, 45, 39)


def fit(img: Image.Image, w: int, h: int) -> Image.Image:
    iw, ih = img.size
    scale = max(w / iw, h / ih)
    nw, nh = int(iw * scale + 0.5), int(ih * scale + 0.5)
    img = img.resize((nw, nh), Image.LANCZOS)
    left = (nw - w) // 2
    top = (nh - h) // 2
    return img.crop((left, top, left + w, top + h))


def vgrad(size, stops):
    """Vertical gradient image from list of (t, rgba)."""
    w, h = size
    img = Image.new("RGBA", (w, h))
    px = img.load()
    stops = sorted(stops)
    for y in range(h):
        t = y / (h - 1)
        # find segment
        for i in range(len(stops) - 1):
            t0, c0 = stops[i]
            t1, c1 = stops[i + 1]
            if t0 <= t <= t1:
                k = 0 if t1 == t0 else (t - t0) / (t1 - t0)
                col = tuple(int(c0[j] + (c1[j] - c0[j]) * k) for j in range(4))
                break
        else:
            col = stops[-1][1]
        for x in range(w):
            px[x, y] = col
    return img


def draw_tracked(draw: ImageDraw.ImageDraw, xy, text, font, fill, tracking=0):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + tracking
    return x


def tracked_width(draw, text, font, tracking):
    return sum(draw.textlength(ch, font=font) for ch in text) + tracking * (len(text) - 1)


def build():
    art = Image.open(ART).convert("RGB")
    base = fit(art, W, H).convert("RGBA")

    # 1. deepen the sky at the top so ivory typography stays legible
    shade = vgrad((W, H), [
        (0.00, (14, 17, 20, 150)),
        (0.28, (18, 21, 24, 108)),
        (0.52, (20, 24, 27, 44)),
        (0.68, (12, 15, 18, 10)),
        (1.00, (8, 10, 12, 26)),
    ])
    base = Image.alpha_composite(base, shade)

    # 2. soft vignette
    vign = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(vign)
    vd.ellipse((-int(W * 0.55), -int(H * 0.30), int(W * 1.55), int(H * 1.30)), fill=120)
    vign = vign.filter(ImageFilter.GaussianBlur(180))
    dark = Image.new("RGBA", (W, H), (6, 8, 10, 255))
    dark.putalpha(ImageEnhance.Brightness(vign).enhance(0.9))
    base = Image.alpha_composite(base, dark)

    draw = ImageDraw.Draw(base)

    # 3. top label
    f_label = ImageFont.truetype(FONT_SERIF, 40)
    lab = "长 篇 小 说"
    lw = tracked_width(draw, lab, f_label, 18)
    draw_tracked(draw, ((W - lw) / 2, 258), lab, f_label, (208, 194, 168), 18)

    # 4. main title
    f_title = ImageFont.truetype(FONT_TITLE, 306)
    title = "井水照人"
    tw = tracked_width(draw, title, f_title, 46)
    tx = (W - tw) / 2
    ty = 430
    # soft shadow first
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    draw_tracked(sd, (tx + 6, ty + 10), title, f_title, (0, 0, 0, 170), 46)
    shadow = shadow.filter(ImageFilter.GaussianBlur(14))
    base = Image.alpha_composite(base, shadow)
    draw = ImageDraw.Draw(base)
    draw_tracked(draw, (tx, ty), title, f_title, IVORY, 46)

    # 5. gold rule with a small diamond
    ry = 900
    half = 300
    draw.line([(W / 2 - half, ry), (W / 2 - 16, ry)], fill=GOLD, width=3)
    draw.line([(W / 2 + 16, ry), (W / 2 + half, ry)], fill=GOLD, width=3)
    d = 9
    draw.polygon([(W / 2, ry - d), (W / 2 + d, ry), (W / 2, ry + d), (W / 2 - d, ry)], fill=GOLD)

    # 6. tagline
    f_tag = ImageFont.truetype(FONT_KAI, 60)
    tag = "井水照人，照见的是各人的心。"
    tagw = draw.textlength(tag, font=f_tag)
    draw.text(((W - tagw) / 2, 972), tag, font=f_tag, fill=(232, 222, 204))

    # 7. author and book line
    f_author = ImageFont.truetype(FONT_SERIF, 66)
    author = "江 召 兵  著"
    aw = tracked_width(draw, author, f_author, 12)
    ay = 2052
    draw_tracked(draw, ((W - aw) / 2, ay), author, f_author, IVORY, 12)

    f_line = ImageFont.truetype(FONT_SERIF, 32)
    line = "三卷四十章 · 一九八六—二〇二六"
    lw2 = tracked_width(draw, line, f_line, 6)
    draw_tracked(draw, ((W - lw2) / 2, 2160), line, f_line, MUTED, 6)

    # 8. red seal, slightly rotated, right of the author line
    seal = Image.new("RGBA", (150, 150), (0, 0, 0, 0))
    sdd = ImageDraw.Draw(seal)
    sdd.rounded_rectangle((6, 6, 144, 144), radius=14, outline=SEAL_RED, width=7)
    sdd.rounded_rectangle((16, 16, 134, 134), radius=8, outline=SEAL_RED, width=2)
    f_seal = ImageFont.truetype(FONT_TITLE, 82)
    cw = sdd.textlength("井", font=f_seal)
    sdd.text(((150 - cw) / 2, 30), "井", font=f_seal, fill=SEAL_RED)
    seal = seal.rotate(6, expand=True, resample=Image.BICUBIC)
    base.alpha_composite(seal, (1258, 2100))

    # 9. subtle paper grain
    grain = Image.effect_noise((W, H), 8).convert("L").resize((W, H))
    grain = ImageEnhance.Contrast(grain).enhance(0.6)
    noise = Image.new("RGBA", (W, H), (255, 255, 255, 0))
    noise.putalpha(grain.point(lambda v: int(v * 0.05)))
    base = Image.alpha_composite(base, noise)

    rgb = base.convert("RGB")
    rgb.save(OUT / "cover.jpg", "JPEG", quality=92, optimize=True)
    card = rgb.resize((640, 960), Image.LANCZOS)
    card.save(OUT / "cover-card.jpg", "JPEG", quality=90, optimize=True)
    prev = rgb.resize((800, 1200), Image.LANCZOS)
    prev.save(OUT / "cover_preview.png", "PNG", optimize=True)
    for p in ("cover.jpg", "cover-card.jpg", "cover_preview.png"):
        f = OUT / p
        print(p, f.stat().st_size)


if __name__ == "__main__":
    build()
