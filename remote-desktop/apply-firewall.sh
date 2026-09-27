#!/usr/bin/env bash
set -euo pipefail
install -d -m 0755 /run/ubuntu-web-desktop
rm -f /run/ubuntu-web-desktop/firewall-ready
# Replace only our table in a single nft transaction, without flushing other rules.
rules=$(mktemp)
trap 'rm -f "$rules"' EXIT
if nft list table inet ubuntu_web_desktop >/dev/null 2>&1; then
    echo 'delete table inet ubuntu_web_desktop' > "$rules"
fi
cat /etc/ubuntu-web-desktop/firewall.nft >> "$rules"
nft --check --file "$rules"
nft --file "$rules"
echo 13389 > /run/ubuntu-web-desktop/firewall-ready
chmod 0644 /run/ubuntu-web-desktop/firewall-ready
