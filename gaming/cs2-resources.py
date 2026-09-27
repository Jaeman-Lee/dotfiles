#!/usr/bin/python3
"""Root-only, reversible gaming resource profile; never restart workloads."""
import json
import os
from pathlib import Path
import subprocess
import sys

STATE = Path('/run/cs2-resources/baseline.json')
UNITS = {'kubepods.slice': {'cpu.max': '400000 100000', 'cpu.weight': '50',
                           'memory.high': str(8 * 1024**3)},
         'k3s.service': {'cpu.weight': '50'}}

def run(*args):
    return subprocess.check_output(args, text=True).strip()

def group(unit):
    name = run('systemctl', 'show', unit, '-p', 'ControlGroup', '--value')
    if not name or name == '/':
        raise RuntimeError(f'No active cgroup for {unit}')
    return Path('/sys/fs/cgroup') / name.lstrip('/')

def property_value(key, value):
    if key == 'cpu.max':
        quota, period = value.split()
        return 'CPUQuota=' + ('' if quota == 'max' else f'{int(quota)/int(period)*100:g}%')
    if key == 'cpu.weight':
        return f'CPUWeight={value}'
    return 'MemoryHigh=' + ('infinity' if value == 'max' else value)

def set_value(unit, key, value):
    subprocess.run(['systemctl', 'set-property', '--runtime', unit,
                    property_value(key, value)], check=True)

def restore():
    if not STATE.exists():
        return
    state = json.loads(STATE.read_text())
    for unit, values in state.items():
        directory = group(unit)
        for key, record in values.items():
            now = (directory / key).read_text().strip()
            if now == record['applied']:
                set_value(unit, key, record['before'])
            elif now != record['before']:
                print(f'Preserving external change: {unit} {key}', file=sys.stderr)
    STATE.unlink()

def apply():
    if STATE.exists():
        raise RuntimeError('Previous profile state exists; restore it first.')
    state = {}
    for unit, values in UNITS.items():
        directory = group(unit)
        state[unit] = {}
        for key, target in values.items():
            before = (directory / key).read_text().strip()
            if key == 'memory.high':
                # Do not force immediate memory reclaim on a busy server.
                usage = int((directory / 'memory.current').read_text())
                if usage > int(target) * 0.8:
                    print(f'Skip memory throttle: {unit} already above 80% of target')
                    continue
                if before != 'max':
                    target = str(min(int(before), int(target)))
            if key == 'cpu.max' and before.split()[0] != 'max':
                quota, period = map(int, before.split())
                target = f'{min(quota, 4 * period)} {period}'
            if key == 'cpu.weight':
                target = str(min(int(before), int(target)))
            state[unit][key] = {'before': before, 'applied': target}
    STATE.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state))
    STATE.chmod(0o600)
    try:
        for unit, values in state.items():
            for key, record in values.items():
                set_value(unit, key, record['applied'])
    except Exception:
        restore()
        raise

if __name__ == '__main__':
    if os.geteuid() != 0:
        raise SystemExit('Run through the installed cs2-resources system service.')
    if sys.argv[1:] == ['start']:
        apply()
    elif sys.argv[1:] == ['stop']:
        restore()
    else:
        raise SystemExit('Expected start or stop')
