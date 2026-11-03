# hypr-config

Personal Hyprland rice backed up from `~/.config`, now running on top of
[HyDE](https://github.com/HyDE-Project/HyDE).

HyDE is the framework (themes, wallpapers, keybinds, Lua modules). The files in
this repo are the user layer: the mechabar waybar layout, Ghostty, Nautilus and
the personal fastfetch config stay in charge, and HyDE only recolours them.

## Layout

- `hypr/` — `hyprland.lua` (personal entrypoint + HyDE bootstrap), hyprlock,
  hyprpaper config, custom scripts, assets + wallpapers
- `waybar/` — mechabar layout; `style.css` imports the generated
  `themes/hyde.css` palette, so only colours follow the HyDE theme
- `hyde/` — local HyDE overrides (see below)
- `ghostty/` — base config + generated `hyde-theme.conf` palette
- `rofi/`, `swaync/`, `fastfetch/`, `micro/`
- `fish/` — config, `conf.d/hyde.fish`, and HyDE's helper functions
  (`bind_M_n_history`, `_hyde_editor`, `fzf/*`)
- `gtk-3.0/`, `nwg-look/`, `autostart/`, `mimeapps.list`
- `applications/hyde-theme.desktop` — theme switcher entry for rofi/app menus

`fish/conf.d/hyde.fish` calls `bind_M_n_history`; if fish says
`Unknown command: bind_M_n_history`, the matching file in
`fish/functions/` was not installed.

## Theme switcher

Open HyDE's visual picker with:

- `SUPER + SHIFT + T`, or
- `hyde-shell theme.select` in a terminal, or
- **HyDE Theme Switcher** in rofi's application list.

Use `SUPER + ALT + Up` / `SUPER + ALT + Down` to cycle themes without opening
the picker. The picker shows wallpaper thumbnails; `thmbDir` must contain a
`.sqre` thumbnail for every theme or entries appear blank. Rebuild them with
`hyde-shell wallpaper --cache theme "<theme name>"`.

## How theming works

`hyde-shell theme.switch` (or `hyde-shell theme.select`) writes HyDE's colour
state. Three hooks then recolour the personal apps:

1. `~/.config/hyde/scripts/theme.switch.sh` wraps HyDE's switch and calls
   `theme-apply.sh`.
2. `theme-apply.sh` runs `~/.local/lib/hyde/mechabar-sync.py`, which reads
   HyDE's `~/.config/waybar/theme.css` and writes the mechabar palette
   (`~/.config/waybar/themes/hyde.css`), then reloads Waybar.
3. `~/.local/lib/hyde/ghostty-sync.py` converts the theme's `kitty.theme` into
   `~/.config/ghostty/hyde-theme.conf` and reloads Ghostty.

Nautilus follows the GTK theme HyDE writes (`gtk-3.0/settings.ini`,
`gtk-4.0` symlink, cursor and fonts). `~/.config/gtk-4.0` is managed by HyDE —
do not restore the old `gtk-4.0` directory from this repo after HyDE is set up.

### Local HyDE fixes carried in `hyde/`

These are local edits on top of upstream HyDE `fa2fd57` (2026-11-03). Copy them
back after installing/updating HyDE:

- `bin/hyq` — Python compatibility shim for `hyprquery` (`hyq`), which HyDE
  calls but which is not packaged on this system.
- `lib/globalcontrol.sh` — defaults `HYPRLAND_CONFIG`, so `theme.switch.sh`
  loads the theme's own GTK/font/cursor variables instead of falling back to
  `Wallbash-Gtk`.
- `lib/color/hypr.sh` — seeds UI state from `env-theme`, restores those
  defaults when a theme omits a value, and records the `terminal`.
- `lib/color.set.sh` — falls back to `color/dconf.py` when the Lua `lgi`
  binding is unavailable.
- `lib/color/dconf.py` — PyGObject replacement for upstream `dconf.lua`
  (gsettings theme/cursor/font/terminal, `hyprctl setcursor`).
- `lib/wallpaper.hyprpaper.sh` — loads the lock helpers when invoked as a
  child of `wallpaper.sh`, and supports hyprpaper >= 0.8 (which dropped the
  `hyprctl hyprpaper` IPC): rewrites the config and restarts the service.
  Paths are published through a space-free `~/.cache/hyde/hyprpaper/wall.*`
  symlink because hyprpaper misparses quoted paths containing spaces (every
  HyDE theme name has one). The script also removes manually started
  hyprpaper instances so only the systemd service owns the socket.
- `lib/mechabar-sync.py` — HyDE palette → mechabar `hyde.css`.
- `lib/ghostty-sync.py` — HyDE `kitty.theme` → Ghostty config.
- `scripts/waybar.sh` — refuses HyDE's layout-changing `waybar --next/--set`
  commands so a theme cannot overwrite mechabar; allows `--update`/`--hide`.

`hyde/config.toml` selects hyprpaper, Ghostty, Nautilus, swaync and the
personal waybar; `hyde/share/env-theme` sets `TERMINAL="ghostty"` and the
cursor; `hyde/state/staterc.example` is the saved theme state.

## Dependencies (Arch/CachyOS)

Already needed by the rice:

`hyprland` `waybar` `rofi` `swaync` `hyprpaper` `hyprlock` `ghostty`
`nautilus` `fastfetch` `fish` `python` `python-gobject` `jq` `grim` `slurp`
`hyprshot` `wl-clipboard` `brightnessctl` `pamixer`

Recommended for the full HyDE feature set (some binds and the Lua tooling are
disabled without them):

```bash
sudo pacman -S lua-lgi luarocks uwsm hyprsunset wl-clip-persist satty \
  hyprpicker qt5ct qt6ct ttf-cascadia-code-nerd ttf-cascadia-mono-nerd \
  network-manager-applet udiskie blueman polkit-kde-agent awww
```

`ttf-cascadia-*-nerd` provides the `CaskaydiaCove Nerd Font Mono` used by
Ghostty. `awww` is optional: this setup uses `hyprpaper`.

After installing fonts, refresh the cache and restart Ghostty:

```bash
fc-cache -f
```

## Restore

1. Install HyDE from upstream (its own `install.sh`), then copy the local
   overrides:

   ```bash
   cd ~/hypr-config
   cp hyde/bin/hyq ~/.local/bin/hyq
   cp hyde/lib/*.py hyde/lib/*.sh ~/.local/lib/hyde/
   cp hyde/lib/color/* ~/.local/lib/hyde/color/
   cp hyde/config.toml ~/.config/hyde/config.toml
   cp hyde/scripts/*.sh ~/.config/hyde/scripts/
   cp hyde/share/env-theme ~/.local/share/hyde/env-theme
   cp hyde/state/staterc.example ~/.local/state/hyde/staterc
   chmod +x ~/.local/bin/hyq ~/.config/hyde/scripts/*.sh
   ```

2. Copy the personal configs:

   ```bash
   cp -r hypr waybar rofi swaync ghostty fastfetch fish micro gtk-3.0 \
     nwg-look autostart ~/.config/
   cp mimeapps.list ~/.config/
   mkdir -p ~/.local/share/applications
   cp applications/hyde-theme.desktop ~/.local/share/applications/
   ```

3. Wallpapers stay at their original paths:

   ```bash
   mkdir -p ~/Pictures/Wallpaper
   cp hypr/assets/wallpapers/* ~/Pictures/Wallpaper/
   ```

4. Generate the colours for the selected theme:

   ```bash
   hyde-shell theme.switch -s "Catppuccin Mocha"
   ```

   This writes `waybar/themes/hyde.css`, `ghostty/hyde-theme.conf`,
   `gtk-3.0/settings.ini` and the `gtk-4.0` symlink.

## Keybinds changed from HyDE defaults

- `SUPER + ALT + Up/Down` — next/previous HyDE theme (HyDE normally uses these
  to switch its own waybar layouts, which would overwrite mechabar).
- `SUPER + SHIFT + T` — HyDE theme picker (recolours waybar + Ghostty).
- `SUPER + E` — Nautilus.
- `SUPER + Return` — Ghostty.
- `SUPER + /` — searchable keybinding overlay.

## Rollback

The pre-HyDE state is archived locally at
`/tmp/opencode/pre-hyde-20261103-110222.tar.gz` (not in this repo). Extract it
over `~/.config` and remove HyDE's bootstrap from `hypr/hyprland.lua` to return
to the old setup.
