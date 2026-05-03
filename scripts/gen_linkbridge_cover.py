"""Generate LinkBridge project cover image (1200x630 OG dimensions, dark theme)."""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

W, H = 1200, 630
OUT = Path(__file__).parent.parent / "static" / "images" / "linkbridge" / "cover.png"
OUT.parent.mkdir(parents=True, exist_ok=True)

bg = (16, 18, 22)        # near-black
fg = (220, 220, 220)
accent = (115, 200, 255) # cyan-blue

img = Image.new("RGB", (W, H), bg)
draw = ImageDraw.Draw(img)


def load_font(size):
    candidates = [
        "/System/Library/Fonts/SFNSMono.ttf",
        "/System/Library/Fonts/Menlo.ttc",
        "/Library/Fonts/Andale Mono.ttf",
        "/System/Library/Fonts/Supplemental/Andale Mono.ttf",
    ]
    for p in candidates:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


title_font = load_font(96)
sub_font = load_font(36)
diagram_font = load_font(28)

# Title
title = "LinkBridge"
tw, th = draw.textbbox((0, 0), title, font=title_font)[2:]
draw.text(((W - tw) / 2, 130), title, fill=fg, font=title_font)

# Subtitle
sub = "Ableton Link  →  MIDI Clock"
sw, sh = draw.textbbox((0, 0), sub, font=sub_font)[2:]
draw.text(((W - sw) / 2, 260), sub, fill=accent, font=sub_font)

# ASCII diagram (box-drawing chars)
diagram_lines = [
    "┌─────────────┐    ┌──────────────┐    ┌─────────────┐",
    "│  djay Pro   │    │  LinkBridge  │    │   Novation  │",
    "│  Mixxx      │ ──→│  (menubar)   │──→ │  Circuit    │",
    "│  Ableton    │    │              │    │   Tracks    │",
    "└─────────────┘    └──────────────┘    └─────────────┘",
    "    Link tempo         Translate          MIDI clock",
]
y = 380
for line in diagram_lines:
    lw, lh = draw.textbbox((0, 0), line, font=diagram_font)[2:]
    draw.text(((W - lw) / 2, y), line, fill=fg, font=diagram_font)
    y += 36

img.save(OUT, "PNG", optimize=True)
print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")
