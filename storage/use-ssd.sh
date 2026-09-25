#!/bin/sh
set -eu
mount_dir=/mnt/dev-ssd
[ -f "$mount_dir/.storage-ready" ] || { echo 'SSD preparation not verified.' >&2; exit 1; }
findmnt -rn -M "$mount_dir" -t ext4 >/dev/null || exit 1
[ -w "$mount_dir/cache/npm" ] || exit 1
config_dir="$HOME/.config/environment.d"
mkdir -p "$config_dir"
destination="$config_dir/60-dev-storage.conf"
temporary=$(mktemp "$config_dir/.dev-storage.XXXXXX")
trap 'rm -f "$temporary"' EXIT HUP INT TERM
cat > "$temporary" <<'CONFIG'
# Source: Git-managed dotfiles/storage/use-ssd.sh
NPM_CONFIG_CACHE=/mnt/dev-ssd/cache/npm
PIP_CACHE_DIR=/mnt/dev-ssd/cache/pip
UV_CACHE_DIR=/mnt/dev-ssd/cache/uv
CONFIG
chmod 600 "$temporary"
if [ -e "$destination" ]; then
  if ! cmp -s "$temporary" "$destination"; then
    echo 'Existing cache environment file differs; preserved for review.' >&2
    exit 1
  fi
else
  mv "$temporary" "$destination"
fi
if command -v npm >/dev/null 2>&1; then
  npm config set cache "$mount_dir/cache/npm" --location=user
fi
printf '%s\n' 'SSD cache configuration installed. Existing caches and repositories were not moved.'
