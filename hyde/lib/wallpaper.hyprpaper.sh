#!/usr/bin/env bash
[[ $HYDE_SHELL_INIT -ne 1 ]] && eval "$(hyde-shell init)"

# wallpaper_acquire_lock lives in globalcontrol.sh. When this script runs as a
# child of wallpaper.sh, HYDE_SHELL_INIT is exported and the init above is
# skipped, so load the shared helpers explicitly.
[[ $HYDE_SHELL_INIT -eq 1 ]] && source "$LIB_DIR/hyde/globalcontrol.sh"

wallpaper_acquire_lock 15
trap 'flock -u "$WALLPAPER_LOCK_FD"' EXIT

selected_wall="${1:-${XDG_CACHE_HOME:-$HOME/.cache}/hyde/wall.set}"
[ -z "$selected_wall" ] && echo "No input wallpaper" && exit 1
selected_wall="$(readlink -f "$selected_wall")"
is_video=$(file --mime-type -b "$selected_wall" | grep -c '^video/')
if [ "$is_video" -eq 1 ]; then
    print_log -sec "wallpaper" -stat "converting video" "$selected_wall"
    mkdir -p "$HYDE_CACHE_HOME/wallpapers/thumbnails"
    cached_thumb="$HYDE_CACHE_HOME/wallpapers/$(${hashMech:-sha1sum} "$selected_wall" | cut -d' ' -f1).png"
    extract_thumbnail "$selected_wall" "$cached_thumb"
    selected_wall="${cached_thumb}"
fi

# Hyprpaper's config parser breaks on quoted paths that contain spaces, and
# every HyDE theme name has one ("Decay Green", "Tokyo Night", ...). Publish
# the chosen wallpaper through a space-free symlink and write that path
# unquoted. Hyprpaper follows the symlink to the real image.
wall_dir="$HYDE_CACHE_HOME/hyprpaper"
mkdir -p "$wall_dir"
ext="${selected_wall##*.}"
ext="${ext,,}"
[[ $ext =~ ^[a-z0-9]{1,5}$ ]] || ext=png
wall_link="$wall_dir/wall.$ext"
rm -f "$wall_dir"/wall.*
ln -sfn "$selected_wall" "$wall_link"

write_config() {
    cat >"$1" <<HYPRPAPER
splash = false

wallpaper {
    monitor =
    path = ${wall_link}
    fit_mode = cover
}
HYPRPAPER
}

# hyprpaper >= 0.8 replaced the `hyprctl hyprpaper` IPC with hyprwire and only
# reads wallpapers from its config file. `hyprctl hyprpaper wallpaper` still
# exits 0 there while doing nothing, so gate on the version instead of the
# exit code, then rewrite the config and restart the service.
hyprpaper_uses_config() {
    local version
    version=$(hyprpaper --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    [[ -n $version ]] || return 1
    [[ $(printf '%s\n%s\n' "$version" "0.8.0" | sort -V | head -1) == "0.8.0" ]]
}

if [[ -n $HYPRLAND_INSTANCE_SIGNATURE ]] && ! hyprpaper_uses_config; then
    hyprctl hyprpaper wallpaper ",${selected_wall}" >/dev/null 2>&1 && exit 0
    hyprctl hyprpaper reload ,"${selected_wall}" >/dev/null 2>&1 && exit 0
fi

write_config "$confDir/hypr/hyprpaper.conf"

# A manually launched hyprpaper keeps the old socket and config. Stop every
# instance first, clear a start-limit from earlier failed launches, then let
# systemd own the only process.
pkill -x hyprpaper 2>/dev/null || true
sleep 0.2
systemctl --user reset-failed hyprpaper.service 2>/dev/null || true
if ! systemctl --user restart hyprpaper.service >/dev/null 2>&1; then
    setsid hyprpaper >/dev/null 2>&1 &
fi
