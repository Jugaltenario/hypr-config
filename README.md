# hypr-config

A personal Hyprland desktop setup for Arch/CachyOS: a mechabar-style Waybar,
Ghostty terminal, rofi launcher, Nautilus, swaync notifications, fish, fastfetch
and a theme switcher that keeps the wallpaper, bar, terminal and GTK apps in
sync.

This repo is a personal configuration, not a desktop distribution. Review the
scripts before running them, and back up your existing config first.

## What you get

- **Window management** — Hyprland Lua config with dwindle and scrolling
  layouts, workspaces, scratchpad, rules, animations and media keys.
- **Waybar** — the mechabar layout: workspaces, window title, media, CPU, RAM,
  disk, network, Bluetooth, volume, brightness, battery, clock and tray.
- **Ghostty** — terminal config with padding, blur and a generated theme.
- **rofi** — application launcher, window switcher, clipboard and searchable
  keybinding overlay, with Brave as the default browser.
- **Nautilus** — file manager with matching GTK3/GTK4 colours.
- **swaync** — notification popups and control centre.
- **Theme switching** — 12 themes that recolour Waybar, Ghostty, GTK apps,
  cursor, fonts and the wallpaper together.
- **Keybinding reference** — a generator that turns the live Hyprland config
  into a PDF and a searchable rofi overlay.

## Repository layout

```text
hypr/          Hyprland entrypoint, Lua config, hyprlock, hyprpaper, scripts
waybar/        mechabar layout and generated palette
ghostty/       terminal config and generated palette
rofi/          launcher config and themes
swaync/        notification daemon config
fish/          shell config and helper functions
fastfetch/     system info config
micro/         editor config
gtk-3.0/       GTK3 settings
gtk-4.0/       GTK4 settings; later managed by the theme switcher
nwg-look/      GTK appearance settings
hyde/          helper-layer overrides and theme-switch scripts
applications/  desktop entries
```

## Requirements

You need a working Hyprland/Wayland session. The commands below assume
Arch/CachyOS package names.

The config also expects the helper layer used by `hyprland.lua` and the theme
switcher (`hyde-shell`, `hyde.sh`, the Lua modules and theme files). This repo
contains the personal configuration and local overrides, not that base layer.
Install the base layer first if `hyde-shell` is not already available.

Core packages:

```bash
sudo pacman -S hyprland waybar rofi swaync hyprpaper hyprlock ghostty \
  nautilus fish fastfetch jq grim slurp hyprshot wl-clipboard \
  brightnessctl playerctl python python-gobject python-cairo \
  imagemagick ffmpeg parallel
```

Optional extras for the full set of binds and features:

```bash
sudo pacman -S lua-lgi luarocks uwsm hyprsunset wl-clip-persist satty \
  hyprpicker qt5ct qt6ct ttf-cascadia-code-nerd ttf-cascadia-mono-nerd \
  network-manager-applet udiskie blueman polkit-kde-agent
```

`ttf-cascadia-*-nerd` provides the terminal font. After installing fonts:

```bash
fc-cache -f
```

The launcher and `SUPER + B` use Brave. Install it with `sudo pacman -S
brave-bin` on CachyOS, or from the AUR on plain Arch. If you use a different
browser, change `browser` in `~/.config/hyde/config.toml` and the default
entries in `~/.config/mimeapps.list`.

## Install

1. Clone the repo and back up anything you already have:

   ```bash
   git clone https://github.com/Jugaltenario/hypr-config.git ~/hypr-config
   cd ~/hypr-config

   backup="$HOME/.config-backup-$(date +%Y%m%d-%H%M%S)"
   mkdir -p "$backup"
   for item in hypr waybar rofi swaync ghostty fish fastfetch micro \
       gtk-3.0 gtk-4.0 nwg-look autostart mimeapps.list; do
       [ -e "$HOME/.config/$item" ] && cp -a "$HOME/.config/$item" "$backup/"
   done
   echo "Backup: $backup"
   ```

2. Copy the desktop configs:

   ```bash
   cp -r hypr waybar rofi swaync ghostty fastfetch fish micro \
     gtk-3.0 nwg-look autostart ~/.config/
   cp mimeapps.list ~/.config/
   mkdir -p ~/.local/share/applications
   cp applications/hyde-theme.desktop ~/.local/share/applications/
   ```

3. Copy the helper-layer overrides and theme scripts:

   ```bash
   mkdir -p ~/.local/bin ~/.local/lib/hyde/color \
     ~/.config/hyde/scripts ~/.local/share/hyde ~/.local/state/hyde

   cp hyde/bin/hyq ~/.local/bin/hyq
   cp hyde/lib/*.py hyde/lib/*.sh ~/.local/lib/hyde/
   cp hyde/lib/color/* ~/.local/lib/hyde/color/
   cp hyde/config.toml ~/.config/hyde/config.toml
   cp hyde/scripts/*.sh ~/.config/hyde/scripts/
   cp hyde/share/env-theme ~/.local/share/hyde/env-theme
   cp hyde/state/staterc.example ~/.local/state/hyde/staterc

   chmod +x ~/.local/bin/hyq ~/.config/hyde/scripts/*.sh
   ```

4. Replace the old home path in the copied files:

   ```bash
   grep -rl '/home/jp' ~/.config/hypr ~/.config/ghostty ~/.config/fish \
     ~/.config/hyde ~/.local/share/hyde ~/.local/state/hyde 2>/dev/null |
     xargs -r sed -i "s|/home/jp|$HOME|g"
   ```

5. Add the wallpapers:

   ```bash
   mkdir -p ~/Pictures/Wallpaper
   cp hypr/assets/wallpapers/* ~/Pictures/Wallpaper/
   ```

6. Apply a theme and generate the palettes:

   ```bash
   hyde-shell theme.switch -s "Catppuccin Mocha"
   ```

7. Log out and start a new Hyprland session. If you use a display manager,
   choose Hyprland there; otherwise start it from a TTY with `Hyprland`.

## Daily use

- `SUPER + Return` — Ghostty
- `SUPER + B` — Brave
- `SUPER + E` — Nautilus
- `SUPER + Space` — application launcher
- `SUPER + Shift + T` — theme picker
- `SUPER + Alt + Up/Down` — next/previous theme
- `SUPER + /` — searchable keybinding overlay

The theme picker's wallpaper previews come from a thumbnail cache. If a theme
shows a blank preview, rebuild that theme's thumbnails:

```bash
hyde-shell wallpaper --cache theme "Catppuccin Mocha"
```

## Keybinding PDF

Generate a printable reference from the running Hyprland config:

```bash
~/.config/hypr/scripts/gen-all-keybinds.py
```

The PDF is written to `~/Desktop/Keybindings.pdf` and
`~/.config/hypr/keybindings.json` is refreshed for the `SUPER + /` overlay.
Re-run it after adding or changing a bind.

## Notes

- `~/.config/gtk-4.0` is managed by the theme switcher after the first switch.
  Do not copy a stale `gtk-4.0` directory over it later.
- Wallpaper changes are handled by `hyprpaper.service`. Do not launch
  `hyprpaper` manually, or you will end up with competing instances.
- If fish reports `Unknown command: bind_M_n_history`, the helper functions
  under `fish/functions/` were not copied. Re-run step 2.
- The config uses `Nautilus`, `Ghostty` and `Waybar`; if you prefer different
  applications, update the variables at the top of `hypr/hyprland.lua`.
- This setup is tuned for a single laptop display. Review the monitor block in
  `hypr/hyprland.lua` before using it on a multi-monitor desktop.

## Updating

```bash
cd ~/hypr-config
git pull
```

Then copy the changed files you want to keep, and re-run
`hyde-shell theme.switch -s "<theme>"` if Waybar or Ghostty colours look stale.
