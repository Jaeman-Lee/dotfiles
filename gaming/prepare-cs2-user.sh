#!/usr/bin/env bash
# Keep the Steam client, games and account data on the existing SSD mount.
set -euo pipefail
[[ $EUID -ne 0 ]] || { echo 'Run as the desktop user, not root.' >&2; exit 1; }
mountpoint -q /mnt/dev-ssd || { echo 'SSD is not mounted.' >&2; exit 1; }
steam_dir=/mnt/dev-ssd/games/Steam
data_dir=${XDG_DATA_HOME:-$HOME/.local/share}
steam_link=$data_dir/Steam
links=("$steam_link" "$HOME/.steam/steam" "$HOME/.steam/root")
for link in "${links[@]}"; do
    if [[ -e $link || -L $link ]]; then
        [[ $(readlink -f "$link") == "$steam_dir" ]] || {
            echo "Existing Steam installation preserved: $link" >&2
            exit 1
        }
    fi
done
if pgrep -u "$(id -u)" -x steam >/dev/null; then
    echo 'Close Steam before preparing its storage.' >&2
    exit 1
fi
mkdir -p "$steam_dir" "$data_dir/applications" "$HOME/.steam"
for link in "${links[@]}"; do
    if [[ ! -L $link ]]; then
        ln -s "$steam_dir" "$link"
    fi
done
desktop_file=$data_dir/applications/counter-strike-2.desktop
if [[ ! -e $desktop_file ]]; then
    cat > "$desktop_file" <<'DESKTOP'
[Desktop Entry]
Type=Application
Name=Counter-Strike 2
Comment=Play Counter-Strike 2 with Steam
Exec=steam steam://rungameid/730
Icon=steam
Terminal=false
Categories=Game;ActionGame;
DESKTOP
fi
if command -v update-desktop-database >/dev/null; then
    update-desktop-database "$data_dir/applications"
fi
printf 'Steam storage: %s\n' "$steam_dir"
printf 'After installing Steam, open: steam steam://install/730\n'
