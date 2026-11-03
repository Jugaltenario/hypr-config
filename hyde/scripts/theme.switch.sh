#!/usr/bin/env bash
# Wrapper: run HyDE's theme switch, then recolour the mechabar waybar and
# Ghostty from the colours it produced.
set -u
LIB_DIR="${LIB_DIR:-$HOME/.local/lib}"

"$LIB_DIR/hyde/theme.switch.sh" "$@"
status=$?
[ "$status" -eq 0 ] && "$HOME/.config/hyde/scripts/theme-apply.sh"
exit "$status"
