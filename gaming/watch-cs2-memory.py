#!/usr/bin/env python3
"""Bounded local CS2 diagnostic. Stop only newly observed CS2 on pressure.

Output contains local process metrics: keep the JSONL outside Git.
No system settings are changed. A baseline run must have no CS2 running.
"""
import argparse
import json
import os
from pathlib import Path
import signal
import time

EXE = Path('/mnt/dev-ssd/games/Steam/steamapps/common/Counter-Strike Global Offensive/game/bin/linuxsteamrt64/cs2')


def counters(path):
    result = {}
    for line in Path(path).read_text().splitlines():
        fields = line.replace(':', '').split()
        if len(fields) >= 2 and fields[1].isdigit():
            result[fields[0]] = int(fields[1])
    return result


def games():
    found = {}
    for p in Path('/proc').glob('[0-9]*'):
        try:
            if p.stat().st_uid == os.getuid() and (p/'comm').read_text().strip() == 'cs2' and (p/'exe').resolve() == EXE:
                # Start time prevents signalling an unrelated process after PID reuse.
                start = (p/'stat').read_text().rsplit(')', 1)[1].split()[19]
                found[int(p.name)] = start
        except (OSError, IndexError):
            pass
    return found


def stop(targets, sig):
    current = games()
    for pid, start in targets.items():
        if current.get(pid) == start:
            try:
                os.kill(pid, sig)
            except ProcessLookupError:
                pass


def pressure(kind):
    return {line.split()[0]: dict(item.split('=') for item in line.split()[1:])
            for line in Path('/proc/pressure', kind).read_text().splitlines()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds', type=int, default=150)
    parser.add_argument('--min-available-mib', type=int, default=2560)
    args = parser.parse_args()
    if args.seconds < 1 or args.min_available_mib < 1024:
        parser.error('positive duration and at least 1024 MiB reserve required')
    if games():
        raise SystemExit('Close CS2 before starting this bounded diagnostic.')
    # Shader preprocessing can precede the game. Allow five minutes to start;
    # the requested measurement duration begins when CS2 is first observed.
    deadline = time.monotonic() + 300
    seen = {}
    reason = 'timeout'
    previous = None
    while time.monotonic() < deadline:
        now = time.monotonic()
        current = games()
        if current and not seen:
            deadline = now + args.seconds
        seen.update(current)
        mem = counters('/proc/meminfo')
        io = pressure('io')
        memory = pressure('memory')
        user = counters('/sys/fs/cgroup/user.slice/memory.stat')
        row = {'time': time.time(), 'available_mib': mem['MemAvailable']/1024,
               'swap_used_mib': (mem['SwapTotal'] - mem['SwapFree'])/1024,
               'io': io, 'memory': memory,
               'user': {k: user.get(k, 0) for k in ('anon', 'file', 'shmem', 'workingset_refault_file', 'pgscan_direct')},
               'games': {}}
        for pid in current:
            try:
                status = counters(f'/proc/{pid}/status')
                row['games'][pid] = {k: status.get(k, 0) for k in ('VmRSS', 'RssAnon', 'RssFile', 'RssShmem')}
                row['games'][pid]['read_bytes'] = counters(f'/proc/{pid}/io').get('read_bytes', 0)
            except OSError:
                pass
        print(json.dumps(row), flush=True)
        if current:
            if row['available_mib'] < args.min_available_mib:
                reason = 'memory reserve'
                break
            if previous:
                dt, total = previous
                io_full = (int(io['full']['total']) - total) / max(now-dt, 0.001) / 10000
                if io_full > 30 and row['available_mib'] < 4096:
                    reason = 'I/O stall above 30 percent with low memory reserve'
                    break
        elif seen:
            reason = 'game exited'
            break
        previous = now, int(io['full']['total'])
        time.sleep(1)
    print(json.dumps({'stop_reason': reason}), flush=True)
    stop(seen, signal.SIGTERM)
    time.sleep(5)
    stop(seen, signal.SIGKILL)


if __name__ == '__main__':
    main()
