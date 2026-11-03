#!/usr/bin/env python3
"""Apply HyDE's Lua UI state to gsettings (lgi-free replacement for dconf.lua).

HyDE writes ~/.local/state/hyde/lua_state/ui.lua on every theme switch and
normally applies it with color/dconf.lua, which needs the Lua lgi binding.
When lgi is not installed this script does the same job through PyGObject,
which ships with python-gobject.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys

try:
    import gi

    gi.require_version("Gio", "2.0")
    from gi.repository import Gio
except (ImportError, ValueError) as error:  # pragma: no cover
    print(f"dconf.py: PyGObject is unavailable: {error}", file=sys.stderr)
    sys.exit(1)

STATE = os.path.join(
    os.environ.get("XDG_STATE_HOME", os.path.expanduser("~/.local/state")),
    "hyde/lua_state/ui.lua",
)

KEYS = (
    "hyde_theme",
    "gtk_theme",
    "icon_theme",
    "color_scheme",
    "button_layout",
    "cursor_theme",
    "cursor_size",
    "font",
    "font_size",
    "document_font",
    "document_font_size",
    "monospace_font",
    "monospace_font_size",
    "notification_font",
    "bar_font",
    "menu_font",
    "font_antialiasing",
    "font_hinting",
    "terminal",
)

STRING_RE = re.compile(r'^\s*([A-Za-z0-9_]+)\s*=\s*"(.*)"\s*,?\s*$')


def read_ui(path: str) -> dict[str, str]:
    values: dict[str, str] = {}
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            for line in handle:
                match = STRING_RE.match(line)
                if match:
                    values[match.group(1)] = match.group(2)
    except OSError:
        pass
    return values


def value(values: dict[str, str], key: str) -> str | None:
    for candidate in (values.get(key), os.environ.get("__" + key.upper()), os.environ.get(key.upper())):
        if candidate:
            return candidate
    return None


def main() -> int:
    values = read_ui(STATE)

    gtk_theme = value(values, "gtk_theme") or "Wallbash-Gtk"
    icon_theme = value(values, "icon_theme")
    color_scheme = value(values, "color_scheme") or "prefer-dark"
    cursor_theme = value(values, "cursor_theme")
    try:
        cursor_size = int(value(values, "cursor_size") or 24)
    except ValueError:
        cursor_size = 24

    def font(name: str, size: str) -> str | None:
        family = value(values, name)
        if not family:
            return None
        point = value(values, size)
        return f"{family} {point}" if point else family

    font_name = font("font", "font_size")
    document_font = font("document_font", "document_font_size")
    monospace_font = font("monospace_font", "monospace_font_size")
    antialiasing = value(values, "font_antialiasing") or "rgba"
    hinting = value(values, "font_hinting") or "slight"
    button_layout = value(values, "button_layout")
    terminal = value(values, "terminal") or "kitty"

    iface = Gio.Settings.new("org.gnome.desktop.interface")
    iface.set_string("gtk-theme", gtk_theme)
    if icon_theme:
        iface.set_string("icon-theme", icon_theme)
    iface.set_string("color-scheme", color_scheme)
    if cursor_theme:
        iface.set_string("cursor-theme", cursor_theme)
    iface.set_int("cursor-size", cursor_size)
    if font_name:
        iface.set_string("font-name", font_name)
    if document_font:
        iface.set_string("document-font-name", document_font)
    if monospace_font:
        iface.set_string("monospace-font-name", monospace_font)
    iface.set_string("font-antialiasing", antialiasing)
    iface.set_string("font-hinting", hinting)
    Gio.Settings.sync()

    if button_layout:
        wm = Gio.Settings.new("org.gnome.desktop.wm.preferences")
        wm.set_string("button-layout", button_layout)
        Gio.Settings.sync()

    terminal_settings = Gio.Settings.new("org.gnome.desktop.default-applications.terminal")
    binary = shutil.which(terminal) or terminal
    if binary:
        terminal_settings.set_string("exec", binary)
        Gio.Settings.sync()

    if os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
        subprocess.run(["hyprctl", "setcursor", cursor_theme or "", str(cursor_size)], check=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
