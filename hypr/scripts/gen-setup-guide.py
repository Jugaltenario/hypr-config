#!/usr/bin/env python3
"""Render the README setup guide to a printable PDF.

The guide lives between the ``setup-guide:start`` and ``setup-guide:end``
markers in README.md, so this script and the README cannot drift apart.

Usage:
    gen-setup-guide.py [README.md] [output.pdf]

Default output: ~/Desktop/Setup-from-Zero.pdf
"""

import os
import re
import sys
from datetime import date
from pathlib import Path

import cairo
import gi

gi.require_version("Pango", "1.0")
gi.require_version("PangoCairo", "1.0")

from gi.repository import Pango, PangoCairo  # noqa: E402

HOME = Path.home()
DEFAULT_README = HOME / "hypr-config/README.md"
DEFAULT_PDF = HOME / "Desktop/Setup-from-Zero.pdf"

PAGE_W, PAGE_H = 595.276, 841.89  # A4 portrait, points
MARGIN = 52.0
CONTENT_W = PAGE_W - 2 * MARGIN
FIRST_TOP = 162.0
NORMAL_TOP = 62.0
BOTTOM = PAGE_H - 54.0

BODY = "Noto Sans"
MONO = "JetBrainsMono Nerd Font"
BODY_SIZE = 10.0
CODE_SIZE = 8.2
TABLE_SIZE = 9.2

TEXT = (0.12, 0.14, 0.19)
MUTED = (0.36, 0.40, 0.47)
FAINT = (0.52, 0.56, 0.62)
ACCENT = (0.38, 0.24, 0.66)
ACCENT_LIGHT = (0.55, 0.42, 0.80)
RULE = (0.89, 0.90, 0.93)
CODE_BG = (0.955, 0.958, 0.972)
CODE_BORDER = (0.88, 0.89, 0.93)
CODE_TEXT = (0.24, 0.18, 0.40)
TABLE_HEAD = (0.955, 0.945, 0.985)
TABLE_ALT = (0.985, 0.985, 0.99)

CODE_PAD_X, CODE_PAD_Y = 10.0, 8.0
CELL_PAD_X, CELL_PAD_Y = 8.0, 6.0


def rgba(color, alpha=1.0):
    return (color[0], color[1], color[2], alpha)


def escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


TOKEN_RE = re.compile(r"(`[^`]+`|\*\*[^*]+\*\*|\[[^\]]+\]\([^)]+\))")


def code_span(text):
    return f'<span font_family="{MONO}" foreground="#5a3fa0">{escape(text)}</span>'


def bold_span(text):
    """Render bold text, still honouring inline code inside it."""
    out = []
    pos = 0
    for match in re.finditer(r"`[^`]+`", text):
        out.append(escape(text[pos : match.start()]))
        out.append(code_span(match.group(0)[1:-1]))
        pos = match.end()
    out.append(escape(text[pos:]))
    return "<b>" + "".join(out) + "</b>"


def inline_markup(text):
    """Convert the small inline subset used in README to Pango markup."""
    out = []
    pos = 0
    for match in TOKEN_RE.finditer(text):
        out.append(escape(text[pos : match.start()]))
        token = match.group(0)
        if token.startswith("`"):
            out.append(code_span(token[1:-1]))
        elif token.startswith("**"):
            out.append(bold_span(token[2:-2]))
        else:
            label, url = re.match(r"\[([^\]]+)\]\(([^)]+)\)", token).groups()
            out.append(escape(label) + " (" + escape(url) + ")")
        pos = match.end()
    out.append(escape(text[pos:]))
    return "".join(out)


def make_layout(
    cr,
    text,
    size,
    family=BODY,
    weight=Pango.Weight.NORMAL,
    style=Pango.Style.NORMAL,
    width=None,
    markup=False,
    spacing=0.0,
):
    layout = PangoCairo.create_layout(cr)
    desc = Pango.FontDescription()
    desc.set_family(family)
    desc.set_size(int(size * Pango.SCALE))
    desc.set_weight(weight)
    desc.set_style(style)
    layout.set_font_description(desc)
    if markup:
        layout.set_markup(text, -1)
    else:
        layout.set_text(text, -1)
    if width is not None:
        layout.set_width(int(width * Pango.SCALE))
        layout.set_wrap(Pango.WrapMode.WORD_CHAR)
    layout.set_spacing(int(spacing * Pango.SCALE))
    return layout


def measure(layout):
    _, height = layout.get_pixel_size()
    return height


def extract_guide(text):
    start = text.find("<!-- setup-guide:start -->")
    end = text.find("<!-- setup-guide:end -->")
    if start == -1 or end == -1 or end <= start:
        raise SystemExit("README is missing the setup-guide start/end markers")
    return text[start + len("<!-- setup-guide:start -->") : end]


def parse_blocks(text):
    lines = text.splitlines()
    blocks = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
            continue

        fence = re.match(r"^(\s*)```", line)
        if fence:
            indent = len(fence.group(1))
            i += 1
            code = []
            while i < len(lines) and not re.match(r"^\s*```", lines[i]):
                code_line = lines[i]
                if indent and code_line.startswith(" " * indent):
                    code_line = code_line[indent:]
                code.append(code_line.rstrip())
                i += 1
            i += 1  # closing fence
            blocks.append({"kind": "code", "lines": code})
            continue

        heading = re.match(r"^(#{2,4})\s+(.*)$", line)
        if heading:
            level = len(heading.group(1))
            label = heading.group(2).strip()
            if level == 2 and label.lower() == "from zero" and not blocks:
                i += 1
                continue
            blocks.append({"kind": f"h{level}", "text": label})
            i += 1
            continue

        if stripped.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [
                    cell.strip()
                    for cell in lines[i].strip().strip("|").split("|")
                ]
                if not all(re.fullmatch(r":?-{2,}:?", cell) for cell in cells):
                    rows.append(cells)
                i += 1
            if rows:
                blocks.append({"kind": "table", "rows": rows})
            continue

        if stripped.startswith(">"):
            parts = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                parts.append(re.sub(r"^\s*>\s?", "", lines[i]).strip())
                i += 1
            blocks.append({"kind": "quote", "text": " ".join(p for p in parts if p)})
            continue

        bullet = re.match(r"^\s*[-*]\s+(.*)$", line)
        if bullet:
            item = bullet.group(1).strip()
            i += 1
            while i < len(lines):
                nxt = lines[i]
                if not nxt.strip() or re.match(
                    r"^\s*(```|#{2,4}\s|[-*]\s|\d+\.\s|\||>)", nxt
                ):
                    break
                if nxt.startswith((" ", "\t")):
                    item += " " + nxt.strip()
                    i += 1
                else:
                    break
            blocks.append({"kind": "bullet", "text": item})
            continue

        numbered = re.match(r"^\s*(\d+)\.\s+(.*)$", line)
        if numbered:
            number = int(numbered.group(1))
            item = numbered.group(2).strip()
            i += 1
            while i < len(lines):
                nxt = lines[i]
                if not nxt.strip() or re.match(
                    r"^\s*(```|#{2,4}\s|[-*]\s|\d+\.\s|\||>)", nxt
                ):
                    break
                if nxt.startswith((" ", "\t")):
                    item += " " + nxt.strip()
                    i += 1
                else:
                    break
            blocks.append({"kind": "num", "num": number, "text": item})
            continue

        parts = [stripped]
        i += 1
        while i < len(lines):
            nxt = lines[i]
            if not nxt.strip() or re.match(
                r"^\s*(```|#{2,4}\s|[-*]\s|\d+\.\s|\||>)", nxt
            ):
                break
            parts.append(nxt.strip())
            i += 1
        blocks.append({"kind": "para", "text": " ".join(parts)})

    return blocks


def code_font_size(cr, lines, width):
    """Largest size at or below CODE_SIZE that keeps every line unwrapped."""
    inner = width - 2 * CODE_PAD_X
    size = CODE_SIZE
    while size > 6.8:
        widest = 0.0
        for line in lines:
            if not line:
                continue
            lay = make_layout(cr, line, size, family=MONO)
            widest = max(widest, lay.get_pixel_size()[0])
        if widest <= inner:
            break
        size = round(size - 0.1, 1)
    return size


def block_height(cr, block, width):
    kind = block["kind"]
    if kind == "para":
        lay = make_layout(
            cr, inline_markup(block["text"]), BODY_SIZE, width=width, markup=True, spacing=1.6
        )
        return measure(lay)
    if kind == "h2":
        lay = make_layout(
            cr,
            inline_markup(block["text"]),
            15.5,
            weight=Pango.Weight.BOLD,
            width=width - 12,
            markup=True,
            spacing=1.0,
        )
        return measure(lay)
    if kind == "h3":
        lay = make_layout(
            cr,
            inline_markup(block["text"]),
            12.0,
            weight=Pango.Weight.BOLD,
            width=width - 4,
            markup=True,
            spacing=1.0,
        )
        return measure(lay)
    if kind == "code":
        inner = width - 2 * CODE_PAD_X
        size = code_font_size(cr, block["lines"], width)
        total = 0.0
        for line in block["lines"]:
            if not line:
                total += size * 1.35
            else:
                lay = make_layout(cr, line, size, family=MONO, width=inner, spacing=1.8)
                total += measure(lay)
        return total + 2 * CODE_PAD_Y
    if kind == "quote":
        lay = make_layout(
            cr,
            inline_markup(block["text"]),
            BODY_SIZE,
            style=Pango.Style.ITALIC,
            width=width - 18,
            markup=True,
            spacing=1.6,
        )
        return measure(lay)
    if kind == "bullet":
        lay = make_layout(
            cr,
            inline_markup(block["text"]),
            BODY_SIZE,
            width=width - 16,
            markup=True,
            spacing=1.6,
        )
        return measure(lay)
    if kind == "num":
        lay = make_layout(
            cr,
            inline_markup(block["text"]),
            BODY_SIZE,
            width=width - 24,
            markup=True,
            spacing=1.6,
        )
        return measure(lay)
    if kind == "table":
        return table_height(cr, block["rows"], width)
    return 0.0


def table_columns(cr, rows, width):
    widest = [0.0, 0.0]
    for row in rows:
        for index, cell in enumerate(row[:2]):
            lay = make_layout(cr, inline_markup(cell), TABLE_SIZE, markup=True)
            widest[index] = max(widest[index], lay.get_pixel_size()[0])
    first = min(widest[0] + 2 * CELL_PAD_X, width * 0.42)
    first = max(first, 120.0)
    return first, width - first


def table_height(cr, rows, width):
    col_w = table_columns(cr, rows, width)
    total = 0.0
    for row_index, row in enumerate(rows):
        height = 0.0
        for col_index, cell in enumerate(row[:2]):
            lay = make_layout(
                cr,
                inline_markup(cell),
                TABLE_SIZE,
                width=col_w[col_index] - 2 * CELL_PAD_X,
                markup=True,
            )
            height = max(height, measure(lay))
        total += height + 2 * CELL_PAD_Y
        if row_index == 0:
            total += 1.0
    return total + 1.0


def space_for(block, first_on_page):
    if first_on_page:
        return 0.0
    return {
        "h2": 14.0,
        "h3": 10.0,
        "para": 3.0,
        "bullet": 2.0,
        "num": 2.0,
        "code": 5.0,
        "quote": 5.0,
        "table": 6.0,
    }.get(block["kind"], 3.0)


def paginate(cr, blocks):
    pages = []
    current = []
    y = 0.0
    page_no = 0
    for index, block in enumerate(blocks):
        capacity = (BOTTOM - FIRST_TOP) if page_no == 0 else (BOTTOM - NORMAL_TOP)
        gap = space_for(block, not current)
        height = block_height(cr, block, CONTENT_W)
        keep_with_next = block["kind"] in ("h2", "h3") or (
            block["kind"] == "para" and block["text"].rstrip().endswith(":")
        )
        lookahead = 0.0
        if keep_with_next and index + 1 < len(blocks):
            nxt = blocks[index + 1]
            lookahead = block_height(cr, nxt, CONTENT_W) + space_for(nxt, False)
        if block["kind"] == "h2":
            lookahead = max(lookahead, 140.0)
        elif block["kind"] == "h3":
            lookahead = max(lookahead, 80.0)
        lookahead = min(lookahead, 180.0)
        if current and y + gap + height + lookahead > capacity:
            pages.append(current)
            current = []
            y = 0.0
            page_no += 1
            gap = 0.0
        current.append((block, y + gap))
        y += gap + height
    if current:
        pages.append(current)
    return pages


def rounded_rect(cr, x, y, width, height, radius, fill, stroke=None):
    radius = min(radius, width / 2, height / 2)
    cr.new_sub_path()
    cr.arc(x + width - radius, y + radius, radius, -1.5708, 0)
    cr.arc(x + width - radius, y + height - radius, radius, 0, 1.5708)
    cr.arc(x + radius, y + height - radius, radius, 1.5708, 3.1416)
    cr.arc(x + radius, y + radius, radius, 3.1416, 4.7124)
    cr.close_path()
    cr.set_source_rgba(*fill)
    cr.fill_preserve()
    if stroke:
        cr.set_source_rgba(*stroke)
        cr.set_line_width(0.8)
        cr.stroke()
    else:
        cr.new_path()


def draw_text(cr, layout, x, y, color=TEXT):
    cr.set_source_rgba(*rgba(color))
    cr.move_to(x, y)
    PangoCairo.show_layout(cr, layout)


def draw_title(cr):
    draw_text(
        cr,
        make_layout(
            cr,
            "CACHYOS / ARCH  \u2192  HYPRLAND",
            8.5,
            weight=Pango.Weight.BOLD,
        ),
        MARGIN,
        46,
        ACCENT,
    )
    draw_text(
        cr,
        make_layout(
            cr, "Setup from Zero", 30.0, weight=Pango.Weight.BOLD, spacing=1.0
        ),
        MARGIN,
        66,
        TEXT,
    )
    draw_text(
        cr,
        make_layout(
            cr,
            "Every step from a bare machine to this exact desktop.",
            11.0,
            style=Pango.Style.ITALIC,
        ),
        MARGIN,
        112,
        MUTED,
    )
    cr.set_source_rgba(*rgba(RULE))
    cr.set_line_width(1.2)
    cr.move_to(MARGIN, 140)
    cr.line_to(PAGE_W - MARGIN, 140)
    cr.stroke()


def draw_header_footer(cr, page, total, show_header=True):
    if show_header:
        draw_text(
            cr,
            make_layout(cr, "hypr-config", 8.0, weight=Pango.Weight.BOLD),
            MARGIN,
            28,
            ACCENT,
        )
        header = make_layout(cr, "Setup from Zero", 8.0)
        hw = header.get_pixel_size()[0]
        draw_text(cr, header, PAGE_W - MARGIN - hw, 28, MUTED)

        cr.set_source_rgba(*rgba(RULE))
        cr.set_line_width(0.7)
        cr.move_to(MARGIN, 38)
        cr.line_to(PAGE_W - MARGIN, 38)
        cr.stroke()

    cr.move_to(MARGIN, PAGE_H - 42)
    cr.line_to(PAGE_W - MARGIN, PAGE_H - 42)
    cr.stroke()

    draw_text(
        cr,
        make_layout(cr, f"Generated from README.md  ·  {date.today().isoformat()}", 7.8),
        MARGIN,
        PAGE_H - 30,
        FAINT,
    )
    label = make_layout(cr, f"Page {page} of {total}", 7.8)
    lw = label.get_pixel_size()[0]
    draw_text(cr, label, PAGE_W - MARGIN - lw, PAGE_H - 30, FAINT)


def draw_block(cr, block, x, y, width):
    kind = block["kind"]

    if kind == "h2":
        cr.set_source_rgba(*rgba(ACCENT))
        cr.rectangle(x, y + 3, 3.0, 13.0)
        cr.fill()
        lay = make_layout(
            cr,
            inline_markup(block["text"]),
            15.5,
            weight=Pango.Weight.BOLD,
            width=width - 12,
            markup=True,
            spacing=1.0,
        )
        draw_text(cr, lay, x + 11, y, TEXT)
        return

    if kind == "h3":
        lay = make_layout(
            cr,
            inline_markup(block["text"]),
            12.0,
            weight=Pango.Weight.BOLD,
            width=width - 4,
            markup=True,
            spacing=1.0,
        )
        draw_text(cr, lay, x, y, ACCENT)
        return

    if kind == "para":
        lay = make_layout(
            cr, inline_markup(block["text"]), BODY_SIZE, width=width, markup=True, spacing=1.6
        )
        draw_text(cr, lay, x, y, TEXT)
        return

    if kind == "quote":
        height = block_height(cr, block, width)
        cr.set_source_rgba(*rgba(ACCENT_LIGHT, 0.55))
        cr.rectangle(x, y, 2.8, height)
        cr.fill()
        lay = make_layout(
            cr,
            inline_markup(block["text"]),
            BODY_SIZE,
            style=Pango.Style.ITALIC,
            width=width - 18,
            markup=True,
            spacing=1.6,
        )
        draw_text(cr, lay, x + 12, y, MUTED)
        return

    if kind == "bullet":
        lay = make_layout(
            cr,
            inline_markup(block["text"]),
            BODY_SIZE,
            width=width - 16,
            markup=True,
            spacing=1.6,
        )
        draw_text(cr, make_layout(cr, "\u2022", BODY_SIZE, weight=Pango.Weight.BOLD), x + 2, y, ACCENT)
        draw_text(cr, lay, x + 16, y, TEXT)
        return

    if kind == "num":
        lay = make_layout(
            cr,
            inline_markup(block["text"]),
            BODY_SIZE,
            width=width - 24,
            markup=True,
            spacing=1.6,
        )
        marker = make_layout(
            cr, f"{block['num']}.", BODY_SIZE, weight=Pango.Weight.BOLD
        )
        mw = marker.get_pixel_size()[0]
        draw_text(cr, marker, x + 24 - mw - 5, y, ACCENT)
        draw_text(cr, lay, x + 24, y, TEXT)
        return

    if kind == "code":
        height = block_height(cr, block, width)
        rounded_rect(
            cr,
            x,
            y,
            width,
            height,
            6,
            rgba(CODE_BG),
            rgba(CODE_BORDER),
        )
        inner = width - 2 * CODE_PAD_X
        size = code_font_size(cr, block["lines"], width)
        cy = y + CODE_PAD_Y
        for line in block["lines"]:
            if not line:
                cy += size * 1.35
                continue
            lay = make_layout(
                cr, line, size, family=MONO, width=inner, spacing=1.8
            )
            draw_text(cr, lay, x + CODE_PAD_X, cy, CODE_TEXT)
            cy += measure(lay)
        return

    if kind == "table":
        draw_table(cr, block["rows"], x, y, width)
        return


def draw_table(cr, rows, x, y, width):
    col0, col1 = table_columns(cr, rows, width)
    col_w = [col0, col1]
    cy = y
    for row_index, row in enumerate(rows):
        cells = row[:2] + [""] * (2 - len(row[:2]))
        layouts = []
        row_height = 0.0
        for index, cell in enumerate(cells):
            lay = make_layout(
                cr,
                inline_markup(cell),
                TABLE_SIZE,
                weight=Pango.Weight.BOLD if row_index == 0 else Pango.Weight.NORMAL,
                width=col_w[index] - 2 * CELL_PAD_X,
                markup=True,
            )
            layouts.append(lay)
            row_height = max(row_height, measure(lay))
        row_height += 2 * CELL_PAD_Y

        if row_index == 0:
            cr.set_source_rgba(*rgba(TABLE_HEAD))
            cr.rectangle(x, cy, width, row_height)
            cr.fill()
        elif row_index % 2 == 0:
            cr.set_source_rgba(*rgba(TABLE_ALT))
            cr.rectangle(x, cy, width, row_height)
            cr.fill()

        cr.set_source_rgba(*rgba(RULE))
        cr.set_line_width(0.7)
        cr.move_to(x, cy + row_height)
        cr.line_to(x + width, cy + row_height)
        cr.stroke()

        cx = x
        for index, lay in enumerate(layouts):
            draw_text(
                cr,
                lay,
                cx + CELL_PAD_X,
                cy + CELL_PAD_Y,
                ACCENT if row_index == 0 else TEXT,
            )
            cx += col_w[index]
        cy += row_height

    cr.set_source_rgba(*rgba(RULE))
    cr.set_line_width(0.7)
    cr.rectangle(x, y, width, cy - y)
    cr.stroke()


def render(readme_path, output_path):
    text = readme_path.read_text(encoding="utf-8")
    blocks = parse_blocks(extract_guide(text))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    surface = cairo.PDFSurface(str(output_path), PAGE_W, PAGE_H)
    cr = cairo.Context(surface)
    cr.set_line_join(cairo.LINE_JOIN_ROUND)
    cr.set_line_cap(cairo.LINE_CAP_ROUND)

    pages = paginate(cr, blocks)
    total = len(pages)

    for page_index, page in enumerate(pages):
        if page_index:
            cr.show_page()
        draw_header_footer(cr, page_index + 1, total, show_header=page_index > 0)
        if page_index == 0:
            draw_title(cr)
            top = FIRST_TOP
        else:
            top = NORMAL_TOP
        for block, offset in page:
            draw_block(cr, block, MARGIN, top + offset, CONTENT_W)

    surface.finish()
    return output_path, total, len(blocks)


def main():
    readme = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else DEFAULT_README
    output = Path(sys.argv[2]).expanduser() if len(sys.argv) > 2 else DEFAULT_PDF
    if not readme.exists():
        raise SystemExit(f"README not found: {readme}")
    path, pages, blocks = render(readme, output)
    print(f"{path} ({pages} pages, {blocks} blocks)")


if __name__ == "__main__":
    main()
