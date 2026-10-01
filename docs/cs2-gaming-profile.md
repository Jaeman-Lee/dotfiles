---
title: CS2 개인 게임 프로필과 서버 자원 공존
date: 2026-09-27
tags: [gaming, cs2, linux, performance]
---

# CS2 개인 게임 프로필과 서버 자원 공존

> 2026-10-02: 마우스 시점 이동 축 누락을 복구하고 실제 적용·사용자 해결 확인을 완료했다.
> [원인 및 검증 기록](cs2-mouse-axes-20261002.md).

Vault 연결 미설정. 이 Markdown이 문서 원본이다.
실제 할 일은 [이슈 #13](https://github.com/Jaeman-Lee/dotfiles/issues/13),
설치 작업은 [이슈 #11](https://github.com/Jaeman-Lee/dotfiles/issues/11),
변경 검토는 [PR #12](https://github.com/Jaeman-Lee/dotfiles/pull/12)에서 관리한다.
구현은 [79a9400](https://github.com/Jaeman-Lee/dotfiles/commit/79a9400),
적용 검증과 인자 전달 수정은 [439a409](https://github.com/Jaeman-Lee/dotfiles/commit/439a409)에 기록했다.

## 적용 기준

사용자가 6가지 설정 적용과 감도 1.0·고정형 초록 조준점을 선택했다.
설정은 Ryzen 5 5600X / RTX 2060 / Ubuntu 26.04.1 / GNOME Wayland 환경에 맞춘다.

| 항목 | 설정 원본 | 동작 |
|---|---|---|
| 화면 | [전환 스크립트](../gaming/set-display-120hz.py) | GNOME에 광고된 FHD 120Hz 모드를 선택하고 기존 화면 배치를 유지한다. |
| 성능 | [실행 래퍼](../gaming/cs2-launch.sh), [GameMode](../gaming/gamemode.ini) | 게임 프로세스가 있는 동안 전원 프로필 performance를 유지하고 GameMode를 활성화한다. |
| 계측 | [게임 설정](../gaming/workstation.cfg) | FPS/프레임 시간·핑·네트워크 손실 표시를 켠다. |
| 서버 공존 | [자원 서비스](../gaming/cs2-resources.service), [제어 코드](../gaming/cs2-resources.py) | 게임 중 kubepods 총 CPU 4개 상당 상한, CPUWeight 50, 메모리 soft threshold 8GiB; k3s 관리 프로세스는 CPUWeight 50. 종료 시 이전 값으로 복원한다. |
| 그래픽·입력 | [비디오 설정](../gaming/video-baseline.json), [게임 설정](../gaming/workstation.cfg) | FHD 전체 화면, VSync 끔, CMAA2, MSAA 끔, 게임 240FPS·메뉴 60FPS 상한, 게임 메뉴의 감도 보존, 고정 초록 조준점, 표준 이동/전투 키. |
| 백업 | [적용 스크립트](../gaming/apply-cs2-profile.py) | 변경 전 사본은 개인 로컬 상태 폴더에 보존하고, 재현 가능한 선택 설정만 Git으로 관리한다. |

CPU 4개는 전체 12개 논리 CPU 중 4개 상당의 시간 할당량이다. 코어를 고정하지 않는다.
메모리 `MemoryHigh`는 회수/스로틀 기준이며 강제 종료 상한이나 예약 메모리가 아니다.
기존 제한이 더 작으면 유지한다. 현재 메모리 사용이 8GiB의 80%를 넘으면 새로운 메모리
스로틀은 생략한다. k3s나 Pod를 재시작하지 않는다. Kubernetes 자원만 대상으로 하므로
호스트에서 직접 실행하는 Docker/AI/빌드는 별도로 관리해야 한다. GPU 사용을 격리하지 않는다.

GameMode 기본 CPU 정책 변경은 이 환경에서 권한 오류가 발생했다.
Ubuntu의 `powerprofilesctl launch`로 게임 수명 동안 performance 프로필을 유지해 보완한다.
split-lock 보호 변경, 오버클럭, CPU 코어 고정은 적용하지 않는다.
GameMode가 활성화된 동안 자원 서비스가 적용되므로 향후 다른 GameMode 게임에도 적용된다.

240FPS는 측정 전 시작 기준이다. 실제 FPS, 지연 개선, 1% low 향상을 보장하지 않는다.
설치 완료 후 연습 맵에서 연막/교전 구간의 프레임 시간을 보고 상한과 그래픽 품질을 조정한다.
Linux의 MSAA 성능 이슈 보고를 고려해 최초 기준은 CMAA2로 정했다. 그래픽 옵션 중 명시하지
않은 항목은 게임의 자동 감지를 사용한다. 하드웨어 마우스 DPI는 변경하지 않는다.

## 적용과 복구

```bash
pkexec /usr/bin/bash "$PWD/gaming/install-gaming-profile.sh"
python3 gaming/set-display-120hz.py
# Steam이 완전히 종료된 상태에서 실행한다.
/usr/bin/python3 gaming/apply-cs2-profile.py
```

Steam의 CS2 시작 옵션은 `~/.local/bin/cs2-launch %command%`에 해당하는 절대 경로로
설정한다. 다른 시작 옵션이 이미 있으면 자동으로 덮어쓰지 않는다. `workstation.cfg`는
기존 autoexec와 다른 파일이며 게임 시작 시 명시적으로 실행한다.
다운로드 중인 Steam을 잠시 정상 종료해 설정을 적용하고 다시 열면 다운로드가 이어진다.

- 화면 복구: `python3 gaming/set-display-120hz.py --restore` 후 변경 유지.
- 서버 자원 즉시 복구: `systemctl stop cs2-resources.service`.
- 게임별 적용 해제: Steam CS2 시작 옵션을 비운다. 전원 프로필 hold는 게임 종료 시 해제된다.
- 개인 설정 이전 사본: `~/.local/state/cs2-setup/backups/`.
- 시스템 도우미 이전 사본: `/var/lib/cs2-setup/backups/`.
- 서버 자원 원래 값은 활성 세션 중 root 소유 `/run/cs2-resources/baseline.json`에 보관한다.
  복구 시 관리자가 별도로 변경한 값은 덮어쓰지 않는다. 사용자 세션 종료 시 서비스도 정지한다.

로그인 정보가 들어 있는 `localconfig.vdf`, 사용자 식별자, Steam Cloud 전체 파일,
게임 로그/다운로드 파일은 Git에 포함하지 않는다. 설정 원본은 위 링크의 저장소 파일이다.

## 검증과 근거

- GNOME D-Bus에서 `1920x1080@120.000`과 저장된 `monitors.xml` 확인.
- 자원 제어 단위 테스트: 정상 복구, 더 엄격한 기존 제한 보존, 외부 변경 보존,
  메모리 과다 사용 시 스로틀 생략, 일부 적용 실패 시 복구.
- [GameMode 공식 사용법](https://github.com/FeralInteractive/gamemode).
- [Valve 내장 계측 안내](https://help.steampowered.com/en/faqs/view/5E6F-5B36-5485-F6B9).
- [Valve Linux 이슈의 실제 비디오 설정/성능 보고](https://github.com/ValveSoftware/csgo-osx-linux/issues/4155).
- 게임 파일의 `game/csgo/cfg/user_keys_default.vcfg`에서 표준 키 바인딩을 확인했다.

실제 게임 다운로드 완료와 플레이 검증은 파일/서비스 설정 검증과 별개로 이슈에 기록한다.
비디오 설정은 게임이 완전한 설정 파일을 생성한 최초 실행 후 재적용해야 한다.
미초기화 상태에서는 적용 스크립트가 비디오 변경을 미루고 안내한다.
첫 실행 후 자동 감지로 설정이 달라진 사례와 재적용·안정성 검증 결과는
[데스크톱 안정성 조사](cs2-desktop-stability-20260927.md)에 기록했다.

## 2026-09-27 적용 검증

- 시스템 서비스와 해당 서비스 start/stop만 허용하는 사용자 한정 Polkit 규칙 설치.
- `shellcheck -x gaming/*.sh`, Python 구문 검사, 자원 테스트 4개 통과.
- 실제 서비스 활성화 시 kubepods `cpu.max=400000 100000`, `cpu.weight=50`,
  `memory.high=8589934592` 확인. 정지 시 기존 `max 100000`, `430`, `max`로 복구.
- 실제 게임 실행 래퍼로 테스트 프로세스를 실행해 performance 프로필과 자원 제한을 확인.
  종료 후 balanced, GameMode inactive, 자원 서비스 inactive 및 기존 값 복구 확인.
- `powerprofilesctl launch --profile performance --appid cs2 -- gamemoded -t` 전체 통과.
  래퍼의 `--`는 게임의 `-h` 해상도 옵션이 전원 도구의 help 옵션으로 해석되지 않게 한다.
- Steam 정상 종료 후 설정 반영, 재시작 후 CS2 시작 옵션과 비디오 설정 유지 확인.
  적용된 GameMode/게임 설정/래퍼/시스템 도우미가 Git 원본과 일치함을 확인.
- Steam 다운로드 재개 후, 사용자가 CS2 정상 구동을 확인했다.
  설치·실행 목표는 완료했으며, 게임 내 개별 설정 반영 화면과 맵 내 FPS/프레임 시간
  비교는 별도로 측정하지 않았다. 240FPS 상한은 성능 측정 결과가 아니다.

이후 실전 관측과 개인 설정 제안은 [경기 관측 기록](cs2-live-session-20260927.md)에 있다.
사용자가 메뉴 감도 2.56과 정상 조작감을 확인하여 시작 cfg의 기존 감도 1.0 강제를
제거했다. 감도는 게임 메뉴에 저장된 값을 유지한다. 제안한 그래픽/레이더/음향 변경은
아직 적용하지 않았으며 현재 FPS 상한도 240을 유지한다.
