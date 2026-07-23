#!/usr/bin/env python3
"""
Converts an image into a monochrome ASCII grid suitable for SVG terminal graphics.
Strips transparent background pixels, handles dark/light theme background sampling,
and maps foreground brightness cleanly.
"""

from PIL import Image, ImageEnhance

# Density ramps (from dense to sparse)
RAMP = "@%#*+=-:. "


def image_to_ascii_grid(
    image_path,
    cols=48,
    char_aspect=2.15,
    bg_color=(30, 33, 39),
    contrast=1.3,
    invert=False,
):
    """
    Converts image to ASCII grid while ignoring transparent background pixels.
    Accepts bg_color to maintain compatibility with build_card.py.
    """
    src = Image.open(image_path).convert("RGBA")

    # Boost contrast slightly so foreground details/edges pop
    if contrast != 1.0:
        enhancer = ImageEnhance.Contrast(src)
        src = enhancer.enhance(contrast)

    w, h = src.size
    cell_w = w / cols
    rows = max(1, round((h / cell_w) / char_aspect))
    cell_h = h / rows

    grid = []
    ramp_len = len(RAMP)

    for ry in range(rows):
        row = []
        for cx in range(cols):
            left = int(cx * cell_w)
            upper = int(ry * cell_h)
            right = int(min(w, (cx + 1) * cell_w))
            lower = int(min(h, (ry + 1) * cell_h))

            if right <= left:
                right = left + 1
            if lower <= upper:
                lower = upper + 1

            region = src.crop((left, upper, right, lower))
            pixels = list(region.getdata())

            # Check average alpha — if it's mostly transparent, leave it empty
            avg_alpha = sum(p[3] for p in pixels) / len(pixels)
            if avg_alpha < 50:
                row.append((" ", None))
                continue

            # Calculate brightness on RGB channels
            avg_r = sum(p[0] for p in pixels) / len(pixels)
            avg_g = sum(p[1] for p in pixels) / len(pixels)
            avg_b = sum(p[2] for p in pixels) / len(pixels)
            brightness = (0.299 * avg_r + 0.587 * avg_g + 0.114 * avg_b) / 255.0

            # Invert for dark backgrounds if requested
            if invert:
                brightness = 1.0 - brightness

            idx = int(brightness * (ramp_len - 1))
            idx = max(0, min(ramp_len - 1, idx))

            row.append((RAMP[idx], None))
        grid.append(row)

    return grid


def grid_to_svg_text_elements(
    grid, x_start, y_start, font_size, line_height, char_width, color=None
):
    """
    Returns a list of SVG <text> strings, one per row.
    Uses inline CSS style to guarantee font-size and char-width (letter-spacing) are applied.
    """
    lines = []
    fill_attr = f' fill="{color}"' if color else ' class="cmd"'

    for ry, row in enumerate(grid):
        y = y_start + ry * line_height
        line_str = "".join(ch for ch, _ in row)

        # Preserve spacing and XML safety
        line_str_escaped = (
            line_str.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace(" ", "&#160;")
        )

        # Style attribute ensures font-size and character spacing override CSS classes
        style_attr = f'style="font-size: {font_size}px; letter-spacing: {char_width}px;"'

        line = (
            f'<text x="{x_start}" y="{y}" font-family="Courier New, monospace" '
            f'{fill_attr} {style_attr} xml:space="preserve">{line_str_escaped}</text>'
        )
        lines.append(line)

    return lines


if __name__ == "__main__":
    import sys

    img_path = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "/mnt/user-data/uploads/Hero_Img.png"
    )
    grid = image_to_ascii_grid(img_path, cols=48)
    for row in grid:
        print("".join(c for c, _ in row))