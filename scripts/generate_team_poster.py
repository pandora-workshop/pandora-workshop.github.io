#!/usr/bin/env python3

from __future__ import annotations

import base64
import mimetypes
import re
from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[1]
ORG_PAGE = ROOT / "_pages" / "organization.md"
OUTPUT = ROOT / "images" / "pandora-team-poster.svg"

WIDTH = 1920
HEIGHT = 1080
CARD_COLS = 4
CARD_ROWS = 2

# Layout
OUTER_MARGIN = 54
HEADER_HEIGHT = 216
GRID_GAP_X = 18
GRID_GAP_Y = 18
GRID_TOP = HEADER_HEIGHT + 30
GRID_WIDTH = WIDTH - OUTER_MARGIN * 2
GRID_HEIGHT = HEIGHT - GRID_TOP - OUTER_MARGIN
CARD_WIDTH = (GRID_WIDTH - GRID_GAP_X * (CARD_COLS - 1)) // CARD_COLS
CARD_HEIGHT = (GRID_HEIGHT - GRID_GAP_Y * (CARD_ROWS - 1)) // CARD_ROWS

# Visual theme
PAGE_BG = "#F8FAFF"
TITLE_COLOR = "#4A3597"
SUBTITLE_COLOR = "#563FA9"
NAME_COLOR = "#101828C1"
AFFILIATION_COLOR = "#101828C7"
PHOTO_RING = "#FFFFFF"
CARD_SHADOW = "#0D13241A"
TAG_BG = "#FFFFFFCC"

PALETTE = [
    {"surface": "#FFF8EF", "accent": "#FF7A59", "glow": "#FFD2C4"},
    {"surface": "#EFFBF7", "accent": "#18B88A", "glow": "#BDF3E1"},
    {"surface": "#F2F5FF", "accent": "#5B6CFF", "glow": "#CFD7FF"},
    {"surface": "#FFF2FA", "accent": "#E649A0", "glow": "#FFC7E4"},
    {"surface": "#FFF7E8", "accent": "#F59E0B", "glow": "#FFE1A6"},
    {"surface": "#EFF9FF", "accent": "#06B6D4", "glow": "#BDEFFF"},
    {"surface": "#F7F2FF", "accent": "#8B5CF6", "glow": "#DDD0FF"},
    {"surface": "#F2FBF5", "accent": "#22C55E", "glow": "#C7F0D4"},
]


def parse_organizers() -> list[dict[str, str]]:
    text = ORG_PAGE.read_text(encoding="utf-8")
    pattern = re.compile(
        r'{% include committee-member\.html\s+'
        r'name="(?P<name>[^"]+)"\s+'
        r'picture="(?P<picture>[^"]+)"\s+'
        r'site="(?P<site>[^"]+)"\s+'
        r'institution="(?P<institution>[^"]+)"\s*%}',
        re.MULTILINE,
    )

    organizers = [match.groupdict() for match in pattern.finditer(text)]
    if not organizers:
        raise RuntimeError("No organizer blocks found in _pages/organization.md")
    return organizers


def wrap_text(text: str, max_chars: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = word if not current else f"{current} {word}"
        if len(trial) <= max_chars or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def text_block(lines: list[str], x: float, y: float, line_height: int, class_name: str) -> str:
    spans = []
    for idx, line in enumerate(lines):
        dy = "0" if idx == 0 else str(line_height)
        spans.append(f'<tspan x="{x}" dy="{dy}">{escape(line)}</tspan>')
    joined = "".join(spans)
    return f'<text x="{x}" y="{y}" class="{class_name}">{joined}</text>'


def image_data_uri(target: str) -> str:
    target_path = (ROOT / target.lstrip("/")).resolve()
    mime_type, _ = mimetypes.guess_type(target_path.name)
    if not mime_type:
        raise RuntimeError(f"Could not detect MIME type for {target_path}")

    data = base64.b64encode(target_path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{data}"


def rounded_rect_path(x: float, y: float, width: float, height: float, radius: float) -> str:
    return (
        f"M {x + radius:.2f} {y:.2f} "
        f"H {x + width - radius:.2f} "
        f"Q {x + width:.2f} {y:.2f} {x + width:.2f} {y + radius:.2f} "
        f"V {y + height - radius:.2f} "
        f"Q {x + width:.2f} {y + height:.2f} {x + width - radius:.2f} {y + height:.2f} "
        f"H {x + radius:.2f} "
        f"Q {x:.2f} {y + height:.2f} {x:.2f} {y + height - radius:.2f} "
        f"V {y + radius:.2f} "
        f"Q {x:.2f} {y:.2f} {x + radius:.2f} {y:.2f} Z"
    )


def build_svg(organizers: list[dict[str, str]]) -> str:
    defs = []
    cards = []

    clip_size = 190
    clip_radius = clip_size / 2
    card_radius = 36

    for idx, organizer in enumerate(organizers[: CARD_COLS * CARD_ROWS]):
        col = idx % CARD_COLS
        row = idx // CARD_COLS
        x = OUTER_MARGIN + col * (CARD_WIDTH + GRID_GAP_X)
        y = GRID_TOP + row * (CARD_HEIGHT + GRID_GAP_Y)
        theme = PALETTE[idx % len(PALETTE)]
        surface = theme["surface"]
        # accent = theme["accent"]
        # glow = theme["glow"]

        clip_id = f"clip-{idx}"
        clip_cx = x + CARD_WIDTH / 2
        clip_cy = y + 122
        defs.append(
            f'<clipPath id="{clip_id}"><circle cx="{clip_cx}" cy="{clip_cy}" r="{clip_radius}"/></clipPath>'
        )

        image_href = image_data_uri(organizer["picture"])
        image_x = clip_cx - clip_size / 2
        image_y = clip_cy - clip_size / 2

        name_lines = wrap_text(organizer["name"], 15)
        affiliation_lines = wrap_text(organizer["institution"], 24)

        name_y = y + 272
        affiliation_y = name_y + 30 * len(name_lines) + 8
        tag_x = x + 24
        tag_y = y + 22
        tag_width = min(210, 92 + len(str(idx + 1)) * 18)
        card_path = rounded_rect_path(x, y, CARD_WIDTH, CARD_HEIGHT, card_radius)



        cards.append(
            f'''
  <g>
    <path d="{card_path}" fill="{surface}"/>
    <image href="{image_href}" x="{image_x}" y="{image_y}" width="{clip_size+12}" height="{clip_size+12}" preserveAspectRatio="xMidYMid slice" clip-path="url(#{clip_id})"/>
    {text_block(name_lines, clip_cx, name_y, 34, "name")}
    {text_block(affiliation_lines, clip_cx, affiliation_y, 22, "affiliation")}
  </g>'''
        )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
  <defs>
    <filter id="card-shadow" x="-20%" y="-20%" width="140%" height="150%">
      <feDropShadow dx="0" dy="16" stdDeviation="18" flood-color="{CARD_SHADOW}"/>
    </filter>
    <linearGradient id="bg-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#F8FAFF"/>
      <stop offset="50%" stop-color="#FFF8F1"/>
      <stop offset="100%" stop-color="#F4F9FF"/>
    </linearGradient>
    <radialGradient id="hero-glow-a" cx="0%" cy="0%" r="100%">
      <stop offset="0%" stop-color="#FFBFA3" stop-opacity="0.9"/>
      <stop offset="100%" stop-color="#FFBFA3" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="hero-glow-b" cx="100%" cy="10%" r="100%">
      <stop offset="0%" stop-color="#B9CCFF" stop-opacity="0.9"/>
      <stop offset="100%" stop-color="#B9CCFF" stop-opacity="0"/>
    </radialGradient>
    <style>
      .title {{
        font-family: "Trebuchet MS", "Arial", Arial, sans-serif;
        font-size: 80px;
        font-weight: 600;
        letter-spacing: 1.5px;
        fill: {TITLE_COLOR};
      }}
      .subtitle {{
        font-family: "Trebuchet MS", Arial, sans-serif;
        font-size: 62px;
        font-weight: 600;
        letter-spacing: 0.6px;
        fill: {SUBTITLE_COLOR};
      }}
      .tag {{
        font-family: "Trebuchet MS", Arial, sans-serif;
        font-size: 18px;
        font-weight: 700;
        letter-spacing: 1.6px;
        fill: #475467;
      }}
      .name {{
        font-family: "Trebuchet MS", "Arial", Arial, sans-serif;
        font-size: 40px;
        font-weight: 680;
        fill: {TITLE_COLOR};
        text-anchor: middle;
      }}
      .affiliation {{
        font-family: "Trebuchet MS", "Arial Narrow", sans-serif;
        font-size: 28px;
        font-weight: 500;
        fill: {AFFILIATION_COLOR};
        text-anchor: middle;
      }}
    </style>
    {''.join(defs)}
  </defs>
  <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#bg-gradient)"/>
  <circle cx="160" cy="140" r="240" fill="url(#hero-glow-a)"/>
  <circle cx="1680" cy="120" r="320" fill="url(#hero-glow-b)"/>
  <circle cx="1540" cy="910" r="260" fill="#CFF4FF" opacity="0.45"/>
  <text x="{OUTER_MARGIN}" y="122" class="subtitle">MEET THE TEAM</text>
  <text x="{OUTER_MARGIN}" y="200" class="title">PANDORA @ EMNLP 2026</text>
  <g filter="url(#card-shadow)">
    {''.join(cards)}
  </g>
</svg>
'''


def main() -> None:
    organizers = parse_organizers()
    svg = build_svg(organizers)
    OUTPUT.write_text(svg, encoding="utf-8")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
