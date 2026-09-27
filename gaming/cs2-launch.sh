#!/usr/bin/env bash
set -euo pipefail
if [[ $# -eq 0 ]]; then
    echo 'Use this wrapper in Steam launch options, followed by %command%.' >&2
    exit 2
fi
# Refresh our separately named config after Steam updates; do not touch autoexec.
config_source=${XDG_CONFIG_HOME:-$HOME/.config}/cs2/workstation.cfg
config_target='/mnt/dev-ssd/games/Steam/steamapps/common/Counter-Strike Global Offensive/game/csgo/cfg/workstation.cfg'
if [[ -f $config_source ]]; then
    install -m 0644 "$config_source" "$config_target"
fi
# The desktop power profile hold is released even if the child crashes.
exec powerprofilesctl launch --profile performance --reason 'Counter-Strike 2' \
    --appid cs2 -- /usr/games/gamemoderun "$@" -w 1920 -h 1080 -fullscreen +exec workstation.cfg
