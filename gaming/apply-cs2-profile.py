#!/usr/bin/python3
"""Apply only selected settings; private rollback copies stay outside Git."""
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import vdf

ROOT = Path(__file__).resolve().parent
HOME = Path.home()
STEAM = Path('/mnt/dev-ssd/games/Steam')
BACKUP = HOME / '.local/state/cs2-setup/backups' / datetime.now().strftime('%Y%m%d-%H%M%S')
if subprocess.run(['pgrep', '-u', str(os.getuid()), '-x', 'steam'],
                  stdout=subprocess.DEVNULL).returncode == 0:
    raise SystemExit('Close Steam before changing its configuration.')
BACKUP.mkdir(mode=0o700, parents=True)

def save(path, content, mode=0o600):
    if path.exists():
        dest = BACKUP / path.relative_to(HOME) if path.is_relative_to(HOME) else BACKUP / 'ssd' / path.relative_to(STEAM)
        dest.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        shutil.copy2(path, dest)
        dest.chmod(0o600)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.cs2-setup-tmp')
    temporary.write_text(content)
    temporary.chmod(mode)
    temporary.replace(path)

# This setup is for one signed-in account; never guess between multiple accounts.
configs = list(STEAM.glob('userdata/*/config/localconfig.vdf'))
if len(configs) != 1:
    raise SystemExit('Expected exactly one Steam account; no configuration changed.')
local = configs[0]
data = vdf.loads(local.read_text())
node = data['UserLocalConfigStore']
for key in ('Software', 'Valve', 'Steam', 'apps', '730'):
    actual = next((k for k in node if k.lower() == key.lower()), key)
    node = node.setdefault(actual, {})
launch = str(HOME / '.local/bin/cs2-launch') + ' %command%'
previous = node.get('LaunchOptions', '')
if previous and previous != launch:
    raise SystemExit('Existing launch options require a manual merge; left unchanged.')
node['LaunchOptions'] = launch
save(local, vdf.dumps(data, pretty=True))
save(HOME / '.local/bin/cs2-launch', (ROOT / 'cs2-launch.sh').read_text(), 0o755)
save(HOME / '.config/gamemode.ini', (ROOT / 'gamemode.ini').read_text())
save(HOME / '.config/cs2/workstation.cfg', (ROOT / 'workstation.cfg').read_text())
game_cfg = STEAM / 'steamapps/common/Counter-Strike Global Offensive/game/csgo/cfg/workstation.cfg'
save(game_cfg, (ROOT / 'workstation.cfg').read_text())
# Partial video configuration: preserve unrelated values and hardware identifiers.
video = local.parent.parent / '730/local/cfg/cs2_video.txt'
settings = vdf.loads(video.read_text()) if video.exists() else {}
if 'Version' in settings.get('video.cfg', {}):
    settings['video.cfg'].update(json.loads((ROOT / 'video-baseline.json').read_text()))
    save(video, vdf.dumps(settings, pretty=True))
    print('Updated initialized video settings. Verify again after game launch.')
else:
    print('Video settings deferred: launch CS2 once, close CS2 and Steam, then rerun.')
print('Installed launch wrapper, GameMode hooks and telemetry/input baseline.')
print(f'Private rollback backup: {BACKUP}')
