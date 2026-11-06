# -*- coding: utf-8 -*-
"""Compose the cover for 井水照人 from a Dreamina-generated colorful background.

Input: _tmp_cover_art/colorB.png (3328x4992, twilight village + well + moon)
Outputs (books/jingshui-zhaoren/):
  cover.jpg         1600x2400
  cover-card.jpg     640x960
  cover_preview.png  800x1200
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "_tmp_cover_art" / "colorB.png"
OUT = ROOT / "books" / "jingshui-zhaoren"
OUT.mkdir(parents=True, exist_ok=True)

W, H = 1600, 2400

FONT_DIR = Path(r"C:\Windows\Fonts")
TITLE_CANDIDATES = [
    FONT_DIR / "Source Han Serif SC Heavy (TrueType).ttf",
    FONT_DIR / "SourceHanSerifSC-Heavy.otf",
    FONT_DIR / "STSONG.TTF",
]
SERIF = FONT_DIR / "STSONG.TTF"
KAI = FONT_DIR / "STKAITI.TTF"


def pick_font(candidates, size):
    for p in candidates:
        if p.exists():
            return ImageFont.truetype(str(p), size)
    raise FileNotFoundError(candidates)


IVORY = (247, 241, 227)
WARM = (232, 222, 204)
GOLD = (198, 164, 104)
GOLD_SOFT = (198, 164, 104, 70)
MUTED = (206, 194, 172)
SEAL_RED = (150, 46, 40)


def fit(img: Image.Image, w: int, h: int) -> Image.Image:
    iw, ih = img.size
    scale = max(w / iw, h / ih)
    nw, nh = int(iw * scale + 0.5), int(ih * scale + 0.5)
    img = img.resize((nw, nh), Image.LANCZOS)
    left = (nw - w) // 2
    top = (nh - h) // 2
    return img.crop((left, top, left + w, top + h))


def vgrad(size, stops):
    w, h = size
    img = Image.new("RGBA", (w, h))
    px = img.load()
    stops = sorted(stops)
    for y in range(h):
        t = y / (h - 1)
        col = stops[-1][1]
        for i in range(len(stops) - 1):
            t0, c0 = stops[i]
            t1, c1 = stops[i + 1]
            if t0 <= t <= t1:
                k = 0 if t1 == t0 else (t - t0) / (t1 - t0)
                col = tuple(int(c0[j] + (c1[j] - c0[j]) * k) for j in range(4))
                break
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

    # 1. Top scrim: keep the indigo sky but deepen it behind the title.
    shade = vgrad((W, H), [
        (0.00, (12, 14, 30, 128)),
        (0.22, (14, 16, 30, 96)),
        (0.42, (16, 18, 30, 46)),
        (0.58, (10, 12, 20, 12)),
        (0.72, (6, 8, 12, 6)),
        (0.82, (6, 6, 10, 84)),
        (0.92, (4, 4, 8, 140)),
        (1.00, (3, 3, 6, 165)),
    ])
    base = Image.alpha_composite(base, shade)

    # 2. soft vignette (gentle, keeps the colors vivid)
    vign = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(vign)
    vd.ellipse((-int(W * 0.62), -int(H * 0.34), int(W * 1.62), int(H * 1.34)), fill=104)
    vign = vign.filter(ImageFilter.GaussianBlur(190))
    dark = Image.new("RGBA", (W, H), (5, 6, 9, 255))
    dark.putalpha(ImageEnhance.Brightness(vign).enhance(0.85))
    base = Image.alpha_composite(base, dark)

    draw = ImageDraw.Draw(base)

    # 3. thin double gold frame, inset from the trim edge
    frame = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(frame)
    fd.rectangle((40, 40, W - 40, H - 40), outline=GOLD_SOFT, width=2)
    fd.rectangle((54, 54, W - 54, H - 54), outline=(198, 164, 104, 42), width=1)
    base = Image.alpha_composite(base, frame)
    draw = ImageDraw.Draw(base)

    # 4. top label
    f_label = ImageFont.truetype(str(SERIF), 40)
    lab = "长 篇 小 说"
    lw = tracked_width(draw, lab, f_label, 18)
    draw_tracked(draw, ((W - lw) / 2, 250), lab, f_label, (216, 200, 170), 18)

    # 5. main title
    f_title = pick_font(TITLE_CANDIDATES, 306)
    title = "井水照人"
    tw = tracked_width(draw, title, f_title, 46)
    tx = (W - tw) / 2
    ty = 420
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    draw_tracked(sd, (tx + 5, ty + 12), title, f_title, (0, 0, 0, 185), 46)
    shadow = shadow.filter(ImageFilter.GaussianBlur(16))
    base = Image.alpha_composite(base, shadow)
    draw = ImageDraw.Draw(base)
    draw_tracked(draw, (tx, ty), title, f_title, IVORY, 46)

    # 6. gold rule with diamond
    ry = 892
    half = 310
    draw.line([(W / 2 - half, ry), (W / 2 - 18, ry)], fill=GOLD, width=3)
    draw.line([(W / 2 + 18, ry), (W / 2 + half, ry)], fill=GOLD, width=3)
    d = 10
    draw.polygon([(W / 2, ry - d), (W / 2 + d, ry), (W / 2, ry + d), (W / 2 - d, ry)], fill=GOLD)

    # 7. tagline
    f_tag = ImageFont.truetype(str(KAI), 60)
    tag = "井水照人，照见的是各人的心。"
    tagw = draw.textlength(tag, font=f_tag)
    draw.text(((W - tagw) / 2, 964), tag, font=f_tag, fill=WARM)

    # 8. author and imprint line (over a soft dark plate at the foot)
    plate = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(plate)
    pd.ellipse((250, 1940, W - 250, 2270), fill=(4, 6, 12, 120))
    plate = plate.filter(ImageFilter.GaussianBlur(70))
    base = Image.alpha_composite(base, plate)
    draw = ImageDraw.Draw(base)

    f_author = ImageFont.truetype(str(SERIF), 66)
    author = "江 召 兵  著"
    aw = tracked_width(draw, author, f_author, 12)
    ay = 2006
    ash = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ad = ImageDraw.Draw(ash)
    draw_tracked(ad, ((W - aw) / 2 + 3, ay + 5), author, f_author, (0, 0, 0, 200), 12)
    ash = ash.filter(ImageFilter.GaussianBlur(8))
    base = Image.alpha_composite(base, ash)
    draw = ImageDraw.Draw(base)
    draw_tracked(draw, ((W - aw) / 2, ay), author, f_author, IVORY, 12)

    f_line = ImageFont.truetype(str(SERIF), 32)
    line = "三卷四十章 · 一九八六—二〇二六"
    lw2 = tracked_width(draw, line, f_line, 6)
    lx = (W - lw2) / 2
    ly = 2116
    lsh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lsh)
    draw_tracked(ld, (lx + 2, ly + 4), line, f_line, (0, 0, 0, 190), 6)
    lsh = lsh.filter(ImageFilter.GaussianBlur(6))
    base = Image.alpha_composite(base, lsh)
    draw = ImageDraw.Draw(base)
    draw_tracked(draw, (lx, ly), line, f_line, (236, 226, 206), 6)

    # 9. red seal
    seal = Image.new("RGBA", (150, 150), (0, 0, 0, 0))
    sdd = ImageDraw.Draw(seal)
    sdd.rounded_rectangle((6, 6, 144, 144), radius=14, outline=SEAL_RED, width=7)
    sdd.rounded_rectangle((16, 16, 134, 134), radius=8, outline=SEAL_RED, width=2)
    f_seal = pick_font(TITLE_CANDIDATES, 82)
    cw = sdd.textlength("井", font=f_seal)
    sdd.text(((150 - cw) / 2, 30), "井", font=f_seal, fill=SEAL_RED)
    seal = seal.rotate(6, expand=True, resample=Image.BICUBIC)
    base.alpha_composite(seal, (1244, 2092))

    # 10. paper grain
    grain = Image.effect_noise((W, H), 7).convert("L")
    grain = ImageEnhance.Contrast(grain).enhance(0.55)
    noise = Image.new("RGBA", (W, H), (255, 255, 255, 0))
    noise.putalpha(grain.point(lambda v: int(v * 0.045)))
    base = Image.alpha_composite(base, noise)

    rgb = base.convert("RGB")
    rgb.save(OUT / "cover.jpg", "JPEG", quality=92, optimize=True)
    rgb.resize((640, 960), Image.LANCZOS).save(OUT / "cover-card.jpg", "JPEG", quality=90, optimize=True)
    rgb.resize((800, 1200), Image.LANCZOS).save(OUT / "cover_preview.png", "PNG", optimize=True)
    for p in ("cover.jpg", "cover-card.jpg", "cover_preview.png"):
        f = OUT / p
        print(p, f.stat().st_size)


if __name__ == "__main__":
    build()
