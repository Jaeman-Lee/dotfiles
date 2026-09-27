#!/usr/bin/env python3
"""Read-only live-game metrics. Never signal the game or change its settings.

Private JSONL every five seconds, optional small performance-HUD capture each minute.
Stop this monitor independently with systemctl --user stop UNIT. A PID identity
check and three-hour limit bound observation without affecting play.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time

EXE = Path('/mnt/dev-ssd/games/Steam/steamapps/common/Counter-Strike Global Offensive/game/bin/linuxsteamrt64/cs2')


def counters(path):
    return {f[0].rstrip(':'): int(f[1]) for line in Path(path).read_text().splitlines()
            if len(f := line.split()) >= 2 and f[1].isdigit()}


def pressure(kind):
    return {line.split()[0]: dict(x.split('=') for x in line.split()[1:])
            for line in Path('/proc/pressure', kind).read_text().splitlines()}


def identity(pid):
    p = Path('/proc')/str(pid)
    if p.stat().st_uid != os.getuid() or (p/'exe').resolve() != EXE:
        raise ValueError('Expected own native CS2 process')
    return (p/'stat').read_text().rsplit(')', 1)[1].split()[19]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pid', type=int, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--hud-window', type=lambda x: int(x, 0))
    args = parser.parse_args()
    start = identity(args.pid)
    os.umask(0o077)
    args.output_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    gdk = window = None
    if args.hud_window:
        import gi
        gi.require_version('Gdk', '3.0')
        gi.require_version('GdkX11', '3.0')
        from gi.repository import Gdk, GdkX11
        gdk = Gdk
        window = GdkX11.X11Window.foreign_new_for_display(Gdk.Display.get_default(), args.hud_window)
    deadline = time.monotonic() + 10800
    next_hud = 0
    with (args.output_dir/'metrics.jsonl').open('x') as out:
        out.write(json.dumps({'type': 'metadata', 'pid': args.pid,
                              'start_ticks': start, 'clock_ticks': os.sysconf('SC_CLK_TCK'),
                              'interval_s': 5, 'started_at': time.time(),
                              'read_only': True})+'\n')
        while time.monotonic() < deadline:
            tick = time.monotonic()
            try:
                if identity(args.pid) != start:
                    break
                proc = Path('/proc')/str(args.pid)
                fields = (proc/'stat').read_text().rsplit(')', 1)[1].split()
                status = counters(proc/'status')
                row = {'time': time.time(), 'monotonic': tick,
                       'memory_kib': counters('/proc/meminfo'),
                       'vmstat': counters('/proc/vmstat'),
                       'pressure': {k: pressure(k) for k in ('cpu', 'memory', 'io')},
                       'game': {'minor_faults': int(fields[7]), 'major_faults': int(fields[9]),
                                'cpu_ticks': int(fields[11])+int(fields[12]),
                                'status_kib': {k: status.get(k, 0) for k in
                                               ('VmRSS', 'VmSwap', 'RssAnon', 'RssFile', 'RssShmem')},
                                'io': counters(proc/'io')},
                       'cpu_ticks': {f[0]: list(map(int, f[1:]))
                                     for line in Path('/proc/stat').read_text().splitlines()
                                     if (f := line.split())[0].startswith('cpu')},
                       'disks': {f[2]: list(map(int, f[3:]))
                                 for line in Path('/proc/diskstats').read_text().splitlines()
                                 if (f := line.split())[2] in ('sda', 'nvme0n1', 'dm-0')}}
            except (OSError, ValueError, IndexError):
                break  # Process exited or changed identity; never signal it.
            try:
                result = subprocess.run([
                    'nvidia-smi', '--query-gpu=utilization.gpu,utilization.memory,memory.used,memory.total,temperature.gpu,power.draw,clocks.gr,clocks.mem',
                    '--format=csv,noheader,nounits'], capture_output=True, text=True, timeout=3)
                row['gpu'] = result.stdout.strip() if result.returncode == 0 else None
            except (OSError, subprocess.TimeoutExpired):
                row['gpu'] = None
            if window and tick >= next_hud:
                try:
                    width = window.get_width()
                    if width >= 420 and window.get_height() >= 80:
                        pixbuf = gdk.pixbuf_get_from_window(window, width-420, 0, 420, 80)
                        if pixbuf:
                            name = f'hud-{int(row["time"])}.png'
                            pixbuf.savev(str(args.output_dir/name), 'png', [], [])
                            row['hud'] = name
                except Exception:
                    row['hud_error'] = True
                next_hud = tick + 60
            out.write(json.dumps(row)+'\n')
            out.flush()
            time.sleep(max(0, 5-(time.monotonic()-tick)))
        out.write(json.dumps({'type': 'end', 'time': time.time()})+'\n')


if __name__ == '__main__':
    main()
