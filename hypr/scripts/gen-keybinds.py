#!/usr/bin/env python3
"""Generate the Hyprland cheat sheet.

Reads ~/.config/hypr/keybindings.json and produces either:
  pdf   -> ~/Documents/Hyprland-Keybindings.pdf (Catppuccin Mocha)
  rofi  -> pango-markup rows for the Super+/ overlay
  text  -> plain text rows (debugging)
"""

import json
import math
import os
import sys
from datetime import date

import gi

gi.require_version("Pango", "1.0")
gi.require_version("PangoCairo", "1.0")

from gi.repository import Pango, PangoCairo  # noqa: E402

import cairo  # noqa: E402

HOME = os.path.expanduser("~")
DATA = os.path.join(HOME, ".config/hypr/keybindings.json")
OUT_PDF = os.path.join(HOME, "Documents/Hyprland-Keybindings.pdf")

# ---------------------------------------------------------------- palette ----
HEX = {
    "rosewater": "f5e0dc",
    "flamingo": "f2cdcd",
    "pink": "f5c2e7",
    "mauve": "cba6f7",
    "red": "f38ba8",
    "maroon": "eba0ac",
    "peach": "fab387",
    "yellow": "f9e2af",
    "green": "a6e3a1",
    "teal": "94e2d5",
    "sky": "89dceb",
    "sapphire": "74c7ec",
    "blue": "89b4fa",
    "lavender": "b4befe",
    "text": "cdd6f4",
    "subtext1": "bac2de",
    "subtext0": "a6adc8",
    "overlay2": "9399b2",
    "overlay1": "7f849c",
    "overlay0": "6c7086",
    "surface2": "585b70",
    "surface1": "45475a",
    "surface0": "313244",
    "base": "1e1e2e",
    "mantle": "181825",
    "crust": "11111b",
}


def rgb(name):
    h = HEX[name]
    return tuple(int(h[i : i + 2], 16) / 255 for i in (0, 2, 4))


def rgba(name, alpha=1.0):
    return (*rgb(name), alpha)


BASE = rgb("base")
TEXT = rgb("text")
SUBTEXT = rgb("subtext1")
MUTED = rgb("subtext0")
FAINT = rgb("overlay0")
LAVENDER = rgb("lavender")
SURFACE0 = rgb("surface0")
MANTLE = rgb("mantle")

FONT = "GoogleSansCode Nerd Font"
MONO = "GoogleSansCode Nerd Font Mono"


# ------------------------------------------------------------------ pango ----
def make_layout(cr, text, size, family=FONT, weight=Pango.Weight.NORMAL,
                width=None, markup=False, spacing=0):
    layout = PangoCairo.create_layout(cr)
    desc = Pango.FontDescription()
    desc.set_family(family)
    desc.set_size(int(round(size * Pango.SCALE)))
    desc.set_weight(weight)
    layout.set_font_description(desc)
    if spacing:
        layout.set_spacing(int(spacing * Pango.SCALE))
    if width is not None:
        layout.set_width(int(width * Pango.SCALE))
        layout.set_wrap(Pango.WrapMode.WORD_CHAR)
    if markup:
        layout.set_markup(text, -1)
    else:
        layout.set_text(text, -1)
    return layout


def layout_px(layout):
    w, h = layout.get_size()
    return w / Pango.SCALE, h / Pango.SCALE


def draw_layout(cr, layout, x, y, color, alpha=1.0):
    cr.save()
    cr.move_to(x, y)
    cr.set_source_rgba(*color, alpha)
    PangoCairo.show_layout(cr, layout)
    cr.restore()


# ---------------------------------------------------------------- shapes ----
def rounded_rect(cr, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    cr.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    cr.close_path()


def fill_round(cr, x, y, w, h, r, color):
    cr.save()
    rounded_rect(cr, x, y, w, h, r)
    cr.set_source_rgba(*color)
    cr.fill()
    cr.restore()


def stroke_round(cr, x, y, w, h, r, color, width=1.0):
    cr.save()
    rounded_rect(cr, x, y, w, h, r)
    cr.set_line_width(width)
    cr.set_source_rgba(*color)
    cr.stroke()
    cr.restore()


# --------------------------------------------------------------- keycaps ----
KEYMAP = {
    "Super": "Super",
    "Shift": "⇧",
    "Alt": "⌥",
    "Ctrl": "Ctrl",
    "Return": "↵",
    "Escape": "Esc",
    "Slash": "/",
    "Period": ".",
    "Comma": ",",
    "Plus": "+",
    "Minus": "−",
    "Arrows": "← ↑ ↓ →",
    "Print": "PrtSc",
    "1…0": "1…0",
    "Scroll ↑↓": "Scroll ↑↓",
    "Mouse drag": "Drag",
    "Right-drag": "Right-drag",
}

PILL_H = 17.0
PILL_PAD = 6.5
PILL_GAP = 3.0
PILL_FONT = 7.6


def pill_width(cr, label):
    lay = make_layout(cr, label, PILL_FONT, family=MONO, weight=Pango.Weight.BOLD)
    w, _ = layout_px(lay)
    return w + PILL_PAD * 2


def draw_pill(cr, label, x, y, w=None):
    if w is None:
        w = pill_width(cr, label)
    fill_round(cr, x, y, w, PILL_H, 5, rgba("surface0", 0.95))
    stroke_round(cr, x, y, w, PILL_H, 5, rgba("lavender", 0.20), 0.8)
    lay = make_layout(cr, label, PILL_FONT, family=MONO, weight=Pango.Weight.BOLD)
    tw, th = layout_px(lay)
    draw_layout(cr, lay, x + (w - tw) / 2, y + (PILL_H - th) / 2, LAVENDER)
    return w


def bind_pills(cr, bind, x, y, max_width):
    labels = [KEYMAP.get(k, k) for k in bind["keys"]]
    widths = [pill_width(cr, label) for label in labels]
    total = sum(widths) + PILL_GAP * (len(widths) - 1)
    if total > max_width:
        # Fall back to one compact pill.
        label = " + ".join(labels)
        w = pill_width(cr, label)
        if w > max_width:
            label = label.replace(" + ", "+")
            w = pill_width(cr, label)
        draw_pill(cr, label, x, y, w)
        return w
    cx = x
    for label, w in zip(labels, widths):
        draw_pill(cr, label, cx, y, w)
        cx += w + PILL_GAP
    return cx - x - PILL_GAP


# ------------------------------------------------------------------ cards ----
CARD_GAP = 9
CARD_PAD = 16
CARD_HEADER = 38
ROW_GAP = 6.5

ACCENTS = {
    "blue": rgb("blue"),
    "mauve": rgb("mauve"),
    "teal": rgb("teal"),
    "lavender": rgb("lavender"),
    "peach": rgb("peach"),
    "green": rgb("green"),
    "pink": rgb("pink"),
    "sky": rgb("sky"),
}


def bind_row_height(cr, bind, inner_w):
    # Reserve up to 55% for keys, but never less than the longest pill.
    labels = [KEYMAP.get(k, k) for k in bind["keys"]]
    pill_w = sum(pill_width(cr, l) for l in labels) + PILL_GAP * (len(labels) - 1)
    single_w = pill_width(cr, " + ".join(labels))
    keys_w = min(max(pill_w, single_w), inner_w * 0.55)
    desc_w = max(60, inner_w - keys_w - 9)
    lay = make_layout(cr, bind["desc"], 8.4, width=desc_w)
    _, dh = layout_px(lay)
    return max(PILL_H, dh) + ROW_GAP, keys_w, desc_w


def card_height(cr, card, width):
    inner_w = width - CARD_PAD * 2
    if card["kind"] == "note":
        total = CARD_HEADER + 2
        for line in card["lines"]:
            lay = make_layout(cr, line, 8.3, width=inner_w)
            _, lh = layout_px(lay)
            total += lh + 5
        return total + 6
    total = CARD_HEADER
    for bind in card["binds"]:
        h, _, _ = bind_row_height(cr, bind, inner_w)
        total += h
    return total + 6


def draw_card(cr, card, x, y, width, height):
    fill_round(cr, x, y, width, height, 13, rgba("mantle", 0.82))
    stroke_round(cr, x, y, width, height, 13, rgba("lavender", 0.16), 1)

    accent = ACCENTS.get(card.get("accent", "lavender"), LAVENDER)
    # Accent bar + title.
    fill_round(cr, x + CARD_PAD, y + 15, 3.5, 12, 2, (*accent, 0.95))
    title = make_layout(cr, card["name"].upper(), 9.6, weight=Pango.Weight.BOLD, spacing=1.1)
    draw_layout(cr, title, x + CARD_PAD + 11, y + 12, TEXT)
    if "count" in card:
        c = make_layout(cr, str(card["count"]), 8.2, family=MONO, weight=Pango.Weight.BOLD)
        cw, ch = layout_px(c)
        draw_layout(cr, c, x + width - CARD_PAD - cw, y + 14, FAINT, 0.95)

    inner_w = width - CARD_PAD * 2
    cy = y + CARD_HEADER - 2

    if card["kind"] == "note":
        for line in card["lines"]:
            lay = make_layout(cr, line, 8.3, width=inner_w)
            _, lh = layout_px(lay)
            draw_layout(cr, lay, x + CARD_PAD, cy, MUTED, 0.98)
            cy += lh + 5
        return

    for bind in card["binds"]:
        h, keys_w, desc_w = bind_row_height(cr, bind, inner_w)
        # Keycaps, vertically centred against the description block.
        desc_lay = make_layout(cr, bind["desc"], 8.4, width=desc_w)
        _, dh = layout_px(desc_lay)
        row_mid = cy + h / 2
        pill_y = row_mid - PILL_H / 2
        bind_pills(cr, bind, x + CARD_PAD, pill_y, keys_w)
        desc_y = row_mid - dh / 2
        draw_layout(cr, desc_lay, x + CARD_PAD + keys_w + 9, desc_y, SUBTEXT, 0.98)
        cy += h


# ------------------------------------------------------------------- page ----
PAGE_W, PAGE_H = 842.0, 595.0
MARGIN = 30.0
HEADER_TOP = 30.0
CONTENT_TOP = 130.0
CONTENT_BOTTOM = PAGE_H - 34.0
COL_GAP = 16.0
COLS = 2
COL_W = (PAGE_W - MARGIN * 2 - COL_GAP * (COLS - 1)) / COLS


def page_background(cr):
    cr.set_source_rgb(*BASE)
    cr.paint()

    # Soft aurora glows.
    for cx, cy, rad, color, alpha in (
        (70, 10, 300, rgb("lavender"), 0.085),
        (760, 560, 340, rgb("mauve"), 0.065),
        (430, -60, 260, rgb("blue"), 0.050),
    ):
        grad = cairo.RadialGradient(cx, cy, 0, cx, cy, rad)
        grad.add_color_stop_rgba(0, *color, alpha)
        grad.add_color_stop_rgba(1, *color, 0)
        cr.set_source(grad)
        cr.paint()

    # Subtle dot grid.
    cr.set_source_rgba(*LAVENDER, 0.035)
    step = 26
    for gx in range(int(MARGIN), int(PAGE_W), step):
        for gy in range(int(CONTENT_TOP), int(CONTENT_BOTTOM), step):
            cr.arc(gx, gy, 0.7, 0, 2 * math.pi)
            cr.fill()


def draw_header(cr, data):
    eyebrow = make_layout(cr, data["eyebrow"], 7.6, family=MONO, weight=Pango.Weight.BOLD, spacing=1.4)
    draw_layout(cr, eyebrow, MARGIN, HEADER_TOP + 2, FAINT)

    title = make_layout(
        cr,
        f"<span foreground='#{HEX['lavender']}'>Hyprland</span> Keybindings",
        30,
        weight=Pango.Weight.BOLD,
        markup=True,
    )
    draw_layout(cr, title, MARGIN, HEADER_TOP + 14, TEXT)

    subtitle = make_layout(cr, data["subtitle"], 8.6, width=500)
    draw_layout(cr, subtitle, MARGIN, HEADER_TOP + 67, MUTED, 0.98)

    # Right-hand shortcut hint.
    label = make_layout(cr, "OPEN THE LIVE CHEAT SHEET", 7.0, family=MONO, weight=Pango.Weight.BOLD, spacing=0.8)
    lw, _ = layout_px(label)
    right = PAGE_W - MARGIN
    draw_layout(cr, label, right - lw, HEADER_TOP + 12, FAINT)

    keys = ["Super", "Slash"]
    widths = [pill_width(cr, KEYMAP[k]) + 3 for k in keys]
    total = sum(widths)
    kx = right - total
    for k, w in zip(keys, widths):
        draw_pill(cr, KEYMAP[k], kx, HEADER_TOP + 26, w)
        kx += w

    hint = make_layout(cr, "rofi overlay · searchable", 7.8)
    hw, _ = layout_px(hint)
    draw_layout(cr, hint, right - hw, HEADER_TOP + 48, MUTED, 0.9)

    # Hairline under the header.
    cr.set_source_rgba(*LAVENDER, 0.10)
    cr.set_line_width(0.8)
    cr.move_to(MARGIN, CONTENT_TOP - 13)
    cr.line_to(PAGE_W - MARGIN, CONTENT_TOP - 13)
    cr.stroke()


def draw_footer(cr, data, page, pages):
    cr.set_source_rgba(*LAVENDER, 0.10)
    cr.set_line_width(0.8)
    cr.move_to(MARGIN, PAGE_H - 26)
    cr.line_to(PAGE_W - MARGIN, PAGE_H - 26)
    cr.stroke()

    left = make_layout(cr, data["footer"] + "   ·   regenerate with gen-keybinds.py", 7.0, family=MONO)
    draw_layout(cr, left, MARGIN, PAGE_H - 20, FAINT, 0.9)

    right_text = f"{page} / {pages}"
    right = make_layout(cr, right_text, 7.4, family=MONO, weight=Pango.Weight.BOLD)
    rw, _ = layout_px(right)
    draw_layout(cr, right, PAGE_W - MARGIN - rw, PAGE_H - 20, MUTED, 0.9)


def build_cards(data):
    cards = []

    # A short intro sits above the categories; the core layout rules sit next to
    # the focus card. Both are compact enough to keep the sheet to two pages.
    intro = {
        "kind": "note",
        "id": "intro",
        "name": "Good to know",
        "accent": "yellow",
        "lines": [
            "Super + / opens this cheat sheet as a searchable rofi overlay.",
            "Super + L switches dwindle ↔ scrolling; it resets to dwindle on reload.",
            "Scrolling: Shift + H/L swap columns; Shift + J/K dock the column left at 50%.",
            "Alt + H/L also swap columns; Alt + J toggles the split direction in dwindle.",
        ],
    }

    cards.append(intro)
    for cat in data["categories"]:
        cards.append(
            {
                "kind": "category",
                "id": cat["id"],
                "name": cat["name"],
                "accent": cat.get("accent", "lavender"),
                "binds": cat["binds"],
                "count": len(cat["binds"]),
            }
        )
        if cat["id"] == "focus":
            cards.append(
                {
                    "kind": "note",
                    "id": "layouts-explained",
                    "name": "Two layouts",
                    "accent": "mauve",
                    "lines": [
                        "Dwindle · windows split the focused pane into a tree.",
                        "Scrolling · windows line up as columns on a horizontal strip.",
                    ],
                }
            )
    return cards


def paginate(cr, cards):
    capacity = CONTENT_BOTTOM - CONTENT_TOP
    columns = []
    col = []
    used = 0.0
    for card in cards:
        h = card_height(cr, card, COL_W)
        need = h if not col else h + CARD_GAP
        if col and used + need > capacity:
            columns.append((col, used))
            col = []
            used = 0.0
            need = h
        col.append((card, h))
        used += need
    if col:
        columns.append((col, used))

    # Each page is filled column by column; a short page simply has fewer
    # columns instead of flowing cards vertically across pages.
    return [columns[i : i + COLS] for i in range(0, len(columns), COLS)]


def render_pdf(data, path):
    cards = build_cards(data)
    surface = cairo.PDFSurface(path, PAGE_W, PAGE_H)
    cr = cairo.Context(surface)
    cr.set_antialias(cairo.ANTIALIAS_BEST)

    pages = paginate(cr, cards)
    total = len(pages)

    for index, columns in enumerate(pages, start=1):
        page_background(cr)
        draw_header(cr, data)
        for ci, (col, used) in enumerate(columns):
            x = MARGIN + ci * (COL_W + COL_GAP)
            y = CONTENT_TOP
            for card, h in col:
                draw_card(cr, card, x, y, COL_W, h)
                y += h + CARD_GAP
        draw_footer(cr, data, index, total)
        cr.show_page()

    surface.finish()
    return path, total


# --------------------------------------------------------------- rofi/text ----
def escape(text):
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def key_label(bind):
    return " + ".join(KEYMAP.get(k, k) for k in bind["keys"])


def render_rofi(data):
    rows = []
    for cat in data["categories"]:
        rows.append(
            f"<span foreground='#{HEX['overlay0']}' weight='bold' size='small'>"
            f"▎ {escape(cat['name'].upper())}</span>"
        )
        for bind in cat["binds"]:
            keys = escape(key_label(bind))
            desc = escape(bind["desc"])
            rows.append(
                f"<span foreground='#{HEX['lavender']}' weight='bold'>{keys}</span>"
                f"<span foreground='#{HEX['overlay0']}'>   ·   </span>"
                f"<span foreground='#{HEX['text']}'>{desc}</span>"
            )
    return "\n".join(rows)


def render_text(data):
    rows = []
    for cat in data["categories"]:
        rows.append(f"## {cat['name']}")
        for bind in cat["binds"]:
            rows.append(f"{key_label(bind):<30} {bind['desc']}")
        rows.append("")
    return "\n".join(rows)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "pdf"
    with open(DATA, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    if mode == "rofi":
        print(render_rofi(data))
        return
    if mode == "text":
        print(render_text(data))
        return

    os.makedirs(os.path.dirname(OUT_PDF), exist_ok=True)
    path, pages = render_pdf(data, OUT_PDF)
    print(f"{path} ({pages} pages)")


if __name__ == "__main__":
    main()
