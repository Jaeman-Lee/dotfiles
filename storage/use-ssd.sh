#!/bin/sh
# Compatibility entry point: the 2026-09-27 storage policy supersedes SSD caches.
set -eu
script_dir=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
exec sh "$script_dir/use-hdd-records.sh" "$@"
