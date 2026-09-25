#!/bin/sh
# Destructive only with the explicit flag and exact hardware identity below.
set -eu
disk_id=/dev/disk/by-id/nvme-eui.002538d221b5a65d
mount_dir=/mnt/dev-ssd
owner=${SUDO_USER:-}
if [ "$(id -u)" -ne 0 ] || [ "${1:-}" != --erase-confirmed-ssd ]; then
  printf '%s\n' 'Run with sudo and --erase-confirmed-ssd only after reviewing the SSD layout.' >&2
  exit 1
fi
if [ -z "$owner" ] || [ "$owner" = root ]; then
  printf '%s\n' 'Run through sudo as the intended development user.' >&2
  exit 1
fi
disk=$(readlink -f "$disk_id")
[ "$disk" = /dev/nvme0n1 ] || { echo 'Unexpected disk mapping' >&2; exit 1; }
model=$(lsblk -dn -o MODEL "$disk")
case "$model" in 'Samsung SSD 980 500GB'*) ;; *) echo 'Unexpected SSD model' >&2; exit 1;; esac
bytes=$(blockdev --getsize64 "$disk")
[ "$bytes" -gt 490000000000 ] && [ "$bytes" -lt 510000000000 ] || exit 1
if lsblk -nr -o MOUNTPOINTS "$disk" | sed '/^[[:space:]]*$/d' | read -r any_mount; then
  echo 'SSD or a child partition is mounted; refusing to erase.' >&2
  exit 1
fi
root_source=$(findmnt -n -o SOURCE /)
if lsblk -snrp -o NAME "$root_source" | grep -Fxq "$disk"; then
  echo 'Target contains the running OS; refusing to erase.' >&2
  exit 1
fi
if [ -d "$mount_dir" ] && [ -n "$(ls -A "$mount_dir")" ]; then
  echo 'Mount destination is not empty; refusing to hide existing files.' >&2
  exit 1
fi
if grep -Eq '^[^#].*[[:space:]]/mnt/dev-ssd[[:space:]]' /etc/fstab; then
  echo 'Mount destination already configured in fstab.' >&2
  exit 1
fi
if lsblk -nr -o TYPE "$disk" | grep -Eq 'crypt|lvm|raid'; then
  echo 'Target has active device-mapper or RAID dependents.' >&2
  exit 1
fi
[ ! -e "$mount_dir/.storage-ready" ] || { echo 'Storage already configured' >&2; exit 1; }
for tool in sfdisk mkfs.ext4 partprobe udevadm blkid mount; do
  command -v "$tool" >/dev/null || { echo "Missing tool: $tool" >&2; exit 1; }
done
backup="/etc/fstab.before-dev-ssd-$(date -u +%Y%m%dT%H%M%SZ)"
cp -p /etc/fstab "$backup"
printf 'Erasing confirmed SSD: %s (%s); HDD/OS remain unchanged.\n' "$disk_id" "$model"
sfdisk "$disk" <<'LAYOUT'
label: gpt
type=L
LAYOUT
partprobe "$disk"
udevadm settle
partition="${disk}p1"
[ -b "$partition" ] || exit 1
mkfs.ext4 -L dev-ssd -m 1 "$partition"
uuid=$(blkid -s UUID -o value "$partition")
mkdir -p "$mount_dir"
mount -o noatime "$partition" "$mount_dir"
printf '\n# Managed development SSD (dotfiles/storage/prepare-ssd.sh)\nUUID=%s %s ext4 defaults,noatime,nofail 0 2\n' "$uuid" "$mount_dir" >> /etc/fstab
mkdir -p "$mount_dir/worktrees" "$mount_dir/projects" "$mount_dir/cache/npm" "$mount_dir/cache/pip" "$mount_dir/cache/uv" "$mount_dir/builds"
chown -R "$owner:$(id -gn "$owner")" "$mount_dir/worktrees" "$mount_dir/projects" "$mount_dir/cache" "$mount_dir/builds"
printf '%s\n' "$uuid" > "$mount_dir/.storage-ready"
sync
if [ -d /run/systemd/system ]; then
  systemctl daemon-reload
fi
findmnt "$mount_dir"
printf 'SSD prepared. Previous fstab saved at %s\n' "$backup"
