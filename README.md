# hypr-config

Personal Hyprland rice backed up from `~/.config`.

## What's included
- `hypr/` — Hyprland (Lua), hyprlock/hyprpaper, custom scripts (`gen-keybinds.py`, `show-keybinds`, `layout-notify`), assets + wallpapers
- `waybar/` — mechabar-style bar (Catppuccin Mocha)
- `rofi/` — config + themes (including the new adi1090x-style launcher and keybinds overlay)
- `swaync/` — notification daemon config + Catppuccin styling
- `ghostty/`, `fastfetch/`, `fish/config.fish`, `micro/settings.json`
- `gtk-3.0/`, `gtk-4.0/`, `nwg-look/config`, `autostart/`, `mimeapps.list`

## Dependencies (Arch/CachyOS)
`hyprland` `waybar` `rofi` `swaync` `hyprpaper` `hyprlock` `ghostty` `fastfetch` `fish` `pango` `cairo` `python-gobject` `jq` `grim` `slurp` `wl-clipboard` `brightnessctl` `pamixer` `network-manager-applet` `nautilus`

## Restore
```bash
# From this repo directory
cp -r hypr waybar rofi swaync ghostty fastfetch fish micro gtk-3.0 gtk-4.0 nwg-look autostart ~/.config/
cp mimeapps.list ~/.config/

# Wallpapers (paths are referenced as-is in hyprpaper/hyprlock)
mkdir -p ~/Pictures/Wallpaper
cp hypr/assets/wallpapers/* ~/Pictures/Wallpaper/
```

## Keybind cheat sheet
The PDF is generated from `hypr/keybindings.json`:
```bash
python3 ~/.config/hypr/scripts/gen-keybinds.py pdf
```
Press `Super+/` to open the searchable rofi overlay.

## Notes
- `waybar` was vendored (original `.git` removed) to keep a clean history.
- Wallpapers are copied here for backup but left at their original paths; see restore instructions above.
