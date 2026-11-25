#!/usr/bin/env python3
"""THE WORLD — front page for Wednesday 25 November 2026.

Draws a 1024x1024 broadsheet PNG summing up the day's world news.
Illustrated panels are AI-generated images (gpt-image-2, Mode B); ALL text
is composited here in code with Pillow. No network, no fonts beyond DejaVu.

Layout (1024x1024, margins 14):
  masthead / subline / UTC timeline / 3 illustrated leads /
  numbers strip / cards 4-13 (10 illustrated) / map + regions + DATE CHECK /
  briefs 14-35 / source legend + footer.
35 stories, 7 regions, 9 fields. Every story happened or was first reported
on Wednesday 25 November 2026 (verified twice against wire reporting).
"""
import hashlib
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")

W, H = 1024, 1024
MARGIN = 14
PAPER = (247, 243, 232)
INK = (20, 20, 20)
RULE = (20, 20, 20)
RED = (176, 30, 36)
NAVY = (28, 47, 74)
GREY = (90, 88, 80)
LIGHT = (238, 233, 220)
TAG_COLORS = {
    "CONFIRMED": (27, 94, 32),
    "OFFICIAL": (21, 71, 140),
    "REPORTED": (146, 94, 0),
    "FORECAST": (106, 27, 154),
}

FONT_DIR = "/usr/share/fonts/truetype/dejavu"


def font(name, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size)


F_SERIF = lambda s: font("DejaVuSerif-Bold.ttf", s)
F_BOLD = lambda s: font("DejaVuSans-Bold.ttf", s)
F_REG = lambda s: font("DejaVuSans.ttf", s)


def text_w(draw, text, fnt):
    return draw.textlength(text, font=fnt)


def wrap(draw, text, fnt, max_w):
    """Greedy word wrap to a pixel width; returns list of lines."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if text_w(draw, trial, fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_tag(draw, x, y, tag, source, fnt):
    """Small coloured tag pill + source, returns width used."""
    color = TAG_COLORS[tag]
    tw = int(text_w(draw, tag, fnt)) + 8
    th = 13
    draw.rounded_rectangle([x, y, x + tw, y + th], radius=3, fill=color)
    draw.text((x + 4, y + 1), tag, font=fnt, fill=(255, 255, 255))
    draw.text((x + tw + 5, y + 1), source, font=fnt, fill=GREY)
    return tw + 5 + int(text_w(draw, source, fnt))


def crop_band(img, box, target_w, target_h, focus=0.45):
    """Crop box region to the target aspect (cover-style: scale the region so
    it fully covers the target, then centre-crop). Never pads with black."""
    x0, y0, x1, y1 = box
    region = img.crop((x0, y0, x1, y1))
    w, h = region.size
    scale = max(target_w / w, target_h / h)
    region = region.resize((max(1, round(w * scale)), max(1, round(h * scale))),
                           Image.LANCZOS)
    rw, rh = region.size
    cx, cy = rw // 2, int(rh * focus)
    left = max(0, min(rw - target_w, cx - target_w // 2))
    top = max(0, min(rh - target_h, cy - target_h // 2))
    return region.crop((left, top, left + target_w, top + target_h))


def load_panels():
    """Crop the generated contact sheets into individual panels."""
    tri = Image.open(os.path.join(ASSETS, "media-generation-leads-triptych-0-afab5270-97e6-413a-aca1-33b3fb6afa76.png")).convert("RGB")
    g6 = Image.open(os.path.join(ASSETS, "media-generation-cards-grid-6-0-d9845c57-8944-4650-9a05-a6fb59f5e6fd.png")).convert("RGB")
    g4 = Image.open(os.path.join(ASSETS, "media-generation-cards-grid-4-0-bace3888-5d1a-4299-b2dd-18df557d5af2.png")).convert("RGB")
    m = Image.open(os.path.join(ASSETS, "media-generation-world-map-base-0-be60dc01-6541-4f55-9f3c-36d55a3b6173.png")).convert("RGB")
    leads = [
        tri.crop((34, 35, 900, 878)),
        tri.crop((934, 35, 1802, 878)),
        tri.crop((1836, 35, 2703, 878)),
    ]
    xs6 = [(36, 633), (660, 1260), (1287, 1885)]
    ys6 = [(36, 632), (661, 1244)]
    cards6 = [g6.crop((x0, y0, x1, y1)) for y0, y1 in ys6 for x0, x1 in xs6]
    xs4 = [(77, 781), (818, 1523)]
    ys4 = [(74, 791), (825, 1526)]
    cards4 = [g4.crop((x0, y0, x1, y1)) for y0, y1 in ys4 for x0, x1 in xs4]
    smalls = cards6 + cards4  # 10 small illustrations, in grid order
    # Map: crop the ocean bbox (parchment border removed), keep natural aspect.
    ocean = m.crop((96, 96, 1821, 1155))
    return leads, smalls, ocean


# ---------------------------------------------------------------- stories
# (number, headline, body, tag, source, region, field)
LEADS = [
    (1, "TANKERS ABLAZE IN HORMUZ",
     "Iran's Revolutionary Guard says two oil tankers struck naval mines and "
     "caught fire in the Strait of Hormuz. Houthis say they hit Saudi "
     "Arabia's Ras Tanura refinery.",
     "REPORTED", "IRGC / Reuters", "Middle East", "Conflict"),
    (2, "PAKISTAN'S FIRST ASTRONAUT",
     "Shenzhou-24 lifts off at 00:18 UTC and docks with Tiangong at 03:56 UTC. "
     "Pakistan's Muhammad Zeeshan Ali is the first foreign astronaut aboard "
     "China's space station.",
     "CONFIRMED", "CMSA / Xinhua", "Asia", "Space"),
    (3, "TRUMP'S NEW TARIFFS",
     "Washington proposes tariffs of up to 40% on 14 partners \u2014 20% on China, "
     "15% on the EU \u2014 after an eight-month probe. A hearing is set for 25 January.",
     "OFFICIAL", "USTR", "North America", "Diplomacy"),
]

# (number, headline, body, tag, source, region, field, small-panel index)
CARDS = [
    (4, "AIR BASE HIT",
     "Ukraine strikes Savasleyka air base, damaging five planes: "
     "three MiG-31 jets and two Su-34 bombers.",
     "REPORTED", "Ukraine Gen. Staff", "Europe", "Conflict", 0),
    (5, "REFINERIES BURN",
     "Drones set two Rosneft refineries ablaze in Samara; "
     "one person killed, 145 drones downed.",
     "REPORTED", "Kyiv Independent", "Europe", "Conflict", 1),
    (6, "GAZA STRIKE",
     "Israeli strike kills a family of four in Al-Shati camp; "
     "the UN cites \u201catrocity crimes\u201d.",
     "CONFIRMED", "QNA / UN", "Middle East", "Conflict", 2),
    (7, "SUDAN KILLINGS",
     "RSF drone strikes kill 19 civilians and wound 20 in Sudan's Blue Nile state.",
     "REPORTED", "Emergency Lawyers", "Africa", "Conflict", 3),
    (8, "MARKETS TUMBLE",
     "Asia's stocks plunge: KOSPI \u22126.16%, Nikkei \u22122.78%, Taiex about \u22125%; "
     "the US inflation gauge hits 3.8%.",
     "CONFIRMED", "Reuters", "Asia", "Markets", 4),
    (9, "CHAMPIONS LEAGUE",
     "Liverpool win 3\u20130 at Brugge; Barcelona hit four; PSG and Roma share "
     "a 2\u20132 thriller in Paris.",
     "CONFIRMED", "UEFA", "Europe", "Sport", 5),
    (10, "CHESS DRAW",
     "Gukesh and Sindarov draw World Championship Game 2 in 20 moves; "
     "the match is level at 1\u20131 in Geneva.",
     "CONFIRMED", "FIDE", "Europe", "Sport", 6),
    (11, "LILLE STUN BAYERN",
     "Lille beat Bayern Munich 2\u20131 in the Champions League; Bayern, missing "
     "Kane, lose their first group game.",
     "CONFIRMED", "UEFA", "Europe", "Sport", 5, 0.75),
    (12, "FLORIDA FLOODS",
     "Rain returns to flooded Florida; the St. Johns River stays in major "
     "flood as Thanksgiving nears.",
     "REPORTED", "NWS", "North America", "Weather", 8),
    (13, "MINERS TRAPPED",
     "The Bogor gold-mine toll rises to six; around 20 miners are still "
     "trapped in a flooded shaft.",
     "CONFIRMED", "Indonesian officials", "Asia", "Health", 9),
]

# (number, headline, tag, source, region, field)
BRIEFS = [
    (14, "Houthis hit Ras Tanura refinery", "REPORTED", "Houthi spox", "Middle East", "Conflict"),
    (15, "Russian strike halts DTEK power plant", "REPORTED", "DTEK", "Europe", "Conflict"),
    (16, "Overnight strike kills two in Odesa", "REPORTED", "Gov. Kiper", "Europe", "Conflict"),
    (17, "Norway pledges $7bn to Ukraine in 2027", "OFFICIAL", "Oslo", "Europe", "Diplomacy"),
    (18, "Poland seeks permanent US base", "REPORTED", "Warsaw", "Europe", "Diplomacy"),
    (19, "Merz defends Ukraine aid in Berlin", "REPORTED", "Bundestag", "Europe", "Politics"),
    (20, "UK warns firms of sabotage threat", "OFFICIAL", "London", "Europe", "Diplomacy"),
    (21, "Ecuador campaign ends ahead of vote", "REPORTED", "Quito", "South America", "Politics"),
    (22, "US tells citizens to leave Iran", "OFFICIAL", "State Dept", "Middle East", "Diplomacy"),
    (23, "Bangladesh raises garment wage 36%", "OFFICIAL", "Dhaka", "Asia", "Labour"),
    (24, "Australia inflation hits 4.9%", "CONFIRMED", "ABS", "Oceania", "Markets"),
    (25, "Dell shares slide 7% after record Q3", "CONFIRMED", "Zacks", "North America", "Markets"),
    (26, "Colombia frees all Cartagena hostages", "CONFIRMED", "Bogot\u00e1", "South America", "Justice"),
    (27, "DR Congo Ebola: medics evacuated", "CONFIRMED", "UN", "Africa", "Health"),
    (28, "Yemen aid chief pleads for access", "OFFICIAL", "UN", "Middle East", "Health"),
    (29, "Pope laments COP31 failure", "REPORTED", "AP", "Europe", "Weather"),
    (30, "Nor'easter bears down on US East Coast", "FORECAST", "NOAA", "North America", "Weather"),
    (31, "Trump hosts NATO chief Rutte", "OFFICIAL", "White House", "North America", "Politics"),
    (32, "Iowa Army detonates ageing lead azide", "CONFIRMED", "US Army", "North America", "Politics"),
    (33, "Solomons pact bars foreign bases", "OFFICIAL", "Canberra", "Oceania", "Diplomacy"),
    (34, "Brazil real rallies as bank sells $2bn", "REPORTED", "Bras\u00edlia", "South America", "Markets"),
    (35, "S. Africa names Mkhwanazi to head Hawks", "REPORTED", "Pretoria", "Africa", "Justice"),
]

TIMELINE = [
    ("00:18", "Shenzhou-24 launches"),
    ("03:56", "Docks with Tiangong"),
    ("06:35", "Crew welcomed aboard"),
    ("07:02", "Colombia hostages freed"),
    ("11:58", "RSF strikes in Sudan"),
    ("15:00", "Iowa lead-azide blast"),
    ("20:00", "UCL late kick-offs"),
]

NUMBERS = [
    ("\u22126.16%", "KOSPI, SEOUL \u2014 WEDNESDAY"),
    ("3.8%", "US PCE INFLATION, OCTOBER"),
    ("74,746", "GAZA DEATH TOLL"),
    ("145", "UKRAINIAN DRONES DOWNED"),
    ("19", "CIVILIANS KILLED IN SUDAN"),
    ("5", "PLANES DAMAGED"),
]

REGIONS = [
    ("Europe", 12), ("North America", 6), ("Middle East", 5), ("Asia", 4),
    ("Africa", 3), ("South America", 3), ("Oceania", 2), ("Antarctica", 0),
]

# Map pins: (story number, x fraction, y fraction of the cropped map,
#              label dx, label dy) — dx/dy shift the number badge off the point.
PINS = [
    (1, 0.646, 0.417, 0, -22),
    (2, 0.768, 0.345, 0, -18),
    (3, 0.189, 0.345, -16, -20),
    (4, 0.612, 0.248, -24, -16),
    (5, 0.629, 0.260, 24, 14),
    (6, 0.596, 0.393, -18, -20),
    (7, 0.596, 0.514, -28, 26),
    (8, 0.835, 0.357, 0, -18),
    (9, 0.490, 0.260, -26, -14),
    (10, 0.512, 0.284, 26, 14),
    (11, 0.505, 0.269, 0, 18),
    (12, 0.178, 0.404, 14, 16),
    (13, 0.784, 0.550, 0, -18),
]

DATE_CHECK_LEFT_OUT = (
    "CAS Senegal ruling (Tue) \u00b7 Huawei verdict (Tue) \u00b7 Dell results (Tue) \u00b7 "
    "Dow 50,000 (Tue) \u00b7 COP31 collapse (Sun) \u00b7 ICJ Myanmar ruling (19 Nov) \u00b7 "
    "Merkury sunk (Sun) \u00b7 Giuliani medal (Tue) \u00b7 Axios AI report (Tue) \u00b7 "
    "Riyadh tower strike (Tue)")
DATE_CHECK_NOT_YET = (
    "Trump\u2013Rutte dinner outcome \u00b7 Thanksgiving nor'easter \u00b7 "
    "Chess Game 3 (Thu) \u00b7 US tariff hearing (25 Jan)")


def main():
    leads, smalls, ocean = load_panels()
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    x0, x1 = MARGIN, W - MARGIN

    # ---- masthead
    d.line([(x0, 8), (x1, 8)], fill=RULE, width=2)
    d.text((W // 2, 12), "THE WORLD", font=F_SERIF(56), fill=INK, anchor="ma")
    d.text((W // 2, 72), "WEDNESDAY 25 NOVEMBER 2026  \u2014  LATE EDITION \u00b7 THE FULL DAY",
           font=F_BOLD(13), fill=RED, anchor="ma")
    d.line([(x0, 92), (x1, 92)], fill=RULE, width=2)
    d.text((x0, 98), "35 STORIES  \u00b7  7 REGIONS  \u00b7  10 FIELDS", font=F_BOLD(12), fill=INK)
    d.text((x1, 98), "ONE DAY \u00b7 ONE FRONT PAGE", font=F_BOLD(11), fill=NAVY, anchor="ra")

    # ---- UTC timeline strip
    ty = 118
    d.rectangle([x0, ty, x1, ty + 40], outline=RULE, width=1, fill=LIGHT)
    d.text((x0 + 8, ty + 4), "THE DAY IN UTC", font=F_BOLD(10), fill=RED)
    seg = (x1 - x0 - 16) / len(TIMELINE)
    for i, (t, ev) in enumerate(TIMELINE):
        cx = x0 + 8 + seg * i
        d.text((cx, ty + 16), t, font=F_BOLD(11), fill=NAVY)
        for j, ln in enumerate(wrap(d, ev, F_REG(9), seg - 8)):
            d.text((cx, ty + 28 + j * 10), ln, font=F_REG(9), fill=INK)
        if i:
            d.line([(cx - 4, ty + 16), (cx - 4, ty + 38)], fill=(200, 195, 180), width=1)

    # ---- three illustrated leads
    ly = 168
    col_w = (x1 - x0 - 20) // 3
    lead_focus = [0.42, 0.45, 0.42]
    for i, (num, head, body, tag, src, _rg, _fd) in enumerate(LEADS):
        cx = x0 + i * (col_w + 10)
        panel = leads[i]
        pic = crop_band(panel, (0, 0, panel.width, panel.height), col_w, 128,
                        focus=lead_focus[i])
        img.paste(pic, (cx, ly))
        d.rectangle([cx, ly, cx + col_w - 1, ly + 127], outline=RULE, width=1)
        d.ellipse([cx + 6, ly + 6, cx + 26, ly + 26], fill=RED)
        d.text((cx + 16, ly + 8), str(num), font=F_BOLD(13), fill=(255, 255, 255),
               anchor="ma")
        hy = ly + 134
        for j, ln in enumerate(wrap(d, head, F_BOLD(14), col_w)):
            d.text((cx, hy + j * 17), ln, font=F_BOLD(14), fill=INK)
        by = hy + 17 * len(wrap(d, head, F_BOLD(14), col_w)) + 3
        for j, ln in enumerate(wrap(d, body, F_REG(11), col_w)[:3]):
            d.text((cx, by + j * 13), ln, font=F_REG(11), fill=INK)
        draw_tag(d, cx, ly + 208, tag, src, F_BOLD(9))

    # ---- numbers strip
    ny = 396
    n_w = (x1 - x0 - 5 * 8) // 6
    for i, (big, label) in enumerate(NUMBERS):
        nx = x0 + i * (n_w + 8)
        d.rectangle([nx, ny, nx + n_w - 1, ny + 41], outline=RULE, width=1, fill=(255, 255, 255))
        d.text((nx + n_w // 2, ny + 2), big, font=F_BOLD(19), fill=RED, anchor="ma")
        for j, ln in enumerate(wrap(d, label, F_BOLD(8), n_w - 8)):
            d.text((nx + n_w // 2, ny + 25 + j * 9), ln, font=F_BOLD(8), fill=GREY, anchor="ma")

    # ---- cards 4-13: two rows of five, each with a small illustration
    cy = 448
    card_w = (x1 - x0 - 4 * 8) // 5
    card_h = 104
    for idx, card in enumerate(CARDS):
        num, head, body, tag, src, _rg, _fd, sm = card[:8]
        focus = card[8] if len(card) > 8 else 0.45
        row, col = divmod(idx, 5)
        cx = x0 + col * (card_w + 8)
        cyy = cy + row * (card_h + 8)
        panel = smalls[sm]
        pic = crop_band(panel, (0, 0, panel.width, panel.height), card_w, 36, focus=focus)
        img.paste(pic, (cx, cyy))
        d.rectangle([cx, cyy, cx + card_w - 1, cyy + 35], outline=RULE, width=1)
        d.ellipse([cx + 4, cyy + 4, cx + 20, cyy + 20], fill=NAVY)
        d.text((cx + 12, cyy + 5), str(num), font=F_BOLD(10), fill=(255, 255, 255), anchor="ma")
        hy = cyy + 40
        for j, ln in enumerate(wrap(d, head, F_BOLD(11), card_w)):
            d.text((cx, hy + j * 13), ln, font=F_BOLD(11), fill=INK)
        by = hy + 13 * len(wrap(d, head, F_BOLD(11), card_w)) + 2
        for j, ln in enumerate(wrap(d, body, F_REG(10), card_w)[:3]):
            d.text((cx, by + j * 11), ln, font=F_REG(10), fill=INK)
        draw_tag(d, cx, cyy + card_h - 13, tag, src, F_BOLD(8))

    # ---- map + regions + DATE CHECK
    my = 672
    map_w, map_h = 300, 184
    d.rectangle([x0, my, x1, my + map_h], outline=RULE, width=1, fill=(255, 255, 255))
    d.text((x0 + 6, my + 4), "WHERE IT HAPPENED", font=F_BOLD(10), fill=RED)
    map_img = ocean.resize((map_w, map_h - 22), Image.LANCZOS)
    img.paste(map_img, (x0 + 2, my + 20))
    d.rectangle([x0 + 2, my + 20, x0 + map_w - 2, my + map_h - 2], outline=RULE, width=1)
    mx0, my0 = x0 + 2, my + 20
    mw, mh = map_w - 4, map_h - 22
    for num, fx, fy, dx, dy in PINS:
        px, py = mx0 + fx * mw, my0 + fy * mh
        bx, by = px + dx, py + dy
        d.line([(px, py), (bx, by)], fill=RED, width=1)
        d.ellipse([bx - 8, by - 8, bx + 8, by + 8], fill=RED, outline=(255, 255, 255), width=1)
        d.text((bx, by - 1), str(num), font=F_BOLD(9), fill=(255, 255, 255), anchor="mm")
        d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=RED)

    # regions column
    rx = x0 + map_w + 16
    rw = 300
    d.text((rx, my + 4), "7 REGIONS \u2014 STORY COUNT", font=F_BOLD(10), fill=RED)
    for i, (name, count) in enumerate(REGIONS):
        ry = my + 24 + i * 20
        d.text((rx, ry), name, font=F_REG(11), fill=INK)
        bar = int(count / 12 * 120)
        d.rectangle([rx + 130, ry + 2, rx + 130 + bar, ry + 12], fill=NAVY)
        d.text((rx + 258, ry), str(count), font=F_BOLD(11), fill=INK)

    # DATE CHECK column
    dx0 = rx + rw + 16
    dw = x1 - dx0
    d.rectangle([dx0, my, x1, my + map_h], outline=RED, width=2, fill=(255, 250, 240))
    d.text((dx0 + 8, my + 5), "DATE CHECK", font=F_BOLD(12), fill=RED)
    ty2 = my + 24
    d.text((dx0 + 8, ty2), "LEFT OUT \u2014 happened before today:", font=F_BOLD(9), fill=INK)
    ty2 += 12
    for ln in wrap(d, DATE_CHECK_LEFT_OUT, F_REG(9), dw - 16):
        d.text((dx0 + 8, ty2), ln, font=F_REG(9), fill=INK)
        ty2 += 11
    ty2 += 4
    d.text((dx0 + 8, ty2), "NOT YET:", font=F_BOLD(9), fill=INK)
    ty2 += 12
    for ln in wrap(d, DATE_CHECK_NOT_YET, F_REG(9), dw - 16):
        d.text((dx0 + 8, ty2), ln, font=F_REG(9), fill=INK)
        ty2 += 11

    # ---- briefs 14-35: three columns
    by0 = 872
    d.text((x0, by0), "BRIEFS 14\u201335 \u2014 THE REST OF WEDNESDAY",
           font=F_BOLD(11), fill=RED)
    d.line([(x0, by0 + 15), (x1, by0 + 15)], fill=RULE, width=1)
    bcol_w = (x1 - x0 - 2 * 12) // 3
    rows = 8
    for idx, (num, head, tag, src, _rg, _fd) in enumerate(BRIEFS):
        col, row = divmod(idx, rows)
        bx = x0 + col * (bcol_w + 12)
        byy = by0 + 20 + row * 13
        line = f"{num}. {head} \u2014 {src} \u00b7 {tag}"
        fnt = F_REG(10)
        if text_w(d, line, fnt) > bcol_w:
            fnt = F_REG(9)
        d.text((bx, byy), f"{num}.", font=F_BOLD(10), fill=RED)
        d.text((bx + 20, byy), f"{head} \u2014 {src} \u00b7 {tag}", font=fnt, fill=INK)

    # ---- footer
    fy = 994
    d.line([(x0, fy), (x1, fy)], fill=RULE, width=1)
    d.text((x0, fy + 4),
           "SOURCES: AP \u00b7 Reuters \u00b7 AFP \u00b7 BBC \u00b7 USTR \u00b7 CMSA \u00b7 UN \u00b7 FIDE \u00b7 UEFA \u00b7 NOAA \u00b7 NWS",
           font=F_REG(9), fill=GREY)
    d.text((x0, fy + 16),
           "Every story on this page happened or was first reported on Wednesday 25 November 2026. "
           "Illustrations are AI-generated panels; all text is set in code.",
           font=F_REG(9), fill=GREY)

    out = os.path.join(HERE, "entry.png")
    img.save(out, optimize=True)
    size = os.path.getsize(out)
    sha = hashlib.sha256(open(out, "rb").read()).hexdigest()
    stories = len(LEADS) + len(CARDS) + len(BRIEFS)
    # Tuple shapes differ: LEADS/CARDS are (num, head, body, tag, src, region,
    # field[, panel]); BRIEFS are (num, head, tag, src, region, field).
    tagged = (sum(1 for s in LEADS + CARDS if s[3] in TAG_COLORS)
              + sum(1 for s in BRIEFS if s[2] in TAG_COLORS))
    regions = {s[5] for s in LEADS + CARDS} | {s[4] for s in BRIEFS}
    fields = {s[6] for s in LEADS + CARDS} | {s[5] for s in BRIEFS}
    print(f"saved {out} {size} bytes sha256={sha}")
    print(f"stories={stories} tagged={tagged}/{stories} "
          f"({100*tagged/stories:.0f}%) regions={len(regions)} fields={len(fields)}")
    print(f"regions: {sorted(regions)}")
    print(f"fields: {sorted(fields)}")
    print(f"size_ok={size <= 1048576} dims={img.size}")


if __name__ == "__main__":
    main()
