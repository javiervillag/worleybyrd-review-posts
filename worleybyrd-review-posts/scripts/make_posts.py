#!/usr/bin/env python3
"""Make Instagram review posts (1080x1350 PNG) + captions + approval sheet.

Needs only Python 3 and Pillow (`pip install pillow`). Fonts are bundled in ./fonts.

  python3 make_posts.py --folder "<business folder>" reviews.json [--template auto|bubble|hero]
                        [--carousel off|long-only|always] [--include-seen]

<business folder> holds settings.json, the logo file and a photos/ folder.
reviews.json is a list of:
  {"source": "Google", "name": "Sam P.", "date": "Jul 2026",
   "quote": "full review, word for word",
   "excerpt": "optional: best sentences, word for word (used for short/teaser slides)",
   "hl": "optional: short phrase to highlight, word for word",
   "edits": [{"from": "REMOVED and REMOVED", "to": "Two reps"}],   # only for names the site blurred (BBB)
   "caption": "post caption",
   "photo": "optional: photo the reviewer posted with the review (path inside the business folder);
             used as this post's background instead of the rotation"}
Output: <business folder>/posts/<date>/ with PNGs, captions.md, approval.csv
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
except ImportError:
    sys.exit("Pillow is missing. Run: pip install pillow")

HERE = Path(__file__).resolve().parent
FONTS = HERE / "fonts"
W, H = 1080, 1350
PHOTO_EXT = {".jpg", ".jpeg", ".png", ".webp"}
DEFAULT_COLORS = {"dark": "#0c3455", "darker": "#071f35", "accent": "#cb972b", "accent_light": "#e2b04a"}


# ---------------------------------------------------------------- fonts
def font(name: str, size: int, weight: int | None = None) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(str(FONTS / name), size)
    if weight is not None:
        try:
            f.set_variation_by_axes([weight])
        except Exception:
            pass
    return f


def serif(size, italic=False, weight=400):
    return font("PlayfairDisplay-Italic.ttf" if italic else "PlayfairDisplay.ttf", size, weight)


def sans(size, style="Regular"):
    return font(f"Poppins-{style}.ttf", size)


def label_font(size, weight=700):
    return font("Raleway.ttf", size, weight)


# ---------------------------------------------------------------- helpers
def rgb(hex_: str, a: int = 255):
    h = hex_.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def words(s: str) -> int:
    return len(s.split())


def cover(photo: Path, focus: str) -> Image.Image:
    img = ImageOps.exif_transpose(Image.open(photo)).convert("RGB")
    fx, fy = (float(v.strip().rstrip("%")) / 100 for v in (focus or "50% 50%").split()[:2])
    scale = max(W / img.width, H / img.height)
    img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
    left, top = round((img.width - W) * fx), round((img.height - H) * fy)
    return img.crop((left, top, left + W, top + H)).convert("RGBA")


def vgradient(stops: list[tuple[float, int]], color: str) -> Image.Image:
    """Vertical overlay; stops = [(y fraction 0..1 from top, alpha 0..255)]."""
    col = Image.new("L", (1, H))
    px = col.load()
    for y in range(H):
        t = y / (H - 1)
        for (t0, a0), (t1, a1) in zip(stops, stops[1:]):
            if t0 <= t <= t1:
                px[0, y] = round(a0 + (a1 - a0) * ((t - t0) / (t1 - t0) if t1 > t0 else 0))
                break
        else:
            px[0, y] = stops[0][1] if t < stops[0][0] else stops[-1][1]
    over = Image.new("RGBA", (W, H), rgb(color))
    over.putalpha(col.resize((W, H)))
    return over


def logo_on_dark(path: Path) -> Image.Image:
    """White version of the logo for dark backgrounds (works with transparent or white-background logos)."""
    img = Image.open(path).convert("RGBA")
    alpha = img.getchannel("A")
    if alpha.getextrema() == (255, 255):  # no transparency: treat light pixels as background
        lum = img.convert("L")
        alpha = lum.point(lambda v: 0 if v > 235 else min(255, (235 - v) * 3))
    white = Image.new("RGBA", img.size, (255, 255, 255, 255))
    white.putalpha(alpha)
    bbox = alpha.getbbox()
    return white.crop(bbox) if bbox else white


def paste_h(base: Image.Image, img: Image.Image, height: int, xy: tuple[int, int], anchor="lt"):
    im = img.resize((max(1, round(img.width * height / img.height)), height), Image.LANCZOS)
    x, y = xy
    if anchor[0] == "m":
        x -= im.width // 2
    if anchor[0] == "r":
        x -= im.width
    base.alpha_composite(im, (x, y))
    return im.width


def star(draw: ImageDraw.ImageDraw, cx: float, cy: float, r: float, fill):
    import math
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rad = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    draw.polygon(pts, fill=fill)


def stars(draw, x, y, size, fill, gap=6):
    for i in range(5):
        star(draw, x + size / 2 + i * (size + gap), y + size / 2, size / 2, fill)
    return 5 * size + 4 * gap


def _digit_font(fnt):
    """Raleway's default digits are old-style (the 5 drops below the line); use Poppins digits instead."""
    return sans(round(fnt.size * 0.98), "SemiBold") if "Raleway" in fnt.getname()[0] else fnt


def spaced(draw, xy, text, fnt, fill, spacing):
    x, y = xy
    dfont = _digit_font(fnt)
    base = y + fnt.getbbox("H")[3]  # align digit baseline with letters
    for ch in text:
        if ch.isdigit() and dfont is not fnt:
            draw.text((x, base), ch, font=dfont, fill=fill, anchor="ls")
            x += dfont.getlength(ch) + spacing
        else:
            draw.text((x, y), ch, font=fnt, fill=fill)
            x += fnt.getlength(ch) + spacing
    return x - xy[0] - spacing


def spaced_len(text, fnt, spacing):
    dfont = _digit_font(fnt)
    return sum((dfont if c.isdigit() else fnt).getlength(c) for c in text) + spacing * (len(text) - 1)


# ---------------------------------------------------------------- rich text (one highlighted phrase)
def tokens(text: str, hl: str):
    """[(piece, is_highlight, joins_previous)]. A word half inside the highlight is split
    into two pieces with no space between, so 'cleanup.' stays together on one line."""
    start = text.find(hl) if hl else -1
    end = start + len(hl) if start >= 0 else -1
    out = []
    for m in re.finditer(r"\S+", text):
        a, b = m.start(), m.end()
        if start < 0 or b <= start or a >= end:
            out.append((m.group(), False, False))
            continue
        cuts = sorted({a, b, max(a, start), min(b, end)})
        first = True
        for x, y in zip(cuts, cuts[1:]):
            out.append((text[x:y], start <= x < end, not first))
            first = False
    return out


def layout_lines(toks, fonts, width):
    """Wrap; pieces that join the previous one move with it."""
    groups, cur = [], []
    for tok in toks:
        if cur and not tok[2]:
            groups.append(cur)
            cur = []
        cur.append(tok)
    if cur:
        groups.append(cur)
    lines, line, lw = [], [], 0.0
    for g in groups:
        gw = sum(fonts[f].getlength(w_) for w_, f, _ in g)
        sp = fonts[g[0][1]].getlength(" ") if line else 0
        if line and lw + sp + gw > width:
            lines.append(line)
            line, lw, sp = [], 0.0, 0
        line.extend(g)
        lw += sp + gw
    if line:
        lines.append(line)
    return lines


def ellipsize(s: str) -> str:
    return re.sub(r"\.+$", "…", s) if s.endswith(".") else s + " …"


def fit_text(text, hl, make_fonts, width, max_h, size_max, size_min, lh):
    """Shrink until it fits; at the minimum size keep whole sentences + ellipsis."""
    for size in range(size_max, size_min - 1, -1):
        fonts = make_fonts(size)
        lines = layout_lines(tokens(text, hl), fonts, width)
        if len(lines) * size * lh <= max_h:
            return lines, fonts, size
    sents = re.findall(r"[^.!?]+[.!?]+[\"')\]]*\s*|[^.!?]+$", text) or [text]
    kept = ""
    fonts = make_fonts(size_min)
    best = layout_lines(tokens(ellipsize(sents[0].strip()), hl), fonts, width)
    for s in sents:
        trial = ellipsize((kept + s).strip())
        lines = layout_lines(tokens(trial, hl), fonts, width)
        if len(lines) * size_min * lh > max_h:
            break
        kept += s
        best = lines
    return best, fonts, size_min


def draw_lines(draw, lines, fonts, x, y, size, lh, colors, align="left", width=0):
    for line in lines:
        lx = x
        for i, (w_, f, join) in enumerate(line):
            if i and not join:
                lx += fonts[f].getlength(" ")
            draw.text((lx, y), w_, font=fonts[f], fill=colors[f])
            lx += fonts[f].getlength(w_)
        y += size * lh
    return y


# ---------------------------------------------------------------- layouts
def hero(bg, logo_white, c, r, swipe=""):
    img = bg.copy()
    img.alpha_composite(vgradient([(0, 0), (0.24, 0), (0.38, 89), (0.66, 240), (1, 255)], c["darker"]))
    img.alpha_composite(vgradient([(0, 190), (0.26, 0), (1, 0)], c["darker"]))
    if logo_white is not None:
        paste_h(img, logo_white, 140, (W // 2, 64), "mt")
    d = ImageDraw.Draw(img)
    side = 104
    lines, fonts, size = fit_text(r["quote"], r.get("hl", ""), lambda s: {False: serif(s), True: serif(s, italic=True)},
                                  W - 2 * side, 360, 60, 40, 1.22)
    block_h = len(lines) * size * 1.22
    top = 780 + (360 - block_h) / 2
    sw = stars(d, side, top - 70, 30, rgb(c["accent_light"]))
    spaced(d, (side + sw + 20, top - 70 + 3), f"{r.get('source', 'Google')} Review".upper(), label_font(23), rgb(c["accent_light"]), 5)
    draw_lines(d, lines, fonts, side, top, size, 1.22, {False: (255, 255, 255, 255), True: rgb(c["accent_light"])})
    d.rectangle((side, 1180, side + 90, 1183), fill=rgb(c["accent"]))
    spaced(d, (side, 1205), (r.get("name") or r["_fallback"]).upper(), label_font(26), (255, 255, 255, 255), 4)
    d.text((side, 1245), r["_srcline"], font=sans(22, "Light"), fill=(255, 255, 255, 190))
    if swipe:
        t = swipe.upper()
        f = label_font(21, 600)
        col = rgb(c["accent_light"])
        x_end = W - side
        spaced(d, (x_end - 44 - spaced_len(t, f, 3), 1212), t, f, col, 3)
        ay = 1224  # drawn arrow (fonts may lack the arrow glyph)
        d.line((x_end - 30, ay, x_end - 4, ay), fill=col, width=3)
        d.polygon([(x_end + 2, ay), (x_end - 10, ay - 8), (x_end - 10, ay + 8)], fill=col)
    return img


def bubble(bg, logo_white, c, r, title):
    img = bg.copy()
    img.alpha_composite(vgradient([(0, 0), (0.38, 0), (0.62, 140), (0.86, 245), (1, 255)], c["darker"]))
    side, pad = 110, 60
    inner_w = W - 2 * side - 2 * pad
    lines, fonts, size = fit_text(r["quote"], r.get("hl", ""), lambda s: {False: sans(s), True: sans(s, "SemiBold")},
                                  inner_w, 470, 34, 27, 1.5)
    text_h = len(lines) * size * 1.5
    box_top, box_h = 110, 56 + 84 + 30 + text_h + 56
    box = (side, box_top, W - side, box_top + box_h)
    # shadow
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((box[0], box[1] + 24, box[2], box[3] + 24), 8, fill=rgb(c["darker"], 110))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(28)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(box, 6, fill=(255, 255, 255, 255))
    d.polygon([(side + 90, box[3] - 1), (side + 186, box[3] - 1), (side + 90, box[3] + 78)], fill=(255, 255, 255, 255))
    ax, ay = side + pad, box_top + 56
    d.ellipse((ax, ay, ax + 84, ay + 84), fill=rgb(c["dark"]))
    name = r.get("name") or r["_fallback"]
    d.text((ax + 42, ay + 44), name.strip()[0].upper(), font=sans(40, "SemiBold"), fill=rgb(c["accent_light"]), anchor="mm")
    nx = ax + 84 + 24
    d.text((nx, ay + 2), name, font=sans(30, "SemiBold"), fill=(29, 39, 51, 255))
    sw = stars(d, nx, ay + 46, 30, rgb(c["accent"]), 5)
    d.text((nx + sw + 16, ay + 49), r["_srcline"], font=sans(20), fill=(74, 85, 99, 255))
    draw_lines(d, lines, fonts, ax, ay + 84 + 30, size, 1.5, {False: (29, 39, 51, 255), True: rgb(c["dark"])})
    spaced(d, (side, 1150), f"5-star {r.get('source', 'Google')} review".upper(), label_font(25), rgb(c["accent_light"]), 5)
    d.text((side, 1190), title, font=serif(64, weight=500), fill=(255, 255, 255, 255))
    if logo_white is not None:
        paste_h(img, logo_white, 140, (W - 100, H - 80 - 140), "rt")
    return img


# ---------------------------------------------------------------- batch
def review_key(r):
    base = f"{r.get('source', '')}|{r.get('name', '')}|{re.sub(r'\s+', ' ', r['quote'].strip())[:80]}"
    return hashlib.sha1(base.lower().encode()).hexdigest()[:16]


def apply_edits(r):
    edits = r.get("edits") or []
    for e in edits:
        if (not e["to"].strip() and re.search(r"[A-Za-z]", e["from"])) or re.search(r"[A-Z][a-z]+ [A-Z][a-z]+", e["to"]):
            sys.exit(f"Edit '{e['to']}': use a plain role word (e.g. 'Two reps', 'The crew lead'), never a guessed name.")
        if e["from"] not in r["quote"]:
            sys.exit(f"'{e['from']}' is not in the review text.")
    r = dict(r)
    for fld in ("quote", "excerpt", "hl"):
        if r.get(fld):
            for e in edits:
                r[fld] = r[fld].replace(e["from"], e["to"].strip())
            r[fld] = re.sub(r"\s+([,.!?])", r"\1", re.sub(r"\s{2,}", " ", r[fld])).strip()
    return r


def mix_order(paths):
    """Spread similar photos apart: alternate between name groups (city-..., dji-...) instead of A-Z."""
    groups = {}
    for p in sorted(paths):
        key = p.stem.split("-")[0]
        groups.setdefault(key, []).append(p)
    out, queues = [], [g for _, g in sorted(groups.items())]
    while any(queues):
        for q in queues:
            if q:
                out.append(q.pop(0))
    return out


def first_sentences(text, limit):
    sents = re.findall(r"[^.!?]+[.!?]+[\"')\]]*\s*|[^.!?]+$", text) or [text]
    out = ""
    for s in sents:
        if out and words(out + s) > limit:
            break
        out += s
    return out.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reviews")
    ap.add_argument("--folder", required=True, help="business folder with settings.json, logo and photos/")
    ap.add_argument("--template", choices=["auto", "bubble", "hero"])
    ap.add_argument("--carousel", choices=["off", "long-only", "always"])
    ap.add_argument("--include-seen", action="store_true")
    a = ap.parse_args()

    folder = Path(a.folder).expanduser()
    cfg = json.loads((folder / "settings.json").read_text())
    c = {**DEFAULT_COLORS, **cfg.get("colors", {})}
    template = a.template or cfg.get("template", "auto")
    carousel = a.carousel or cfg.get("carousel", "long-only")
    short = int(cfg.get("short_quote_words", 32))
    long_words = int(cfg.get("carousel_min_words", 70))  # only really long reviews become 2-slide carousels
    brand = cfg.get("business_name", "")

    logo_path = folder / cfg.get("logo", "logo.png")
    logo_white = logo_on_dark(logo_path) if logo_path.is_file() else None
    pdir = folder / cfg.get("photos_folder", "photos")
    photos = mix_order(p for p in pdir.glob("*") if p.suffix.lower() in PHOTO_EXT) if pdir.exists() else []  # top level only; review photos live in photos/from-reviews/
    focus = cfg.get("photo_focus", {})
    rot_file, seen_file = folder / ".photo-rotation", folder / "seen.json"
    rot = int(rot_file.read_text()) if rot_file.exists() else 0
    seen = json.loads(seen_file.read_text()) if seen_file.exists() else {}

    out = folder / "posts" / dt.date.today().isoformat()
    out.mkdir(parents=True, exist_ok=True)
    rows, md, skipped, n = [], [f"# {brand} review posts, {dt.date.today():%d %b %Y}\n"], [], 0

    for raw in json.loads(Path(a.reviews).read_text()):
        key = review_key(raw)
        if key in seen and not a.include_seen:
            skipped.append(raw.get("name") or "a review")
            continue
        for fld in ("excerpt", "hl"):
            if raw.get(fld) and raw[fld] not in raw["quote"]:
                sys.exit(f"{raw.get('name')}: '{fld}' must be copied word for word from the review.")
        r = apply_edits(raw)
        edit_note = "; ".join(f"'{e['from']}' -> '{e['to']}'" for e in raw.get("edits") or [])
        r["_fallback"] = f"{brand} customer" if brand else "Happy customer"
        r["_srcline"] = "Posted on " + r.get("source", "Google")  # date stays in the approval sheet, not on the image
        n += 1
        own = folder / r["photo"] if r.get("photo") else None
        if own and own.is_file():  # the reviewer's own photo of the job beats any stock rotation
            bg = cover(own, r.get("photo_focus", "50% 50%"))
        elif photos:
            p = photos[rot % len(photos)]
            bg = cover(p, focus.get(p.name, "50% 50%"))
            rot += 1
        else:  # no photos yet: plain brand background
            bg = Image.new("RGBA", (W, H), rgb(c["dark"]))
        slug = re.sub(r"[^a-z0-9]+", "-", (r.get("name") or f"review-{n}").lower()).strip("-")
        is_long = words(r["quote"]) > long_words
        shown = r.get("excerpt") or r["quote"]
        slides = []
        if carousel == "always" or (carousel == "long-only" and is_long):
            teaser = r.get("excerpt") or first_sentences(r["quote"], short)
            slides.append(hero(bg, logo_white, c, {**r, "quote": teaser, "hl": r.get("hl", "") if r.get("hl", "") in teaser else ""},
                               cfg.get("swipe_text", "")))
            slides.append(bubble(bg, logo_white, c, r, cfg.get("bubble_title", "Client Review")))
        else:
            pick = template if template != "auto" else ("hero" if words(shown) <= short else "bubble")
            rr = {**r, "quote": shown}
            slides.append(hero(bg, logo_white, c, rr) if pick == "hero" else bubble(bg, logo_white, c, rr, cfg.get("bubble_title", "Client Review")))
        files = []
        for i, im in enumerate(slides, 1):
            name = f"{n:02d}-{slug}{'-' + str(i) if len(slides) > 1 else ''}.png"
            im.convert("RGB").save(out / name, optimize=True)
            files.append(name)
            print(out / name)
        kind = "Carousel" if len(files) > 1 else "Single image"
        cap = r.get("caption", "").strip()
        md.append(f"## {n:02d}. {r.get('name') or 'Customer'} ({r.get('source', 'Google')}{', ' + r['date'] if r.get('date') else ''})\n"
                  f"{kind}: {', '.join(files)}\n\n" + (f"**Edited:** {edit_note} (the review site hid these names)\n\n" if edit_note else "") + f"**Caption**\n\n{cap or '(no caption yet)'}\n\n**Full review**\n\n> {r['quote']}\n")
        rows.append({"post": n, "files": " ".join(files), "type": kind, "source": r.get("source", "Google"),
                     "reviewer": r.get("name", ""), "date": r.get("date", ""), "review": r["quote"], "caption": cap,
                     "edits (blurred names replaced)": edit_note, "approve (Y/N)": "", "posted (date)": ""})
        seen[key] = {"name": r.get("name", ""), "source": r.get("source", ""), "made": dt.date.today().isoformat()}

    if photos:
        rot_file.write_text(str(rot % len(photos)))
    seen_file.write_text(json.dumps(seen, indent=2) + "\n")
    if rows:
        (out / "captions.md").write_text("\n".join(md))
        with (out / "approval.csv").open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
    print(f"\nDONE: {len(rows)} post(s) in {out}")
    if skipped:
        print(f"Skipped {len(skipped)} already made before: {', '.join(skipped)}")
    if not photos:
        print("NOTE: no photos found, so a plain brand background was used. Add house photos to the photos folder.")
    if logo_white is None:
        print("NOTE: no logo found. Add the logo file and set its name in settings.json.")


if __name__ == "__main__":
    main()
