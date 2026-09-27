#!/usr/bin/env bash
# Run after setup.py prepare. No passwords are accepted as command arguments.
set -euo pipefail
[[ $EUID == 0 && -n ${SUDO_USER:-} && $SUDO_USER != root ]] || {
    echo 'Run this script with sudo from your desktop account.' >&2; exit 1;
}
source_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
desktop_uid=$(id -u "$SUDO_USER")
desktop_home=$(getent passwd "$SUDO_USER" | cut -d: -f6)
[[ -f "$desktop_home/.local/share/ubuntu-web-desktop/credentials.json" ]] || {
    echo 'Run setup.py prepare as your desktop user first.' >&2; exit 1;
}
python3 - "$desktop_home/.local/share/ubuntu-web-desktop/credentials.json" <<'PY'
import json, sys
with open(sys.argv[1]) as stream:
    if not json.load(stream).get("password_hash"):
        sys.exit("Run python3 remote-desktop/set-login.py first to choose your familiar web login.")
PY
command -v nft >/dev/null
# Refuse to take over an unrelated Tailscale Serve service on this port.
tailscale serve status --json | python3 -c '
import json,sys
d=json.load(sys.stdin)
owned=False
for address, config in d.get("Web", {}).items():
    if address.endswith(":8443"):
        handlers=config.get("Handlers", {})
        if handlers != {"/": {"Proxy": "http://127.0.0.1:18080"}}:
            sys.exit("Port 8443 already has another Tailscale Serve configuration.")
        owned=True
if "8443" in d.get("TCP", {}) and not owned:
    sys.exit("TCP port 8443 already belongs to another Tailscale Serve configuration.")
'
install -d -m 0755 /etc/ubuntu-web-desktop /usr/local/libexec
install -m 0644 "$source_dir/firewall.nft" /etc/ubuntu-web-desktop/firewall.nft
install -m 0755 "$source_dir/apply-firewall.sh" /usr/local/libexec/ubuntu-web-desktop-firewall
install -m 0644 "$source_dir/ubuntu-web-desktop-firewall.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable ubuntu-web-desktop-firewall.service
systemctl restart ubuntu-web-desktop-firewall.service
runuser -u "$SUDO_USER" -- env \
    XDG_RUNTIME_DIR="/run/user/$desktop_uid" \
    DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$desktop_uid/bus" \
    python3 "$source_dir/setup.py" activate
tailscale serve --bg --https=8443 http://127.0.0.1:18080
echo "Ready. Login details: $desktop_home/.local/share/ubuntu-web-desktop/접속정보.txt"
