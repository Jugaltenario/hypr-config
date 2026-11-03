#!/usr/bin/env bash
# Wrapper: HyDE's rofi theme picker switches the theme itself, so sync the
# mechabar waybar and Ghostty after it returns.
set -u
LIB_DIR="${LIB_DIR:-$HOME/.local/lib}"

"$LIB_DIR/hyde/theme.select.sh" "$@"
status=$?
[ "$status" -eq 0 ] && "$HOME/.config/hyde/scripts/theme-apply.sh"
exit "$status"
