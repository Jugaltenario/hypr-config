#!/usr/bin/env bash
# Wrapper: a wallpaper change re-runs HyDE's colour engine, so keep the
# mechabar waybar and Ghostty in sync too.
set -u
LIB_DIR="${LIB_DIR:-$HOME/.local/lib}"

"$LIB_DIR/hyde/wallpaper.sh" "$@"
status=$?
[ "$status" -eq 0 ] && "$HOME/.config/hyde/scripts/theme-apply.sh"
exit "$status"
