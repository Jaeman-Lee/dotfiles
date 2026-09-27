#!/usr/bin/env bash
# Run with pkexec or sudo. Game/account data is managed by the desktop user.
set -euo pipefail
if [[ $EUID -ne 0 ]]; then
    echo 'Run this script with pkexec or sudo.' >&2
    exit 1
fi
source /etc/os-release
[[ $ID == ubuntu && $(dpkg --print-architecture) == amd64 ]] || exit 1

# Match the existing NVIDIA userspace version; do not replace the kernel driver.
gpu_package=libnvidia-gl-595
gpu_version=$(dpkg-query -W -f='${Version}' "$gpu_package:amd64")
dpkg --add-architecture i386
apt-get update
packages=(steam-installer steam-devices libvulkan1:amd64 libvulkan1:i386
          "$gpu_package:i386=$gpu_version" vulkan-tools)
apt-get --simulate --no-remove install "${packages[@]}"
DEBIAN_FRONTEND=noninteractive apt-get --yes --no-remove install "${packages[@]}"
