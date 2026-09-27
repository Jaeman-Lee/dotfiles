#!/usr/bin/env python3
"""Prepare private state and web UI; activate RDP only after host protection."""
import argparse
import getpass
import hashlib
import json
import os
from pathlib import Path
import secrets
import shlex
import subprocess
import tempfile
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
STATE = Path.home() / ".local/share/ubuntu-web-desktop"
SCHEMA = "org.gnome.desktop.remote-desktop.rdp"
KEYS = ("enable", "view-only", "port", "negotiate-port", "tls-cert", "tls-key")


def run(*args, **kwargs):
    return subprocess.run(args, check=True, text=True, **kwargs)


def output(*args):
    return run(*args, capture_output=True).stdout.strip()


def private_write(path, content):
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as stream:
        stream.write(content)
        temporary = Path(stream.name)
    temporary.chmod(0o600)
    temporary.replace(path)


def compose(*args):
    command = ["docker", "compose", "--env-file", str(STATE / "compose.env"),
               "-f", str(HERE / "compose.yaml"), *args]
    # A user already assigned to docker may have an older login session.
    if subprocess.run(["docker", "info"], stdout=subprocess.DEVNULL,
                      stderr=subprocess.DEVNULL).returncode:
        run("sg", "docker", "-c", shlex.join(command))
    else:
        run(*command)


def prepare():
    STATE.mkdir(parents=True, exist_ok=True, mode=0o700)
    STATE.chmod(0o700)
    if not (STATE / "original.json").exists():
        if output("gsettings", "get", SCHEMA, "enable") != "false":
            raise SystemExit("Existing RDP configuration is enabled; review before replacing it.")
        status = output("env", "LC_ALL=C", "grdctl", "status")
        if "Username: (empty)" not in status or "Password: (empty)" not in status:
            raise SystemExit("Existing RDP credentials found; preserve them before proceeding.")
        original = {k: output("gsettings", "get", SCHEMA, k) for k in KEYS}
        original["unit_enabled"] = subprocess.run(
            ["systemctl", "--user", "is-enabled", "--quiet", "gnome-remote-desktop.service"]
        ).returncode == 0
        private_write(STATE / "original.json", json.dumps(original, indent=2))
    for name in ("rdp", "guacamole"):
        (STATE / name).mkdir(exist_ok=True, mode=0o700)
    credentials_path = STATE / "credentials.json"
    if not credentials_path.exists():
        private_write(credentials_path, json.dumps({
            "username": getpass.getuser(), "password": secrets.token_urlsafe(18),
            "rdp_username": "desktop", "rdp_password": secrets.token_urlsafe(32),
        }, indent=2))
    credentials = json.loads(credentials_path.read_text())
    cert, key = STATE / "rdp/tls.crt", STATE / "rdp/tls.key"
    if not cert.exists():
        run("openssl", "req", "-x509", "-newkey", "rsa:3072", "-nodes",
            "-days", "365", "-subj", "/CN=ubuntu-web-desktop",
            "-keyout", str(key), "-out", str(cert),
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        key.chmod(0o600)
    fingerprint = output("openssl", "x509", "-in", str(cert), "-noout",
                         "-fingerprint", "-sha256").split("=", 1)[1].lower()
    root = ET.Element("user-mapping")
    password_hash = credentials.get("password_hash")
    if not password_hash:
        password_hash = hashlib.sha256(credentials["password"].encode()).hexdigest()
    auth = ET.SubElement(root, "authorize", username=credentials["username"],
                         password=password_hash, encoding="sha256")
    connection = ET.SubElement(auth, "connection", name="Ubuntu PC")
    ET.SubElement(connection, "protocol").text = "rdp"
    params = {"hostname": "host.docker.internal", "port": "13389",
              "username": credentials["rdp_username"], "password": credentials["rdp_password"],
              "security": "nla", "cert-fingerprints": "sha256:" + fingerprint,
              "server-layout": "en-us-qwerty", "disable-audio": "true",
              "enable-wallpaper": "true", "color-depth": "32"}
    for name, value in params.items():
        ET.SubElement(connection, "param", name=name).text = value
    private_write(STATE / "guacamole/user-mapping.xml", ET.tostring(root, encoding="unicode"))
    private_write(STATE / "compose.env", f"LOCAL_UID={os.getuid()}\nLOCAL_GID={os.getgid()}\nDESKTOP_STATE={STATE}\n")
    tail = json.loads(output("tailscale", "status", "--json"))
    dns = tail["Self"]["DNSName"].rstrip(".")
    password_hint = credentials.get("password", "설정할 때 입력한 Ubuntu 로그인 비밀번호 (원문 저장 안 함)")
    private_write(STATE / "접속정보.txt", (
        f"Ubuntu 원격 화면\n\n주소: https://{dns}:8443/\n"
        f"아이디: {credentials['username']}\n비밀번호: {password_hint}\n\n"
        "갤럭시/iPad에서 Tailscale 연결 후 접속하세요.\n"
        "이 파일은 비밀번호가 포함되어 있으므로 Git/이슈/채팅에 붙여넣지 마세요.\n"
    ))
    run("python3", str(HERE / "install-mobile-input.py"))
    compose("up", "-d")
    print(f"Web UI prepared at http://127.0.0.1:18080/; credentials: {STATE / '접속정보.txt'}")


def activate():
    # /run is cleared on reboot. Only the root-owned firewall unit creates this marker.
    marker = Path("/run/ubuntu-web-desktop/firewall-ready")
    if not marker.exists() or marker.stat().st_uid != 0 or marker.read_text().strip() != "13389":
        raise SystemExit("Run enable-host.sh with sudo first. RDP remains disabled.")
    dropin = Path.home() / ".config/systemd/user/gnome-remote-desktop.service.d"
    dropin.mkdir(parents=True, exist_ok=True)
    private_write(dropin / "90-ubuntu-web-desktop.conf", (
        "[Service]\nExecStartPre=/usr/bin/test -r /run/ubuntu-web-desktop/firewall-ready\n"
    ))
    run("systemctl", "--user", "daemon-reload")
    credentials = json.loads((STATE / "credentials.json").read_text())
    # Set both paths before constructing grdctl's settings object, avoiding
    # misleading "invalid certificate" diagnostics during first-time setup.
    run("gsettings", "set", SCHEMA, "tls-cert", str(STATE / "rdp/tls.crt"))
    run("gsettings", "set", SCHEMA, "tls-key", str(STATE / "rdp/tls.key"))
    run("grdctl", "rdp", "set-port", "13389")
    run("grdctl", "rdp", "disable-port-negotiation")
    # grdctl 50.2 creates a separate buffered reader for each prompt. Sending
    # two lines together can lose the second line and trigger a segmentation
    # fault. Pass the non-secret username as an argument, only the password
    # through stdin, and keep the password out of process arguments and logs.
    run("grdctl", "rdp", "set-credentials", credentials["rdp_username"],
        input=credentials["rdp_password"] + "\n", stdout=subprocess.DEVNULL,
        timeout=30)
    run("grdctl", "rdp", "disable-view-only")
    run("grdctl", "rdp", "enable")
    run("systemctl", "--user", "enable", "--now", "gnome-remote-desktop.service")
    print("Desktop sharing enabled on protected port 13389.")


def stop():
    run("grdctl", "rdp", "disable")
    run("systemctl", "--user", "stop", "gnome-remote-desktop.service")
    compose("stop")


def restore():
    stop()
    original = json.loads((STATE / "original.json").read_text())
    run("grdctl", "rdp", "clear-credentials")
    for key in KEYS:
        run("gsettings", "set", SCHEMA, key, original[key])
    if not original["unit_enabled"]:
        run("systemctl", "--user", "disable", "gnome-remote-desktop.service")
    dropin = Path.home() / ".config/systemd/user/gnome-remote-desktop.service.d/90-ubuntu-web-desktop.conf"
    dropin.unlink(missing_ok=True)
    run("systemctl", "--user", "daemon-reload")
    print("Original RDP settings restored. Private credentials retained for deliberate cleanup.")


if __name__ == "__main__":
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "activate", "stop", "restore"))
    args = parser.parse_args()
    globals()[args.action]()
