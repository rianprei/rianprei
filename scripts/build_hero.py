#!/usr/bin/python3
"""Build the profile hero SVG with subset fonts embedded.

The hero carries its own saturated background, so one file works on GitHub light and dark.
usage: /usr/bin/python3 scripts/build_hero.py <out-dir>
Needs fontTools + brotli (system python) and the font files below.
"""
from __future__ import annotations

import base64
import io
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from fontTools import subset
from fontTools.ttLib import TTFont

FONT_TITLE = Path("/usr/share/fonts/TTF/FiraSansCompressed-ExtraBold.ttf")
FONT_SUB = Path("/usr/share/fonts/TTF/FiraSansCompressed-Medium.ttf")
FONT_MONO = Path("/usr/share/fonts/TTF/Hack-Regular.ttf")

# Design tokens (also used by README badges/cards).
NAVY = "#0A2472"       # hero background, badge label fill (white text 14:1)
NAVY_LIGHT = "#1B3A9E" # shapes on the navy
BLUE = "#1F4FD8"       # phone shadow, accent on light theme (6:1 on white)
POCO = "#FFD21F"       # POCO brand yellow: phone body, prompt, cursor
INK = "#14141A"        # phone screen
WHITE = "#FFFFFF"      # title
SUB_TEXT = "#BFD0FF"   # subtitle on navy (10:1)

TITLE = "rianprei"
SUBTITLE = ["Frontend", "Android/Termux", "Linux"]
PROMPT = "~ $"

# One layout for every viewport: the subtitle stays >= 16px when GitHub mobile
# scales the 840px canvas down to ~358px.
W, H, RADIUS, PAD = 840, 300, 24, 40
TITLE_SIZE, TITLE_Y = 150, 168
SUB_SIZE, SUB_Y = 38, 240
PHONE_X, PHONE_Y, PHONE_W, PHONE_H = 610, 40, 210, 420  # cropped by the canvas bottom
PROMPT_SIZE = 28


def subset_b64(font: Path, text: str) -> str:
    opts = subset.Options()
    opts.flavor, opts.hinting, opts.layout_features = "woff2", False, ["kern", "liga"]
    f = TTFont(font)
    sub = subset.Subsetter(opts)
    sub.populate(text=text)
    sub.subset(f)
    buf = io.BytesIO()
    f.save(buf)
    return base64.b64encode(buf.getvalue()).decode()


def text_width(font: Path, text: str, size: float) -> float:
    """Advance width in px, ignoring kerning (a few px of slack at most)."""
    f = TTFont(font, lazy=True)
    cmap, hmtx, upm = f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm
    return sum(hmtx[cmap[ord(c)]][0] for c in text) * size / upm


def subtitle_svg() -> tuple[str, float]:
    parts, x, gap = [], PAD + 4.0, SUB_SIZE * 0.55
    for i, word in enumerate(SUBTITLE):
        if i:
            parts.append(f'<rect x="{x + gap - 1.5:.1f}" y="{SUB_Y - SUB_SIZE * 0.72:.1f}" width="3" '
                         f'height="{SUB_SIZE * 0.8:.1f}" fill="{POCO}"/>')
            x += 2 * gap
        parts.append(f'<text x="{x:.1f}" y="{SUB_Y}" class="sub">{escape(word)}</text>')
        x += text_width(FONT_SUB, word, SUB_SIZE)
    return "".join(parts), x


def phone_svg() -> str:
    sx, sy = PHONE_X + 10, PHONE_Y + 10
    px, py = sx + 22, sy + 78
    cur_x = px + text_width(FONT_MONO, PROMPT + " ", PROMPT_SIZE)
    return (
        '<g class="phone">'
        f'<rect x="{PHONE_X + 14}" y="{PHONE_Y + 14}" width="{PHONE_W}" height="{PHONE_H}" rx="36" fill="{BLUE}"/>'
        f'<rect x="{PHONE_X}" y="{PHONE_Y}" width="{PHONE_W}" height="{PHONE_H}" rx="36" fill="{POCO}"/>'
        f'<rect x="{PHONE_X + PHONE_W - 1}" y="{PHONE_Y + 96}" width="5" height="48" rx="2.5" fill="{POCO}"/>'
        f'<rect x="{sx}" y="{sy}" width="{PHONE_W - 20}" height="{PHONE_H - 20}" rx="27" fill="{INK}"/>'
        f'<circle cx="{PHONE_X + PHONE_W / 2}" cy="{sy + 17}" r="5" fill="#2A2A33"/>'
        f'<text x="{px}" y="{py}" class="prompt">{escape(PROMPT)}</text>'
        f'<rect class="cur" x="{cur_x:.1f}" y="{py - PROMPT_SIZE * 0.78:.1f}" width="{PROMPT_SIZE * 0.6:.1f}" '
        f'height="{PROMPT_SIZE:.1f}" fill="{POCO}"/>'
        "</g>"
    )


def build(fonts: dict[str, str]) -> str:
    label = f"{TITLE}: {', '.join(SUBTITLE)}"
    sub, _ = subtitle_svg()
    style = f"""
@font-face{{font-family:T;src:url(data:font/woff2;base64,{fonts['title']}) format('woff2')}}
@font-face{{font-family:S;src:url(data:font/woff2;base64,{fonts['sub']}) format('woff2')}}
@font-face{{font-family:M;src:url(data:font/woff2;base64,{fonts['mono']}) format('woff2')}}
.title{{font:800 {TITLE_SIZE}px T,'Fira Sans Compressed','Arial Narrow',sans-serif;letter-spacing:-1.5px;fill:{WHITE}}}
.sub{{font:500 {SUB_SIZE}px S,'Fira Sans Compressed','Arial Narrow',sans-serif;fill:{SUB_TEXT}}}
.prompt{{font:400 {PROMPT_SIZE}px M,Hack,'DejaVu Sans Mono',monospace;fill:{POCO}}}
.phone{{animation:rise .45s cubic-bezier(.2,.7,.2,1) both}}
.cur{{animation:blink 1s steps(1) .6s 3}}
@keyframes rise{{from{{opacity:0;transform:translateY(28px)}}to{{opacity:1;transform:none}}}}
@keyframes blink{{50%{{opacity:0}}}}
@media (prefers-reduced-motion:reduce){{.phone,.cur{{animation:none}}}}
"""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="{escape(label)}">'
        f"<title>{escape(label)}</title><style>{style}</style>"
        f'<clipPath id="c"><rect width="{W}" height="{H}" rx="{RADIUS}"/></clipPath>'
        f'<g clip-path="url(#c)"><rect width="{W}" height="{H}" fill="{NAVY}"/>'
        f'<circle cx="{PHONE_X + PHONE_W / 2}" cy="{H + 10}" r="190" fill="{NAVY_LIGHT}" opacity=".7"/>'
        f'<text x="{PAD}" y="{TITLE_Y}" class="title">{TITLE}</text>'
        + sub + phone_svg() + "</g></svg>\n"
    )


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    for f in (FONT_TITLE, FONT_SUB, FONT_MONO):
        if not f.is_file():
            sys.exit(f"missing font: {f}")
    # Self-check: text column must not run into the phone.
    _, sub_end = subtitle_svg()
    title_end = PAD + text_width(FONT_TITLE, TITLE, TITLE_SIZE)
    assert max(sub_end, title_end) < PHONE_X - 24, (sub_end, title_end)
    fonts = {
        "title": subset_b64(FONT_TITLE, TITLE),
        "sub": subset_b64(FONT_SUB, "".join(SUBTITLE)),
        "mono": subset_b64(FONT_MONO, PROMPT),
    }
    path = out / "hero.svg"
    path.write_text(build(fonts), encoding="utf-8")
    print(f"{path} {path.stat().st_size} B")


if __name__ == "__main__":
    main()
