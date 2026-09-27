#!/usr/bin/env python3
"""Install a reversible user-only Ptyxis X11 launcher; do not close existing terminals."""
from datetime import datetime
from pathlib import Path
import shutil
import subprocess

home = Path.home()
source = Path(__file__).resolve().parent
backup = home/'.local/state/cs2-setup/backups'/datetime.now().strftime('%Y%m%d-%H%M%S-terminal')
wrapper = home/'.local/bin/ptyxis-x11'
desktop = home/'.local/share/applications/org.gnome.Ptyxis.desktop'
vendor = Path('/usr/share/applications/org.gnome.Ptyxis.desktop')

text = vendor.read_text()
if 'Exec=ptyxis\n' not in text or 'DBusActivatable=true' not in text:
    raise SystemExit('Ptyxis vendor launcher changed; inspect before applying.')
text = text.replace('DBusActivatable=true', 'DBusActivatable=false')
text = text.replace('Exec=ptyxis', f'Exec="{wrapper}"')
backup.mkdir(parents=True, mode=0o700)
for target in (wrapper, desktop):
    if target.is_symlink():
        raise SystemExit(f'Refusing to overwrite symlink: {target}')
    if target.exists():
        shutil.copy2(target, backup/target.name)
    else:
        with (backup/'new-files.txt').open('a') as stream:
            stream.write(str(target)+'\n')
    target.parent.mkdir(parents=True, exist_ok=True)
wrapper.write_text((source/'ptyxis-x11').read_text())
wrapper.chmod(0o755)
desktop.write_text(text)
if shutil.which('desktop-file-validate'):
    subprocess.run(['desktop-file-validate', str(desktop)], check=True)
subprocess.run(['update-desktop-database', str(desktop.parent)], check=True)
print(f'User launcher installed. Backup: {backup}')
