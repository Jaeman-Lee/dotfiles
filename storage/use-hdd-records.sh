#!/bin/sh
# Package download caches and their logs belong on the HDD; runtime stays on SSD.
set -eu
cache_root="$HOME/.cache/dev-packages"
config_dir="$HOME/.config/environment.d"
state_dir="$HOME/.local/state/storage-placement"
mkdir -p "$cache_root/npm" "$cache_root/pip" "$cache_root/uv" "$config_dir" "$state_dir"
[ "$(stat -c %d "$cache_root")" = "$(stat -c %d /)" ] || {
  echo 'Cache root is not on the expected OS/HDD filesystem.' >&2
  exit 1
}
if [ -L "$config_dir/60-dev-storage.conf" ]; then
  echo 'Refusing to replace a symlinked environment file.' >&2
  exit 1
fi
temporary=$(mktemp "$config_dir/.dev-storage.XXXXXX")
trap 'rm -f "$temporary"' EXIT HUP INT TERM
{
  echo '# Source: Git-managed dotfiles/storage/use-hdd-records.sh'
  printf 'NPM_CONFIG_CACHE=%s/npm\n' "$cache_root"
  printf 'PIP_CACHE_DIR=%s/pip\n' "$cache_root"
  printf 'UV_CACHE_DIR=%s/uv\n' "$cache_root"
} > "$temporary"
chmod 600 "$temporary"
if [ -e "$config_dir/60-dev-storage.conf" ]; then
  cp -p "$config_dir/60-dev-storage.conf" "$state_dir/environment-before-$(date -u +%Y%m%dT%H%M%SZ).conf"
fi
mv "$temporary" "$config_dir/60-dev-storage.conf"
# Edit only npm's cache key; npm preserves unrelated registry/auth configuration.
if command -v npm >/dev/null 2>&1; then
  npm config set cache "$cache_root/npm" --location=user
fi
if command -v systemctl >/dev/null 2>&1; then
  systemctl --user set-environment \
    "NPM_CONFIG_CACHE=$cache_root/npm" \
    "PIP_CACHE_DIR=$cache_root/pip" \
    "UV_CACHE_DIR=$cache_root/uv"
fi
printf '%s\n' 'HDD package cache defaults installed. Existing processes keep their environment.'
