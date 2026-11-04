#!/usr/bin/env python3
"""Build a complete keybinding reference from the live Hyprland config.

Reads `hyprctl binds -j`, writes ~/.config/hypr/keybindings.json (also used by
the Super+/ rofi overlay), then renders a PDF with the existing Cairo renderer.

Usage:
    gen-all-keybinds.py [output.pdf]

Default output: ~/Desktop/HyDE-Keybindings.pdf
"""

import importlib.util
import json
import os
import re
import subprocess
import sys
from collections import OrderedDict
from datetime import date
from pathlib import Path

HOME = Path.home()
DATA = HOME / ".config/hypr/keybindings.json"
RENDERER = HOME / ".config/hypr/scripts/gen-keybinds.py"
DEFAULT_PDF = HOME / "Desktop/Keybindings.pdf"
MAX_BINDS_PER_CARD = 10

MODIFIERS = (
    (64, "Super"),
    (4, "Ctrl"),
    (8, "Alt"),
    (1, "Shift"),
    (32, "Hyper"),
    (16, "Meta"),
    (2, "Caps"),
)

KEY_LABELS = {
    "return": "↵",
    "enter": "↵",
    "escape": "Esc",
    "delete": "Del",
    "print": "PrtSc",
    "space": "Space",
    "tab": "Tab",
    "slash": "/",
    "period": ".",
    "comma": ",",
    "plus": "+",
    "minus": "−",
    "left": "←",
    "right": "→",
    "up": "↑",
    "down": "↓",
    "mouse:272": "Left click",
    "mouse:273": "Right click",
    "mouse_down": "Scroll down",
    "mouse_up": "Scroll up",
    "xf86audioraisevolume": "Volume +",
    "xf86audiolowervolume": "Volume −",
    "xf86audiomute": "Mute",
    "xf86audiomicmute": "Mic mute",
    "xf86audioplay": "Play",
    "xf86audiopause": "Pause",
    "xf86audionext": "Next track",
    "xf86audioprev": "Previous track",
    "xf86monbrightnessup": "Brightness +",
    "xf86monbrightnessdown": "Brightness −",
    "xf86kbrightnessup": "Keyboard light +",
    "xf86kbrightnessdown": "Keyboard light −",
}

PREFERRED_ORDER = [
    "Launcher",
    "Window Management",
    "Workspaces",
    "Layout Management",
    "Utilities",
    "Theming and Wallpaper",
    "Hardware Controls",
    "Misc",
]

ACCENTS = {
    "Launcher": "blue",
    "Window Management": "teal",
    "Workspaces": "mauve",
    "Layout Management": "lavender",
    "Utilities": "peach",
    "Theming and Wallpaper": "pink",
    "Hardware Controls": "green",
    "Misc": "sky",
}


def hyprctl_binds():
    out = subprocess.check_output(["hyprctl", "binds", "-j"], text=True)
    return json.loads(out)


def hyprland_version():
    try:
        out = subprocess.check_output(["hyprctl", "version"], text=True)
        m = re.search(r"Hyprland\s+(\S+)", out)
        if m:
            return m.group(1)
    except (OSError, subprocess.CalledProcessError):
        pass
    return "unknown"


def parse_description(raw):
    """Split '[Category|Subcategory] text' into category parts and text."""
    raw = (raw or "").strip()
    match = re.match(r"^\[([^\]]*)\]\s*(.*)$", raw)
    if match:
        headers = [part.strip() for part in match.group(1).split("|")]
        desc = match.group(2).strip()
    else:
        headers = ["Misc"]
        desc = raw

    category = headers[0] or "Misc"
    subcategory = headers[1] if len(headers) > 1 else ""
    desc = desc.replace("un/mmute", "mute / unmute").replace("un/mute", "mute / unmute")
    desc = desc.replace("]", "").strip()
    return category, subcategory, desc


def key_label(key):
    low = key.lower()
    if low in KEY_LABELS:
        return KEY_LABELS[low]
    if re.fullmatch(r"f\d{1,2}", low):
        return low.upper()
    if low.startswith("kp_"):
        return "Num " + key[3:].replace("_", " ")
    if len(key) == 1:
        return key.upper()
    return key


def bind_keys(bind):
    keys = [name for bit, name in MODIFIERS if bind.get("modmask", 0) & bit]
    key = bind.get("key") or ""
    if key:
        keys.append(key_label(key))
    return keys


def slug(text):
    text = text.lower().replace("&", "and")
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-") or "misc"


def build_data(binds):
    groups = OrderedDict()
    count = 0

    for bind in binds:
        if bind.get("catch_all"):
            continue
        category, subcategory, desc = parse_description(bind.get("description"))
        if not desc:
            # Every personal bind now has a description; this is a safety net
            # for binds added later without one.
            desc = bind.get("dispatcher", "action").replace("HL.Dispatcher(", "").rstrip(")")
        keys = bind_keys(bind)
        if not keys:
            continue
        group = groups.setdefault((category, subcategory), [])
        group.append({"keys": keys, "desc": desc})
        count += 1

    def order_key(item):
        category, _ = item[0]
        return PREFERRED_ORDER.index(category) if category in PREFERRED_ORDER else len(PREFERRED_ORDER)

    categories = []
    for (category, subcategory), items in sorted(groups.items(), key=order_key):
        name = category if not subcategory else f"{category} · {subcategory}"
        chunks = [items[i : i + MAX_BINDS_PER_CARD] for i in range(0, len(items), MAX_BINDS_PER_CARD)]
        for index, chunk in enumerate(chunks, start=1):
            suffix = "" if len(chunks) == 1 else f" ({index}/{len(chunks)})"
            categories.append(
                {
                    "id": slug(name) + (f"-{index}" if len(chunks) > 1 else ""),
                    "name": name + suffix,
                    "accent": ACCENTS.get(category, "lavender"),
                    "binds": chunk,
                    "count": len(chunk),
                }
            )

    today = date.today().isoformat()
    return {
        "title": "Hyprland Keybindings",
        "eyebrow": f"LIVE HYPRCTL BINDS · HYPRLAND {hyprland_version()} · {today}",
        "subtitle": (
            f"Every active shortcut ({count} binds). Hold Super, then press the keys shown. "
            "Generated from the running Hyprland config."
        ),
        "footer": "~/.config/hypr/keybindings.json · regenerate with gen-all-keybinds.py",
        "categories": categories,
    }


def load_renderer():
    spec = importlib.util.spec_from_file_location("gen_keybinds", RENDERER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    output = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else DEFAULT_PDF
    data = build_data(hyprctl_binds())

    DATA.parent.mkdir(parents=True, exist_ok=True)
    DATA.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    output.parent.mkdir(parents=True, exist_ok=True)
    renderer = load_renderer()
    path, pages = renderer.render_pdf(data, str(output))
    print(f"{path} ({pages} pages, {sum(len(c['binds']) for c in data['categories'])} binds)")
    print(f"updated {DATA}")


if __name__ == "__main__":
    main()
