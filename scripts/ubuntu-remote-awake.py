#!/usr/bin/env python3
"""Apply/restore GNOME idle settings for an AC-powered remote desktop."""
import argparse
import json
import os
from pathlib import Path
import subprocess

SETTINGS = [
    ('org.gnome.desktop.session', 'idle-delay', 'uint32 0'),
    ('org.gnome.desktop.screensaver', 'lock-enabled', 'false'),
    ('org.gnome.settings-daemon.plugins.power', 'sleep-inactive-ac-type', "'nothing'"),
    ('org.gnome.settings-daemon.plugins.power', 'sleep-inactive-ac-timeout', '0'),
    ('org.gnome.settings-daemon.plugins.power', 'idle-dim', 'false'),
]

def get(schema, key):
    return subprocess.check_output(['gsettings', 'get', schema, key], text=True).strip()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['apply', 'status', 'restore'], nargs='?', default='status')
    args = parser.parse_args()
    state = Path(os.environ.get('XDG_STATE_HOME', str(Path.home()/'.local/state'))) / 'dotfiles'
    backup = state / 'ubuntu-remote-awake.json'
    current = [(schema, key, get(schema, key)) for schema, key, _ in SETTINGS]
    if args.action == 'apply':
        state.mkdir(parents=True, exist_ok=True)
        if not backup.exists():
            with open(backup, 'x', opener=lambda path, flags: os.open(path, flags, 0o600)) as f:
                json.dump(current, f, indent=2)
        desired = SETTINGS
    elif args.action == 'restore':
        desired = json.loads(backup.read_text())
        if [(row[0], row[1]) for row in desired] != [(row[0], row[1]) for row in SETTINGS]:
            raise SystemExit('Backup keys do not match this script; no settings changed.')
    else:
        desired = []
    for schema, key, value in desired:
        subprocess.run(['gsettings', 'set', schema, key, value], check=True)
        if get(schema, key) != value:
            raise SystemExit(f'Could not verify {schema} {key}')
    for schema, key, _ in SETTINGS:
        print(f'{schema} {key} = {get(schema,key)}')
    if args.action != 'status':
        print(f'Backup: {backup}')

if __name__ == '__main__':
    main()
