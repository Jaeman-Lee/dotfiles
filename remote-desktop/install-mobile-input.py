#!/usr/bin/env python3
"""Build the local Guacamole UI extension. Restart web to load updates."""
from pathlib import Path
import os
import tempfile
import zipfile


def install():
    source = Path(__file__).resolve().parent / 'mobile-input'
    destination = Path.home() / '.local/share/ubuntu-web-desktop/guacamole/extensions'
    destination.mkdir(parents=True, exist_ok=True, mode=0o700)
    with tempfile.NamedTemporaryFile(dir=destination, suffix='.tmp', delete=False) as stream:
        temporary = Path(stream.name)
    try:
        with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(source.iterdir()):
                if path.is_file():
                    archive.write(path, path.name)
        temporary.replace(destination / 'ubuntu-mobile-input.jar')
    finally:
        temporary.unlink(missing_ok=True)


if __name__ == '__main__':
    os.umask(0o077)
    install()
    print('Mobile input extension installed. Restart the web container to load it.')
