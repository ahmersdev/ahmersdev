#!/usr/bin/env python3
"""
Builds dark_mode_template.svg and light_mode_template.svg by combining:
 - a colored ASCII-art rendering of the user's photo (left panel, static)
 - stat placeholders {{...}} that today.py fills in on every run (right panel)

Run this once (or whenever you want to change the source photo). It's a
one-time build step, separate from today.py which runs on the schedule.
"""

import sys
from ascii_art import image_to_ascii_grid, grid_to_svg_text_elements

IMAGE_PATH = sys.argv[1] if len(sys.argv) > 1 else "/mnt/user-data/uploads/Hero_Img.png"

CARD_WIDTH = 860
CARD_HEIGHT = 460

THEMES = {
    "dark": {
        "bg": (30, 33, 39),
        "title_bar": "#21252b",
        "window_bg": "#1e2127",
        "prompt": "#56d364",
        "cmd": "#c9d1d9",
        "label": "#8b949e",
        "value": "#79c0ff",
        "accent": "#f778ba",
        "danger": "#f85149",
        "titletext": "#8b949e",
        "divider": "#30363d",
    },
    "light": {
        "bg": (255, 255, 255),
        "title_bar": "#f6f8fa",
        "window_bg": "#ffffff",
        "prompt": "#1a7f37",
        "cmd": "#24292f",
        "label": "#57606a",
        "value": "#0969da",
        "accent": "#bf3989",
        "danger": "#cf222e",
        "titletext": "#57606a",
        "divider": "#d0d7de",
    },
}


def build_template(theme_name):
    t = THEMES[theme_name]

    # 1. Lower char_aspect (1.7) -> generates more rows to fix pinched height
    grid = image_to_ascii_grid(
        IMAGE_PATH,
        cols=38,
        char_aspect=1.5,
        bg_color=t["bg"],
        invert=(theme_name == "dark"),
    )

    # 2. y_start=86 adds ~10px top padding below the `$ cat avatar.txt` prompt
    # 3. Increase line_height slightly (9.0) if you want even taller vertical presence
    ascii_lines = grid_to_svg_text_elements(
        grid, x_start=35, y_start=100, font_size=10, line_height=12.5, char_width=1
    )
    ascii_block = "\n  ".join(ascii_lines)

    svg = f"""<svg width="{CARD_WIDTH}" height="{CARD_HEIGHT}" viewBox="0 0 {CARD_WIDTH} {CARD_HEIGHT}" xmlns="http://www.w3.org/2000/svg" font-family="'Courier New', Courier, monospace">
  <style>
    .title-bar {{ fill: {t['title_bar']}; }}
    .window-bg {{ fill: {t['window_bg']}; }}
    .prompt {{ fill: {t['prompt']}; font-size: 15px; }}
    .cmd {{ fill: {t['cmd']}; font-size: 15px; }}
    .label {{ fill: {t['label']}; font-size: 13px; }}
    .value {{ fill: {t['value']}; font-size: 13px; font-weight: bold; }}
    .accent {{ fill: {t['accent']}; font-size: 13px; }}
    .cursor {{ fill: {t['prompt']}; }}
    .titletext {{ fill: {t['titletext']}; font-size: 13px; }}
    .caption {{ fill: {t['label']}; font-size: 11px; font-style: italic; }}
  </style>

  <rect x="0" y="0" width="{CARD_WIDTH}" height="{CARD_HEIGHT}" rx="10" class="window-bg"/>
  <rect x="0" y="0" width="{CARD_WIDTH}" height="34" rx="10" class="title-bar"/>
  <rect x="0" y="24" width="{CARD_WIDTH}" height="10" class="title-bar"/>

  <circle cx="22" cy="17" r="6" fill="#ff5f56"/>
  <circle cx="42" cy="17" r="6" fill="#ffbd2e"/>
  <circle cx="62" cy="17" r="6" fill="#27c93f"/>
  <text x="{CARD_WIDTH/2}" y="22" text-anchor="middle" class="titletext">ahmer@github: ~</text>

  <!-- Left panel: ASCII avatar -->
  <text x="28" y="60" class="prompt">$ <tspan class="cmd">cat avatar.txt</tspan></text>
  {ascii_block}

  <!-- Divider -->
  <line x1="330" y1="44" x2="330" y2="{CARD_HEIGHT - 20}" stroke="{t['divider']}" stroke-width="1"/>

  <!-- Right panel: live stats -->
  <text x="352" y="60" class="prompt">$ <tspan class="cmd">whoami</tspan></text>
  <text x="352" y="82" class="cmd">{{{{FULL_NAME}}}} &#8212; {{{{TAGLINE}}}}</text>

  <text x="352" y="114" class="prompt">$ <tspan class="cmd">cat stats.txt</tspan></text>
  <text x="352" y="140" class="label">Repositories       <tspan class="value">{{{{REPOS}}}}</tspan></text>
  <text x="352" y="162" class="label">Total Commits      <tspan class="value">{{{{COMMITS}}}}</tspan></text>
  <text x="352" y="184" class="label">Stars Earned       <tspan class="value">{{{{STARS}}}}</tspan></text>
  <text x="352" y="206" class="label">Followers          <tspan class="value">{{{{FOLLOWERS}}}}</tspan></text>
  <text x="352" y="228" class="label">Lines of Code      <tspan class="accent">+{{{{LINES_ADDED}}}}</tspan><tspan class="label">, </tspan><tspan fill="{t['danger']}">-{{{{LINES_DELETED}}}}</tspan></text>

  <text x="352" y="260" class="prompt">$ <tspan class="cmd">cat tech_stack.txt</tspan></text>
  <text x="352" y="282" class="label">{{{{TECH_LINE_1}}}}</text>
  <text x="352" y="302" class="label">{{{{TECH_LINE_2}}}}</text>

  <text x="352" y="334" class="prompt">$ <tspan class="cmd">cat contact.txt</tspan></text>
  <text x="352" y="356" class="label">email:     <tspan class="value">{{{{EMAIL}}}}</tspan></text>
  <text x="352" y="376" class="label">linkedin:  <tspan class="value">{{{{LINKEDIN}}}}</tspan></text>
  <text x="352" y="396" class="label">portfolio: <tspan class="value">{{{{PORTFOLIO}}}}</tspan></text>

  <text x="352" y="428" class="prompt">$ <tspan class="cursor">&#9612;</tspan>
    <animate attributeName="opacity" values="1;0;1" dur="1.2s" repeatCount="indefinite"/>
  </text>

  <text x="{CARD_WIDTH - 20}" y="{CARD_HEIGHT - 12}" text-anchor="end" class="titletext" font-size="11">updated {{{{LAST_UPDATED}}}}</text>
</svg>
"""
    return svg


def main():
    for theme in ("dark", "light"):
        svg = build_template(theme)
        out_path = f"{theme}_mode_template.svg"
        with open(out_path, "w") as f:
            f.write(svg)
        print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()