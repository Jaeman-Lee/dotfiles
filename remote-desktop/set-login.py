#!/usr/bin/env python3
"""Set the web login using a local, hidden password dialog; never log the password."""
import getpass
import hashlib
import json
import subprocess
import urllib.error
import urllib.parse
import urllib.request

from setup import STATE, prepare, private_write


def set_login():
    username = getpass.getuser()
    result = subprocess.run([
        "zenity", "--forms", "--title=Ubuntu 원격 접속 로그인 설정",
        "--text=" + username + " 계정으로 웹 원격 접속을 설정합니다.\n"
        "평소 Ubuntu 로그인에 쓰는 비밀번호를 입력하세요.\n"
        "입력값은 채팅이나 파일에 원문으로 저장하지 않습니다.",
        "--add-password=Ubuntu 로그인 비밀번호", "--add-password=비밀번호 확인",
        "--separator=\x1f", "--ok-label=적용", "--cancel-label=취소",
    ], capture_output=True, text=True)
    if result.returncode:
        raise SystemExit("취소했습니다. 기존 웹 로그인은 유지됩니다.")
    parts = result.stdout.rstrip("\n").split("\x1f")
    if len(parts) != 2 or not parts[0] or parts[0] != parts[1]:
        raise SystemExit("비밀번호가 비어 있거나 일치하지 않습니다. 변경하지 않았습니다.")
    password = parts[0]
    path = STATE / "credentials.json"
    original = path.read_text()
    credentials = json.loads(original)
    credentials["username"] = username
    credentials["password_hash"] = hashlib.sha256(password.encode()).hexdigest()
    credentials.pop("password", None)
    private_write(path, json.dumps(credentials, indent=2))
    try:
        prepare()
        payload = urllib.parse.urlencode({"username": username, "password": password}).encode()
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open("http://127.0.0.1:18080/api/tokens", payload, timeout=10) as response:
            auth = json.load(response)
        request = urllib.request.Request("http://127.0.0.1:18080/api/tokens/" +
                                         urllib.parse.quote(auth["authToken"]), method="DELETE")
        opener.open(request, timeout=10).close()
    except Exception:
        private_write(path, original)
        prepare()
        raise SystemExit("새 로그인 검증에 실패해 기존 설정으로 복구했습니다. 비밀번호는 출력하지 않습니다.")
    print(f"완료: 웹 로그인 아이디 {username}, 입력한 비밀번호로 로그인 검증 성공.")
    print("Ubuntu 비밀번호를 나중에 변경하면 이 설정도 다시 실행하세요. 자동 동기화는 아닙니다.")


if __name__ == "__main__":
    set_login()
