#!/usr/bin/env python3
"""Translate HyDE theme colours into the mechabar waybar palette."""
from __future__ import annotations

import argparse
import os
import re
import sys

Color = tuple[float, float, float, float]

HEX_RE = re.compile(r"^#([0-9a-fA-F]{3,8})$")
RGB_RE = re.compile(r"^rgba?\(\s*([0-9.]+)\s*,\s*([0-9.]+)\s*,\s*([0-9.]+)\s*(?:,\s*([0-9.]+)\s*)?\)$")
DEFINE_RE = re.compile(r"@define-color\s+([A-Za-z0-9_-]+)\s+([^;]+);")
KITTY_RE = re.compile(r"^\s*color([0-9]{1,2})\s+(#[0-9a-fA-F]{3,8})\s*$")


def parse_color(value: str) -> Color | None:
    value = value.strip()
    match = HEX_RE.match(value)
    if match:
        digits = match.group(1)
        if len(digits) == 3:
            digits = "".join(ch * 2 for ch in digits)
        if len(digits) == 6:
            digits += "ff"
        if len(digits) != 8:
            return None
        return tuple(int(digits[i : i + 2], 16) / 255.0 for i in range(0, 8, 2))  # type: ignore[return-value]
    match = RGB_RE.match(value)
    if match:
        r, g, b = (float(match.group(i)) / 255.0 for i in range(1, 4))
        a = float(match.group(4)) if match.group(4) is not None else 1.0
        return (r, g, b, a)
    return None


def read_theme_css(path: str) -> dict[str, Color]:
    colors: dict[str, Color] = {}
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            for line in handle:
                match = DEFINE_RE.search(line)
                if not match:
                    continue
                parsed = parse_color(match.group(2))
                if parsed:
                    colors[match.group(1)] = parsed
    except OSError:
        pass
    return colors


def read_kitty_palette(path: str) -> dict[int, Color]:
    palette: dict[int, Color] = {}
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            for line in handle:
                match = KITTY_RE.match(line)
                if not match:
                    continue
                parsed = parse_color(match.group(2))
                if parsed:
                    palette[int(match.group(1))] = parsed
    except OSError:
        pass
    return palette


def mix(a: Color, b: Color, t: float) -> Color:
    return tuple(a[i] * (1.0 - t) + b[i] * t for i in range(4))  # type: ignore[return-value]


BLACK: Color = (0.0, 0.0, 0.0, 1.0)
WHITE: Color = (1.0, 1.0, 1.0, 1.0)


def composite(fg: Color, bg: Color) -> Color:
    alpha = fg[3] + bg[3] * (1.0 - fg[3])
    if alpha == 0:
        return (0.0, 0.0, 0.0, 0.0)
    channels = [(fg[i] * fg[3] + bg[i] * bg[3] * (1.0 - fg[3])) / alpha for i in range(3)]
    return (channels[0], channels[1], channels[2], alpha)


def luminance(color: Color) -> float:
    return 0.2126 * color[0] + 0.7152 * color[1] + 0.0722 * color[2]


def css(color: Color) -> str:
    r, g, b, a = color
    if a >= 0.999:
        return "#{:02x}{:02x}{:02x}".format(round(r * 255), round(g * 255), round(b * 255))
    return "rgba({}, {}, {}, {:.2f})".format(round(r * 255), round(g * 255), round(b * 255), a)


def build(theme_css: str, kitty_theme: str, theme_name: str) -> str:
    colors = read_theme_css(theme_css)
    palette = read_kitty_palette(kitty_theme)

    base = colors.get("main-bg") or (0.07, 0.07, 0.11, 1.0)
    fg = colors.get("main-fg") or (0.80, 0.84, 0.96, 1.0)
    bar_bg = colors.get("bar-bg") or (0.0, 0.0, 0.0, 0.1)
    accent = colors.get("wb-act-bg") or fg
    hover_bg = colors.get("wb-hvr-bg") or mix(base, fg, 0.2)
    hover_fg = colors.get("wb-hvr-fg") or fg

    light = luminance(base) > 0.6
    if light:
        bg0 = mix(base, WHITE, 0.60)
        bg1 = mix(base, WHITE, 0.30)
        bg3 = mix(base, fg, 0.16)
    else:
        bg0 = mix(base, BLACK, 0.55)
        bg1 = mix(base, BLACK, 0.30)
        bg3 = mix(base, fg, 0.16)
    bg2 = base
    border = mix(fg, base, 0.50)
    shadow = mix(composite(bar_bg, base), BLACK, 0.10)

    warning = palette.get(3) or ((0.86, 0.60, 0.29, 1.0) if light else (0.98, 0.89, 0.69, 1.0))
    critical = palette.get(1) or ((0.82, 0.06, 0.22, 1.0) if light else (0.95, 0.55, 0.66, 1.0))
    charging = palette.get(2) or ((0.25, 0.63, 0.17, 1.0) if light else (0.65, 0.89, 0.63, 1.0))

    # palette names used by some mechabar modules / user snippets
    named = {
        "rosewater": palette.get(7, fg),
        "flamingo": palette.get(5, fg),
        "pink": palette.get(5, fg),
        "mauve": palette.get(5, accent),
        "red": critical,
        "maroon": critical,
        "peach": palette.get(3, warning),
        "yellow": warning,
        "green": charging,
        "teal": palette.get(6, palette.get(4, accent)),
        "sky": palette.get(6, palette.get(4, accent)),
        "sapphire": palette.get(4, accent),
        "blue": palette.get(4, accent),
        "lavender": accent,
        "text": fg,
        "subtext1": mix(fg, base, 0.20),
        "subtext0": border,
        "overlay2": mix(fg, base, 0.60),
        "overlay1": mix(fg, base, 0.70),
        "overlay0": mix(fg, base, 0.78),
        "surface2": mix(base, fg, 0.30),
        "surface1": mix(base, fg, 0.24),
        "surface0": bg3,
        "base": base,
        "mantle": bg1,
        "crust": bg0,
    }

    lines = [
        "/* Generated by HyDE -> mechabar bridge. Do not edit by hand. */",
        f"/* HyDE theme: {theme_name} */",
        "",
        "/* Palette */",
    ]
    for name, color in named.items():
        lines.append(f"@define-color {name:<12} {css(color)};")
    lines += [
        "",
        "/* Base colours */",
        f"@define-color accent       {css(accent)};",
        f"@define-color fg           {css(fg)};",
        f"@define-color bg_0         {css(bg0)};",
        f"@define-color bg_1         {css(bg1)};",
        f"@define-color bg_2         {css(bg2)};",
        f"@define-color bg_3         {css(bg3)};",
        f"@define-color border       {css(border)};",
        f"@define-color shadow       {css(shadow)};",
        "",
        "/* States */",
        f"@define-color warning      {css(warning)};",
        f"@define-color critical     {css(critical)};",
        f"@define-color charging     {css(charging)};",
        f"@define-color bg_alt       {css(hover_bg)};",
        f"@define-color fg_alt       {css(hover_fg)};",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--theme-css", default=os.path.expanduser("~/.config/waybar/theme.css"))
    parser.add_argument("--theme-dir", default="")
    parser.add_argument("--theme-name", default=os.environ.get("HYDE_THEME", "HyDE"))
    parser.add_argument("--out", default=os.path.expanduser("~/.config/waybar/themes/hyde.css"))
    args = parser.parse_args()

    kitty_theme = os.path.join(args.theme_dir, "kitty.theme") if args.theme_dir else ""
    if not os.path.isfile(args.theme_css):
        # fall back to the theme's own waybar.theme when colour.set has not run yet
        candidate = os.path.join(args.theme_dir, "waybar.theme") if args.theme_dir else ""
        if candidate and os.path.isfile(candidate):
            args.theme_css = candidate
    try:
        content = build(args.theme_css, kitty_theme, args.theme_name)
    except Exception as error:  # noqa: BLE001
        print(f"mechabar-sync: {error}", file=sys.stderr)
        return 1
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as handle:
        handle.write(content)
    print(f"mechabar-sync: wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
