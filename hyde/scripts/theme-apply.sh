#!/usr/bin/env bash
# Re-render the mechabar waybar palette and the Ghostty theme from the colours
# HyDE just wrote for the active theme.
set +u

LIB_DIR="${LIB_DIR:-$HOME/.local/lib}"
# shellcheck disable=SC1091
source "$LIB_DIR/hyde/globalcontrol.sh"

theme_dir="${HYDE_THEME_DIR:-$HOME/.config/hyde/themes/$HYDE_THEME}"
theme_name="${HYDE_THEME:-HyDE}"

# colour.set.sh writes ~/.config/waybar/theme.css; give the (async) theme
# switch a moment on a cold session start before falling back.
theme_css="$HOME/.config/waybar/theme.css"
for _ in 1 2 3 4 5 6 7 8 9 10; do
    [ -s "$theme_css" ] && break
    sleep 0.3
done

python3 "$LIB_DIR/hyde/mechabar-sync.py" \
    --theme-css "$theme_css" \
    --theme-dir "$theme_dir" \
    --theme-name "$theme_name" \
    --out "$HOME/.config/waybar/themes/hyde.css" || true

python3 "$LIB_DIR/hyde/ghostty-sync.py" \
    --theme-dir "$theme_dir" \
    --theme-name "$theme_name" \
    --out "$HOME/.config/ghostty/hyde-theme.conf" || true

# Waybar re-reads style.css on SIGUSR2; ghostty reloads its config on SIGUSR2.
pkill -SIGUSR2 -x waybar 2>/dev/null || true
pkill -SIGUSR2 -x ghostty 2>/dev/null || true
