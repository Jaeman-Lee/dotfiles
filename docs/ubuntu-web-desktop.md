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
python3 remote-desktop/set-login.py
sudo bash remote-desktop/enable-host.sh
```

첫 명령은 공식 Guacamole 1.6.0 이미지 두 개와 내부 RDP 인증 정보, TLS 인증서를 준비한다.
이미지는 digest로 고정했다. 사용자 한 명과 연결 한 개를 위한 XML 인증을 사용하므로 별도 DB는 없다.
기존 RDP가 활성화되어 있거나 저장된 RDP 자격 증명이 있으면 자동으로 덮어쓰지 않고 중지한다.

두 번째 명령의 PC 전용 비공개 입력창에 평소 Ubuntu 로그인 비밀번호를 입력한다.
웹 아이디는 PC 사용자명으로 설정하고 비밀번호는 Guacamole이 지원하는 SHA-256 해시로 저장한다.
입력한 비밀번호로 웹 로그인 검증까지 자동으로 수행하며, 비밀번호 원문은 파일이나 로그에 저장하지 않는다.
이는 기존 OS 인증의 자동 연동이 아니라 같은 로그인 정보로 맞추는 방식이다.
Ubuntu 비밀번호를 바꾸면 `set-login.py`를 다시 실행한다.

마지막 관리자 명령은 다음을 수행한다.

1. 전용 nftables 테이블과 부팅 시 적용할 systemd 서비스를 설치한다. 다른 방화벽 규칙은 지우지 않는다.
2. 방화벽 적용 확인 후 사용자 GNOME RDP를 전용 포트에서 켜고 입력 제어를 허용한다.
3. 부팅 후 방화벽 준비 전에는 RDP 서비스가 시작되지 않도록 사용자 서비스에 시작 조건을 추가한다.
4. Tailscale 전용 HTTPS 8443 주소를 로컬 웹 포트에 연결한다. 다른 Serve 설정이 이미 있으면 덮어쓰지 않는다.

Tailscale에서 HTTPS 활성화가 필요하다는 안내와 링크가 나오면 해당 Tailnet 관리자 계정으로 완료한다.
완료되지 않으면 웹 원격 접속은 아직 준비되지 않은 상태다.

### 접속 정보 확인

평소 PC 계정 이름과 설정할 때 입력한 Ubuntu 로그인 비밀번호로 접속한다.
PC에서 다음 파일을 열면 접속 주소와 계정 이름을 확인할 수 있다. 비밀번호 원문은 들어 있지 않다.

```bash
xdg-open "$HOME/.local/share/ubuntu-web-desktop/접속정보.txt"
```

이 파일과 `credentials.json`, `guacamole/user-mapping.xml`, `rdp/tls.key`는 개인 폴더 안에 0600으로 저장한다.
비밀번호를 GitHub 이슈·PR·채팅에 붙여넣지 않는다. 서버 내부 RDP 비밀번호는 자동 관리하므로 사용자가 입력할 필요가 없다.

## 갤럭시 S24

1. Tailscale 앱에서 이 PC와 같은 Tailnet에 연결한다. 기존 연결을 그대로 사용한다.
2. Firefox 또는 Chrome에서 PC의 `접속정보.txt`에 있는 HTTPS 주소를 연다.
3. PC 계정 이름과 설정 시 입력한 Ubuntu 로그인 비밀번호로 로그인한다.
4. `Ubuntu PC` 연결을 선택한다. 연결이 하나면 바로 화면이 열릴 수도 있다.
5. PC 화면에서 입력할 곳을 누른다. 하단 **글쓰기**의 흰 입력칸을 눌러 휴대폰 키보드를 연다.
6. 문장을 작성한 뒤 **전송 ↵** 또는 상단 **Enter**를 누른다. 붙여넣기와 Enter를 순서대로 보낸다. 입력 대상은 **Codex · 터미널**이 기본이다. 웹페이지나 일반 앱 입력칸이면 **브라우저 · 일반 앱**으로 바꾼다.
7. 한/영 전환은 평소 휴대폰 키보드에서 한다. 실행 없이 글만 넣으려면 **붙여넣기만**을 누른다. 기기 키보드의 Enter는 입력칸에서 줄바꿈한다.
8. **접기**로 화면을 넓히고 **글쓰기**로 입력칸을 다시 연다. **메뉴**에서 마우스 터치패드 모드 등을 선택한다.

화면을 가로로 돌리고 확대/축소해서 사용한다. 짧은 Codex 지시와 작업 진행 확인에 적합하다.
문장은 기기에서 먼저 완성하고 PC로 붙여넣는다. 작성 중에는 PC에 키 입력을 보내지 않는다.
PC 클립보드는 작성한 문장으로 바뀐다. 문장은 연결 화면을 떠나면 지워지며 별도 파일이나 로그에 저장하지 않는다.
붙여넣기 후에도 입력칸에 문장을 남기므로 PC 화면에서 결과를 확인하고 **지우기**를 누른다.
**붙여넣기만**을 누른 뒤 상단 **Enter**를 누르면 같은 글을 다시 붙이지 않고 Enter만 보낸다.
글을 수정하면 다음 전송에서 새 문장을 붙인다. **붙여넣기만**을 반복하면 중복 입력될 수 있다.

## iPad

1. Tailscale 앱에서 같은 Tailnet에 연결한다.
2. Safari에서 동일한 HTTPS 주소를 열고 같은 웹 계정으로 로그인한다.
3. `Ubuntu PC`를 선택한다. 가로 화면으로 사용하면 PC 화면을 넓게 볼 수 있다.
4. PC 화면의 입력할 곳을 누르고 하단 **글쓰기** 입력칸에 글을 쓴 뒤 **전송 ↵** 또는 상단 **Enter**를 누른다.
5. iPad의 화면 키보드에서는 **지구본(🌐)**으로 한국어/영어를 바꾼다. 한국어가 없다면
   iPad 설정 → 일반 → 키보드 → 키보드에서 한국어를 추가한다.
6. 외장 키보드에서는 글쓰기 입력칸에 초점을 두고 iPad의 **Control + Space** 언어 전환을 사용한다.
   한국어 키보드를 추가한 Apple 외장 키보드는 Caps Lock으로 영문/한국어를 바꾸는 방법도 지원한다.
7. 입력 대상은 **Codex · 터미널**이 기본이다. 일반 앱에서는 **브라우저 · 일반 앱**을 선택한다. **붙여넣기만**은 실행하지 않고, **전송 ↵**와 상단 **Enter**는 붙여넣은 뒤 실행한다.
8. 하단 **키보드**는 기존 Text input과 Ctrl/Alt/Esc/Tab을 연다. 한글 문장은 **글쓰기**를 우선 사용한다.

기존 Text input만으로는 실제 호스트에서 한글 누락과 PC 입력기에 의한 영문 재해석을 재현했다.
따라서 이전의 Text input 선택 안내를 기본 해법으로 사용하지 않는다.
글쓰기 방식은 기기에서 조합을 끝낸 문장을 클립보드로 보내 이 문제를 피한다.
PC의 전역 한/영 단축키는 임의로 변경하지 않는다.

갤럭시와 iPad 모두 주소를 즐겨찾기에 저장하면 다음 접속이 간단하다.
두 기기에서 동시에 연결하는 기능은 별도 검증하지 않았으므로 우선 한 기기씩 사용한다.

## 운영과 복구

### 모바일 입력 UI 업데이트

Guacamole 1.6.0의 공식 UI 확장 방식으로 하단 입력 도구를 추가한다.
소스는 [mobile-input](../remote-desktop/mobile-input/), 설치는
[install-mobile-input.py](../remote-desktop/install-mobile-input.py)에서 관리한다.
`setup.py prepare`는 확장 JAR도 생성한다. 이미 실행 중인 웹 컨테이너에는 다음 명령으로 적용한다.

```bash
python3 remote-desktop/install-mobile-input.py
sg docker -c 'docker compose --env-file "$HOME/.local/share/ubuntu-web-desktop/compose.env" -f remote-desktop/compose.yaml restart web'
```

웹 연결은 잠시 끊기며 PC 프로그램은 유지된다. 기기 브라우저를 새로고침한다.
확장은 터치 기기에서 글쓰기 입력칸을 기본 표시한다. 실제 키보드를 열려면 입력칸 또는 글쓰기 버튼을 누른다.
붙여넣기는 클립보드 전송 후 500ms 뒤 단축키를 보낸다. 원격 앱이 붙여넣기를 완료했다는 확인은 없으므로
문장을 자동 삭제하지 않고 PC 화면에서 확인하도록 안내한다. 일반 앱은 Ctrl+V, 기본 Codex·터미널 모드는 Ctrl+Shift+V다.
UI 확장은 1.6.0 내부 Angular 이벤트에 의존하므로 Guacamole 버전 변경 시 재검증한다.
전송은 붙여넣기 단축키 후 300ms를 기다린 뒤 Enter를 보낸다. 전송 중 버튼 연타를 막으며,
연결 변경·종료 또는 화면 이탈 시 대기 중인 Enter를 취소한다.
2026-09-27 후속 검증: Enter 전송/붙여넣기 후 중복 방지/터미널 키 순서/빈 입력·접힌 입력/연결 끊김/화면 이탈의
자동 회귀 테스트 6개 통과. 실제 Ubuntu GTK 입력창에서 `Enter 전송 확인 123`을 받고 activate 이벤트까지 확인했다.
스마트폰 키보드 표시와 PC 붙여넣기 성공은 사용자가 확인했으며, 이번 Enter 동작의 실기기 확인은 별도다.

2026-09-27 검증: 별도 로컬 웹 컨테이너와 임시 계정으로 360px 휴대폰 화면 및 1024px 태블릿 화면을 확인했다.
터치 에뮬레이션에서 입력칸 기본 표시, 접기/다시 열기와 포커스, 로컬 타이핑의 원격 키 중복 방지,
실제 Ubuntu GTK 테스트 창에 `English 한글 입력 123`이 그대로 도착하는 것을 확인했다.
최초에는 터미널 모드 키 순서만 전송 경계에서 검증했고, 이것만으로는 RDP 변환 후 실제 키 입력을 보장하지 못했다.
이후 실제 Ptyxis 터미널 검증과 수정 결과는 아래 기록을 따른다. 스마트폰 키보드 표시·붙여넣기 성공은 사용자가 확인했고 iPad는 확인이 남아 있다.
수정 후 브라우저 콘솔 오류 없음, 운영 웹의 확장 로드와 HTTPS HTTP 200을 확인했다.
임시 웹 컨테이너·계정 서비스와 테스트 창은 종료했다. 화면 캡처와 인증 자료는 Git에 넣지 않았다.

### Codex 이미지 붙여넣기 오류 수정

2026-09-27 사용자가 글을 전송했을 때 `Failed to paste image` 오류를 보고했다.
기본값이 일반 앱용 Ctrl+V였으며, 터미널 모드를 선택해도 Shift와 함께 소문자 `v` keysym(0x76)을 보내고 있었다.
실제 Ptyxis 테스트 창에서 터미널 프로그램이 Ctrl+V 바이트(0x16)를 받는 것을 재현했다.
Guacamole RDP 키 변환이 소문자에 맞춰 Shift를 해제하기 때문에 발생했다.
터미널 붙여넣기에는 대문자 `V` keysym(0x56)을 보내고, 기본 대상을 Codex·터미널로 바꿨다.
작은 체크박스 대신 입력칸 위에 대상 선택을 표시한다. PC 전역 터미널 단축키는 변경하지 않았다.

검증: Ptyxis의 `paste-clipboard` 설정은 `<ctrl><shift>v`다.
별도 Ptyxis 창의 실행 없는 입력 수신 프로그램에서 이전 코드의 `0x16 + CR`을 재현했고,
수정 후에는 `ESC[200~ + UTF-8 한글/영문/숫자 + ESC[201~ + CR`이 도착했다.
수정 확장을 다시 빌드·로드해 기본 선택 상태에서 실제 전송 버튼으로도 재검증했다.
자동 회귀 테스트는 7개 통과했다. 기존 Codex 세션에는 테스트 명령을 보내지 않았다.
이 검증은 실제 터미널 입력 경로까지 확인한 것이며 사용자의 Codex 화면 최종 확인은 별도다.

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
- 사용자 요청에 따라 웹 계정을 PC 계정명으로 변경하고 비공개 입력창에서 받은 비밀번호로 실제 로그인 성공 확인.
- OS 비밀번호 원문을 저장하지 않으며, XML에는 `encoding="sha256"`를 사용함을 확인.
- 저장소/worktree, 개인 실행 상태, Docker 데이터·로그가 HDD(`/dev/sda`의 루트 LVM)에 위치함을 확인.
- 갤럭시/iPad 실기기 터치·한글 입력, 재부팅 및 수동 잠금 이후 연결은 미검증.

초기 활성화에서 GNOME `grdctl` 50.2에 사용자명과 비밀번호를 두 줄로 함께 전달하면 버퍼 처리 중
SIGSEGV가 발생했다. 사용자명은 인자로, 비밀번호 한 줄만 stdin으로 전달하도록 수정했고
같은 PC에서 등록·활성화 성공을 확인했다. 비밀번호는 명령 인자나 로그로 출력하지 않는다.

사용자는 별도 임의 계정/긴 비밀번호의 수동 입력이 불편하다고 지적했다.
기존 PC 계정명과 익숙한 비밀번호로 맞추는 로컬 입력 절차를 추가하고,
[지속 작업 지침](../codex/AGENTS.md)에 기존 인증 흐름 활용·모바일 입력 최소화·핵심 사용 흐름 검증을 기록했다.
Git 원본과 `~/.codex/AGENTS.md`에 설치한 내용의 일치를 확인했으며 기존 지침도 보존했다.

자동화 브라우저는 Ubuntu의 사용자 네임스페이스 제한 때문에 검증용 세션에 한해서
`--no-sandbox`로 실행했다. PC의 Firefox나 시스템 보안 설정을 변경한 것은 아니다.

## 사용자 연결 확인과 대기 자원 측정 — 2026-09-27

사용자가 정상 연결을 확인했다. 이후 측정 시에는 활성 RDP 연결이 없었으므로 아래 값은 대기 상태다.
Guacamole 웹 컨테이너 메모리 약 142 MiB, guacd 약 8 MiB, GNOME 원격 데스크톱 RSS 약 181 MiB로
합계 약 331 MiB였다(서로 다른 메모리 집계 방식의 근사 합계). 웹 CPU 0.12%, guacd 0%,
GNOME 원격 데스크톱의 5초 CPU 평균은 0.40%였다. CPU 100%는 논리 CPU 한 개 기준이며 PC에는 12개가 있다.
시스템 가용 메모리는 약 6.9 GiB였다. 접속 중 스크롤·영상 등 화면 변화가 많은 작업의 최대 부하는 측정하지 않았다.

## 참고 자료

- [Ubuntu 데스크톱 공유](https://ubuntu.com/desktop/docs/en/24.04/how-to/share-your-desktop-remotely/)
- [Guacamole 공식 Docker 설치](https://guacamole.apache.org/doc/gug/guacamole-docker.html)
- [Guacamole 인증·RDP 연결 설정](https://guacamole.apache.org/doc/gug/configuring-guacamole.html)
- [Guacamole 모바일 입력과 클립보드](https://guacamole.apache.org/doc/gug/using-guacamole.html)
- [iPad 키보드 언어 전환](https://support.apple.com/guide/ipad/switch-between-keyboards-ipaddd28d7ed/ipados)
- [Guacamole 1.6.0 한글 조합 이벤트 처리](https://github.com/apache/guacamole-client/blob/1.6.0/guacamole/src/main/frontend/src/app/textInput/directives/guacTextInput.js)
- [Tailscale Serve](https://tailscale.com/docs/features/tailscale-serve)
