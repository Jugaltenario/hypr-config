#!/usr/bin/env bash
# Keep the mechabar layout in charge of ~/.config/waybar.
#
# HyDE's `waybar --update` runs apply_theme_layout(), which lets a theme ship
# its own config.jsonc/style.css and overwrite the user's bar. This rice keeps
# mechabar; HyDE only supplies the palette in theme.css, so the update path is
# reduced to a reload and the layout-changing subcommands are refused.
set -u
LIB_DIR="${LIB_DIR:-$HOME/.local/lib}"
real="$LIB_DIR/hyde/waybar.py"

case "${1:-}" in
--hide)
    pkill -SIGUSR1 -x waybar 2>/dev/null || true
    ;;
--update)
    pkill -SIGUSR2 -x waybar 2>/dev/null || true
    ;;
--next | --prev | --set | --select-layout | --select-style | --config | --style)
    echo "mechabar: refusing 'waybar $1'; HyDE bar layouts would overwrite ~/.config/waybar." >&2
    echo "mechabar: edit ~/.config/waybar directly or use the HyDE theme picker for colours." >&2
    exit 1
    ;;
*)
    exec python3 "$real" "$@"
    ;;
esac
