#!/usr/bin/env bash
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo 'Use pkexec to install the system helpers.' >&2; exit 1; }
profile_uid=${PKEXEC_UID:-${SUDO_UID:-}}
[[ $profile_uid =~ ^[0-9]+$ && $profile_uid -gt 0 ]] || exit 1
profile_user=$(getent passwd "$profile_uid" | cut -d: -f1)
[[ $profile_user =~ ^[a-z_][a-z0-9_-]*$ ]] || exit 1
source_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
backup_dir=/var/lib/cs2-setup/backups/$(date +%Y%m%d-%H%M%S)
install -d -m 0700 "$backup_dir"
for target in /usr/local/libexec/cs2-resources /etc/systemd/system/cs2-resources.service /etc/polkit-1/rules.d/60-cs2-resources.rules; do
    if [[ -e $target ]]; then cp -a --parents "$target" "$backup_dir/"; fi
done
install -d /usr/local/libexec
install -m 0755 "$source_dir/cs2-resources.py" /usr/local/libexec/cs2-resources
install -m 0644 "$source_dir/cs2-resources.service" /etc/systemd/system/cs2-resources.service
install -d /etc/systemd/system/cs2-resources.service.d
cat > /etc/systemd/system/cs2-resources.service.d/session.conf <<EOF
[Unit]
BindsTo=user@$profile_uid.service
After=user@$profile_uid.service
EOF
cat > /etc/polkit-1/rules.d/60-cs2-resources.rules <<EOF
polkit.addRule(function(action, subject) {
    if (action.id == "org.freedesktop.systemd1.manage-units" &&
        action.lookup("unit") == "cs2-resources.service" &&
        (action.lookup("verb") == "start" || action.lookup("verb") == "stop") &&
        subject.user == "$profile_user") {
        return polkit.Result.YES;
    }
});
EOF
chmod 0644 /etc/polkit-1/rules.d/60-cs2-resources.rules
systemctl daemon-reload
DEBIAN_FRONTEND=noninteractive apt-get --yes --no-remove install python3-vdf shellcheck
systemd-analyze verify /etc/systemd/system/cs2-resources.service
