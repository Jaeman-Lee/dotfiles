---
title: Ubuntu PC를 갤럭시·iPad 웹에서 원격 조작
date: 2026-09-27
vault: 미설정
---

# Ubuntu PC를 갤럭시·iPad 웹에서 원격 조작

요구사항과 진행 상태: [GitHub issue #14](https://github.com/Jaeman-Lee/dotfiles/issues/14).
변경 검토: [draft PR #17](https://github.com/Jaeman-Lee/dotfiles/pull/17).
구현과 검증 기록: [커밋 22e3357](https://github.com/Jaeman-Lee/dotfiles/commit/22e3357).
이 문서는 운영 절차의 원본이다. 지정된 Obsidian Vault는 확인되지 않아 저장소 `docs/`에 보관한다.
실제 비밀번호·인증서 개인키·접속 세션·화면 캡처는 Git에 넣지 않는다.

## 사용 방식

갤럭시 S24 또는 iPad에서 Tailscale을 연결하고 웹주소에 접속하면 이 PC의 현재 GNOME 화면을 제어한다.
열려 있는 Firefox, Codex CLI, VS Code 등은 PC에서 계속 실행된다.
Firefox Sync나 Codex 전용 연결은 필요하지 않다.

연결 경로는 `모바일 브라우저 → Tailscale Serve HTTPS:8443 → Guacamole → GNOME RDP:13389`이다.
Guacamole 웹 포트는 PC의 `127.0.0.1:18080`에만 공개한다. guacd 포트는 Docker 네트워크 내부에만 둔다.
RDP 13389는 로컬 루프백과 전용 Docker 브리지 `br-udesk`에서만 접근할 수 있도록 nftables로 제한한다.
Tailscale Funnel이나 공유기 포트 포워딩을 사용하지 않는다. Tailnet의 기존 접근 정책은 그대로 적용된다.

## Ubuntu에서 준비

확인한 환경: Ubuntu 26.04.1 LTS, GNOME 50, Wayland, Docker Engine 29.8.1, Compose 5.5.1.
GNOME Remote Desktop과 Tailscale이 이미 설치되어 있다. Docker 그룹에 가입했지만 현재 로그인 세션에
그룹이 반영되지 않은 경우 설치 스크립트가 `sg docker`로 실행한다.

저장소 루트에서 일반 사용자로 실행한다.

```bash
python3 remote-desktop/setup.py prepare
sudo bash remote-desktop/enable-host.sh
```

첫 명령은 공식 Guacamole 1.6.0 이미지 두 개를 실행하고 무작위 웹/RDP 비밀번호와 TLS 인증서를 생성한다.
이미지는 digest로 고정했다. 사용자 한 명과 연결 한 개를 위한 XML 인증을 사용하므로 별도 DB는 없다.
기존 RDP가 활성화되어 있거나 저장된 RDP 자격 증명이 있으면 자동으로 덮어쓰지 않고 중지한다.

두 번째 명령은 다음을 수행한다.

1. 전용 nftables 테이블과 부팅 시 적용할 systemd 서비스를 설치한다. 다른 방화벽 규칙은 지우지 않는다.
2. 방화벽 적용 확인 후 사용자 GNOME RDP를 전용 포트에서 켜고 입력 제어를 허용한다.
3. 부팅 후 방화벽 준비 전에는 RDP 서비스가 시작되지 않도록 사용자 서비스에 시작 조건을 추가한다.
4. Tailscale 전용 HTTPS 8443 주소를 로컬 웹 포트에 연결한다. 다른 Serve 설정이 이미 있으면 덮어쓰지 않는다.

Tailscale에서 HTTPS 활성화가 필요하다는 안내와 링크가 나오면 해당 Tailnet 관리자 계정으로 완료한다.
완료되지 않으면 웹 원격 접속은 아직 준비되지 않은 상태다.

### 접속 정보 확인

PC에서 다음 파일을 연다. 웹 로그인 아이디와 비밀번호가 들어 있다.

```bash
xdg-open "$HOME/.local/share/ubuntu-web-desktop/접속정보.txt"
```

이 파일과 `credentials.json`, `guacamole/user-mapping.xml`, `rdp/tls.key`는 개인 폴더 안에 0600으로 저장한다.
비밀번호를 GitHub 이슈·PR·채팅에 붙여넣지 않는다. Ubuntu 로그인 비밀번호와 웹 비밀번호는 별개다.

## 갤럭시 S24

1. Tailscale 앱에서 이 PC와 같은 Tailnet에 연결한다. 기존 연결을 그대로 사용한다.
2. Firefox 또는 Chrome에서 PC의 `접속정보.txt`에 있는 HTTPS 주소를 연다.
3. 파일에 적힌 `desktop` 아이디와 웹 비밀번호로 로그인한다.
4. `Ubuntu PC` 연결을 선택한다. 연결이 하나면 바로 화면이 열릴 수도 있다.
5. 화면 왼쪽 가장자리에서 오른쪽으로 밀면 Guacamole 메뉴가 열린다.
6. 메뉴의 입력 설정에서 화면 키보드 또는 텍스트 입력을 선택한다. 작은 화면에서는 마우스 터치패드 모드가 편하다.

화면을 가로로 돌리고 확대/축소해서 사용한다. 짧은 Codex 지시와 작업 진행 확인에 적합하다.
휴대폰의 한글 조합 입력이 잘 전달되지 않으면 메뉴의 클립보드 텍스트 칸에 붙여넣고 PC 쪽에 붙여넣는다.
이는 실제 기기의 키보드/브라우저 조합에서 별도 확인해야 한다.

## iPad

1. Tailscale 앱에서 같은 Tailnet에 연결한다.
2. Safari에서 동일한 HTTPS 주소를 열고 같은 웹 계정으로 로그인한다.
3. `Ubuntu PC`를 선택한다. 가로 화면으로 사용하면 PC 화면을 넓게 볼 수 있다.
4. 터치 입력과 화면 키보드를 사용할 수 있다. 연결된 Bluetooth 키보드·마우스가 있다면 함께 사용할 수 있다.
5. 일부 단축키는 iPadOS/Safari가 먼저 처리한다. 필요한 키 조합은 Guacamole 화면 키보드로 전달한다.

갤럭시와 iPad 모두 주소를 즐겨찾기에 저장하면 다음 접속이 간단하다.
두 기기에서 동시에 연결하는 기능은 별도 검증하지 않았으므로 우선 한 기기씩 사용한다.

## 운영과 복구

- 현재 로그인된 GNOME 세션을 공유한다. 전원이 꺼져 있거나 로그아웃된 PC에는 접속할 수 없다.
- 이 PC의 기존 자동 잠금/AC 절전 방지 설정은 별도 작업에서 적용되어 있었으며 여기서 변경하지 않는다.
- 수동 화면 잠금, 재부팅 직후, 모니터 전원/연결 변경은 실제 기기에서 추가 검증해야 한다.
- Docker 컨테이너는 재시작 정책을 사용한다. GNOME 공유는 사용자 로그인 후 시작한다.
- 자체 서명한 RDP 인증서는 365일 유효하며 Guacamole에 SHA-256 지문을 고정했다. 갱신할 때 XML 지문도 함께 갱신해야 한다.
- 영상·게임 스트리밍보다 데스크톱 작업을 위한 구성이다. 오디오는 현재 끄고 파일 전송은 설정하지 않았다.

상태 확인:

```bash
grdctl status
tailscale serve status
systemctl status ubuntu-web-desktop-firewall.service
systemctl --user status gnome-remote-desktop.service
```

일시 중지(웹 컨테이너와 화면 공유):

```bash
python3 remote-desktop/setup.py stop
```

다시 시작:

```bash
python3 remote-desktop/setup.py prepare
python3 remote-desktop/setup.py activate
```

최초 RDP 설정으로 복원하고 웹 컨테이너를 중지:

```bash
python3 remote-desktop/setup.py restore
sudo tailscale serve --https=8443 off
```

복원은 최초 `original.json`에 저장된 설정값을 사용한다. 이 설치에서 생성한 RDP 자격 증명을 지운다.
이 설치는 기존 RDP 자격 증명이 비어 있던 PC에서 검증했다. 이미 저장된 자격 증명이 있는 다른 PC에
그대로 적용해서는 안 된다. 개인 접속 정보와 최초 백업은 복원 후에도 남겨 수동으로 정리할 수 있게 한다.

RDP가 중지된 것을 확인한 뒤 전용 방화벽 규칙도 해제하려면:

```bash
sudo systemctl disable --now ubuntu-web-desktop-firewall.service
sudo nft delete table inet ubuntu_web_desktop
sudo rm -f /run/ubuntu-web-desktop/firewall-ready
```

## 검증 기록 — 2026-09-27

- Python 구문 검사 및 두 셸 스크립트 구문 검사 통과.
- 관리자 방화벽 준비 전 `activate`가 거부되고 RDP가 꺼진 채로 유지됨을 확인.
- Docker 컨테이너 실행, 로컬 HTTP 200, 브라우저 로그인 화면 렌더링 확인.
- 잘못된 비밀번호 HTTP 403, 정상 인증 후 `Ubuntu PC` 연결 조회, 테스트 토큰 폐기 확인.
- 사용자가 관리자 명령을 실행해 전용 방화벽 서비스와 Tailscale HTTPS 주소 등록 완료.
- 실제 GNOME 화면 수신, 키보드 창 전환 단축키와 마우스 클릭 반응 확인.
- 전용 Docker 브리지의 RDP 연결 성공, 다른 Docker 브리지의 연결 차단 확인.
- 인증서 검증을 생략하지 않고 SHA-256 지문이 일치하는 인증서로 RDP 연결 성공.
- Tailscale HTTPS URL의 인증서 검증 및 HTTP 200 확인.
- HTTPS 브라우저 로그인 후 1920×1088 RDP 캔버스 수신, 384×832 및 1024×1366 뷰포트에서 표시 확인.
- 비밀값 파일 권한 0600과 상위 디렉터리 0700 확인.
- 저장소/worktree, 개인 실행 상태, Docker 데이터·로그가 HDD(`/dev/sda`의 루트 LVM)에 위치함을 확인.
- 갤럭시/iPad 실기기 터치·한글 입력, 재부팅 및 수동 잠금 이후 연결은 미검증.

초기 활성화에서 GNOME `grdctl` 50.2에 사용자명과 비밀번호를 두 줄로 함께 전달하면 버퍼 처리 중
SIGSEGV가 발생했다. 사용자명은 인자로, 비밀번호 한 줄만 stdin으로 전달하도록 수정했고
같은 PC에서 등록·활성화 성공을 확인했다. 비밀번호는 명령 인자나 로그로 출력하지 않는다.

자동화 브라우저는 Ubuntu의 사용자 네임스페이스 제한 때문에 검증용 세션에 한해서
`--no-sandbox`로 실행했다. PC의 Firefox나 시스템 보안 설정을 변경한 것은 아니다.

## 근거

- [Ubuntu 데스크톱 공유](https://ubuntu.com/desktop/docs/en/24.04/how-to/share-your-desktop-remotely/)
- [Guacamole 공식 Docker 설치](https://guacamole.apache.org/doc/gug/guacamole-docker.html)
- [Guacamole 인증·RDP 연결 설정](https://guacamole.apache.org/doc/gug/configuring-guacamole.html)
- [Guacamole 모바일 입력과 클립보드](https://guacamole.apache.org/doc/gug/using-guacamole.html)
- [Tailscale Serve](https://tailscale.com/docs/features/tailscale-serve)
