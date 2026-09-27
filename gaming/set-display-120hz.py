#!/usr/bin/python3
"""Preserve the current GNOME layout, changing only the primary FHD refresh."""
import json
import argparse
from pathlib import Path
from gi.repository import Gio, GLib

parser = argparse.ArgumentParser()
parser.add_argument('--restore', action='store_true', help='Restore the saved refresh modes')
args = parser.parse_args()
bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
def call(method, args=None):
    return bus.call_sync('org.gnome.Mutter.DisplayConfig',
        '/org/gnome/Mutter/DisplayConfig', 'org.gnome.Mutter.DisplayConfig',
        method, args, None, Gio.DBusCallFlags.NONE, 5000, None)

serial, monitors, logical, properties = call('GetCurrentState').unpack()
current = {m[0][0]: next(x[0] for x in m[1] if x[-1].get('is-current'))
           for m in monitors if any(x[-1].get('is-current') for x in m[1])}
backup = Path.home() / '.local/state/cs2-setup/display-before.json'
backup.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
if args.restore and not backup.exists():
    raise SystemExit('No previous display mode snapshot exists.')
if not backup.exists():
    backup.write_text(json.dumps({'modes': current, 'layout': logical}, indent=2))
    backup.chmod(0o600)
config = []
changed = False
for x, y, scale, transform, primary, specs, props in logical:
    outputs = []
    for spec in specs:
        connector = spec[0]
        mode = current[connector]
        if args.restore:
            mode = json.loads(backup.read_text())['modes'][connector]
            changed |= mode != current[connector]
        elif primary:
            candidates = next(m[1] for m in monitors if m[0] == spec)
            target = next(m for m in candidates
                          if m[1:3] == (1920, 1080) and abs(m[3] - 120) < 0.1)
            changed |= mode != target[0]
            mode = target[0]
        outputs.append((connector, mode, {}))
    config.append((x, y, scale, transform, primary, outputs))
if changed:
    call('ApplyMonitorsConfig', GLib.Variant('(uua(iiduba(ssa{sv}))a{sv})',
                                          (serial, 2, config, {})))
    print('Requested persistent display mode change; confirm Keep Changes on the display.')
else:
    print('Display already uses the requested mode.')
