#!/bin/sh
set -eu
mount_dir=/mnt/dev-ssd
[ -f "$mount_dir/.storage-ready" ] || { echo 'SSD preparation not verified.' >&2; exit 1; }
findmnt -rn -M "$mount_dir" -t ext4 >/dev/null || exit 1
[ -w "$mount_dir/cache/npm" ] || exit 1
config_dir="$HOME/.config/environment.d"
mkdir -p "$config_dir"
destination="$config_dir/60-dev-storage.conf"
if [ -e "$destination" ]; then
  echo 'Existing cache environment file preserved; review manually.' >&2
  exit 1
fi
cat > "$destination" <<'CONFIG'
# Source: Git-managed dotfiles/storage/use-ssd.sh
NPM_CONFIG_CACHE=/mnt/dev-ssd/cache/npm
PIP_CACHE_DIR=/mnt/dev-ssd/cache/pip
UV_CACHE_DIR=/mnt/dev-ssd/cache/uv
CONFIG
chmod 600 "$destination"
printf '%s\n' 'SSD cache paths saved for new login sessions. Existing caches and repositories were not moved.'
