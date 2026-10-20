"""Creative renderer: branded post images as PNG, no external service needed.

Deterministic layout engine on Pillow: theme palette, wrapped headline,
subline, and a company band. Arabic text is shaped and bidirectionally
ordered when the shaping libraries are present, with a Latin fallback so the
renderer never hard fails. An AI image provider can be added behind
render_image later; the layout path stays as the branded template option.
"""

import io
import re
from pathlib import Path
from typing import Tuple

from PIL import Image, ImageDraw, ImageFont, features

# With libraqm, Pillow shapes and orders Arabic itself: feed it raw logical
# text with direction="rtl". Pre-shaping in that case double processes the
# text and reverses it on screen. Without raqm, fall back to reshaper + bidi.
HAS_RAQM = features.check("raqm")

THEMES = {
    "automotive": {"bg": (20, 24, 29), "accent": (245, 158, 11), "text": (240, 244, 248), "muted": (160, 172, 188)},
    "saas": {"bg": (10, 26, 47), "accent": (56, 189, 248), "text": (240, 248, 255), "muted": (148, 180, 210)},
    "default": {"bg": (24, 24, 32), "accent": (167, 139, 250), "text": (245, 245, 250), "muted": (170, 170, 185)},
}

_FONT_CANDIDATES_LATIN = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]
_FONT_CANDIDATES_ARABIC = [
    "/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansArabic-SemiBold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf",
]
_ARABIC = re.compile(r"[\u0600-\u06FF]")


def _font(text: str, size: int):
    candidates = _FONT_CANDIDATES_ARABIC if _ARABIC.search(text or "") else _FONT_CANDIDATES_LATIN
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _shape(text: str) -> str:
    """Visual-order shaping, only for renderers without raqm."""
    if HAS_RAQM or not _ARABIC.search(text or ""):
        return text
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display

        return get_display(arabic_reshaper.reshape(text))
    except Exception:
        return text


def _measure(draw: ImageDraw.ImageDraw, text: str, font) -> float:
    if HAS_RAQM and _ARABIC.search(text or ""):
        return draw.textlength(text, font=font, direction="rtl", language="ar")
    return draw.textlength(_shape(text), font=font)


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list:
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = f"{current} {word}".strip()
        if _measure(draw, trial, font) <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _draw_line(draw: ImageDraw.ImageDraw, x_left: int, x_right: int, y: int, text: str, font, fill) -> None:
    if _ARABIC.search(text or ""):
        if HAS_RAQM:
            draw.text((x_right, y), text, font=font, fill=fill, direction="rtl", language="ar", anchor="ra")
        else:
            draw.text((x_left, y), _shape(text), font=font, fill=fill)
    else:
        draw.text((x_left, y), text, font=font, fill=fill)


def render_image(
    company: str,
    product: str,
    headline: str,
    subline: str,
    theme: str = "automotive",
    size: Tuple[int, int] = (1080, 1080),
) -> bytes:
    palette = THEMES.get(theme, THEMES["default"])
    width, height = size
    img = Image.new("RGB", size, palette["bg"])
    draw = ImageDraw.Draw(img)

    # Accent geometry: top stripe and a diagonal corner panel.
    draw.rectangle([0, 0, width, 14], fill=palette["accent"])
    draw.polygon([(width, height), (width, int(height * 0.55)), (int(width * 0.62), height)], fill=palette["accent"])
    draw.polygon([(width, height), (width, int(height * 0.68)), (int(width * 0.74), height)], fill=palette["bg"])

    margin = 72
    max_width = width - margin * 2

    x_right = width - margin
    company_font = _font(company, 34)
    _draw_line(draw, margin, x_right, 64, company, company_font, palette["muted"])

    headline_size = 84
    lines = []
    font = _font(headline, headline_size)
    while headline_size > 40:
        font = _font(headline, headline_size)
        lines = _wrap(draw, headline, font, max_width)
        if len(lines) <= 3:
            break
        headline_size -= 8
    y = int(height * 0.30)
    line_factor = 1.34 if _ARABIC.search(headline or "") else 1.18
    for line in lines:
        _draw_line(draw, margin, x_right, y, line, font, palette["text"])
        y += int(headline_size * line_factor)

    y += 40 if _ARABIC.search(headline or "") else 26
    sub_font = _font(subline, 40)
    for line in _wrap(draw, subline, sub_font, max_width):
        _draw_line(draw, margin, x_right, y, line, sub_font, palette["muted"])
        y += 52

    band_y = height - 128
    draw.rectangle([0, band_y, width, height], fill=(0, 0, 0))
    band_font = _font(product, 44)
    label = f"{product}  ·  {company}" if product else company
    _draw_line(draw, margin, x_right, band_y + 38, label, band_font, palette["accent"])

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()
