#!/bin/sh
set -eu
source_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
target_dir=${CODEX_HOME:-"$HOME/.codex"}
target="$target_dir/AGENTS.md"
mkdir -p "$target_dir"
if [ -e "$target" ] && ! cmp -s "$source_dir/AGENTS.md" "$target"; then
  printf '%s\n' 'Existing AGENTS.md differs; merge it before installing.' >&2
  exit 1
fi
temporary=$(mktemp "$target_dir/.AGENTS.XXXXXX")
trap 'rm -f "$temporary"' EXIT HUP INT TERM
cp "$source_dir/AGENTS.md" "$temporary"
chmod 600 "$temporary"
mv -f "$temporary" "$target"
printf '%s\n' 'Installed Git-managed Codex instructions.'
