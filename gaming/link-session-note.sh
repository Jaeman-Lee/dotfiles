#!/usr/bin/env bash
# Deploy a pointer to the single Git-managed session note; never copy its body.
set -euo pipefail
repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
note_source="$repo_root/docs/sessions/2026-09-27-gaming-closeout.md"
note_target=/mnt/dev-ssd/games/SESSION.md
[[ -f "$note_source" && -d /mnt/dev-ssd/games ]]
if [[ -e "$note_target" || -L "$note_target" ]]; then
    [[ -L "$note_target" && $(readlink -- "$note_target") == "$note_source" ]] || {
        echo 'Existing session note differs; preserved without overwrite.' >&2
        exit 1
    }
else
    ln -s -- "$note_source" "$note_target"
fi
printf 'Session note: %s\n' "$note_target"
