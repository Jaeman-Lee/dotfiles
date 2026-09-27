---
title: CS2 실행 중 데스크톱 지연 및 종료 조사
date: 2026-09-27
tags: [gaming, linux, troubleshooting]
---

# CS2 실행 중 데스크톱 지연 및 종료 조사

Vault 연결 미설정. 원본은 이 문서이며, 진행 상태는 다시 연
[이슈 #11](https://github.com/Jaeman-Lee/dotfiles/issues/11), 검토는
[draft PR #12](https://github.com/Jaeman-Lee/dotfiles/pull/12)에서 관리한다.

## 확인된 사실

- 최초 정상 실행은 사용자 확인을 받았으나 이후 터미널 전체 종료,
  CS2 종료 및 재실행 지연, Firefox 동반 지연을 보고받았다. 안정성은 미해결이다.
- 18:53:53 Ptyxis가 `Error flushing display: Resource temporarily unavailable`로
  종료했다. 18:53:42~18:54:05 GNOME Shell 응답 불가/회복 기록이 있다.
- 18:55:47 CS2가 Steam IPC의 broken pipe 및 fatal assertion으로 종료했다.
  당시 Steam도 사라졌고 재실행 로그는 비정상 종료를 감지했다.
  터미널과 Steam의 최초 종료 원인이 동일한지는 아직 확인하지 못했다.
- 18:58 재실행 시 Steam 본체 두 개가 동시에 기동되어 runtime launcher가
  반복 재시작했다. 게임을 소유한 본체를 보존하고 중복 본체에 SIGTERM을 보냈으나
  종료되지 않아, PID/실행 파일/게임 부모 관계를 재확인 후 중복 본체만 SIGKILL했다.
- 게임 RSS는 약 4.6GiB에서 6.4GiB까지 증가했다. 전체 가용 메모리는 약 1.6GiB까지
  감소했고 swap은 0이었다. Firefox/Codex/k3s 등에서 major page fault와 디스크 읽기가
  관측됐다. 시스템 HDD는 읽기 대기 약 51~74ms, 사용률 약 86~89%, 상위 LVM 장치는
  사용률 100%였다. I/O PSI some/full avg10이 약 88%/84%까지 상승했다.
- CPU 사용률도 짧게 포화됐으나 이후 낮아졌다. GPU 표본은 VRAM 약 5/6GiB,
  온도 54~56도, 사용률 2~44%로 GPU 과열/지속 포화를 뒷받침하지 않는다.
- user.slice의 memory.high/max는 무제한이며 oom/oom_kill 이벤트는 0이다.
  게임 시작 시 NVIDIA UVM 경로의 order-9 vmemmap 할당 실패 경고는 있었으나,
  이는 OOM 강제 종료의 증거가 아니며 종료와의 인과관계는 미확정이다.
- kubepods 메모리는 약 100MiB, memory.high 이벤트 0이었다. 게임 자원 서비스의
  8GiB soft threshold가 관측된 데스크톱 지연의 원인이라는 증거는 없다.

## 조치와 판단

- 데스크톱 응답 회복을 위해 현재 CS2 프로세스에만 SIGTERM을 보냈다.
  게임 종료 후 가용 메모리는 약 7.6GiB로 회복했다. 브라우저와 터미널은 종료하지 않았다.
- 종료 직후 디스크 읽기 대기는 잠시 지속됐으므로 메모리 회복을 완전 해결로 간주하지 않는다.
- 메모리 압박과 HDD 재읽기가 현재 동반 지연의 유력한 경로다. 최초 터미널/Steam 종료의
  근본 원인까지 확정한 것은 아니다. 중복 Steam은 최초 종료 이후 발생한 별도 문제다.
- 드라이버 교체, 재부팅, 세션 전환, 임의 캐시 삭제, swap 추가는 수행하지 않았다.
  swap 도입은 k3s의 swap 정책과 충돌 여부를 먼저 확인해야 한다.
- 다음 검증은 메모리 여유 확보 후 단일 Steam에서 재현하고 I/O·메모리 압박을 비교하는 것이다.
  FPS 상한만 낮추는 조치를 메모리 문제의 해결책으로 단정하지 않는다.
- 원본 로그·메모리 덤프·계정 식별자는 Git에 저장하지 않는다.

## 19:06 회복 확인

사용자가 전체 먹통을 추가 보고했다. 재실행된 Ptyxis도 19:01:31에 같은 화면 통신
오류로 종료했고 19:02:11 GNOME Shell 응답 불가 기록이 있어 재현으로 취급한다.
게임 종료 후 19:06에는 CS2 프로세스 없음, Steam 본체 1개, 가용 메모리 약 7GiB,
메모리 PSI avg10=0, CPU idle 약 88%, HDD 사용률 약 31%를 확인했다.
전원 프로필 balanced와 자원 서비스 inactive도 확인했다. 관측 지표는 회복했으나
사용자가 느끼는 화면 응답과 게임 재실행 안정성은 별도 확인이 필요하다.

## 19:11~19:17 추가 검증과 수정

### 실제 그래픽 설정의 불일치

실행 후 생성된 `cs2_video.txt`는 4x MSAA, CMAA2 비활성, 높은 텍스처/입자/음영
설정이었다. 사용자는 그래픽 옵션을 직접 변경하지 않았다고 확인했다.
최초 실행 전에 만든 부분 설정 파일이 게임 자동 감지 과정에서 대체된 것으로 추정한다.
초기 파일 적용 검증은 실제 게임 실행 후의 유지 검증을 대신하지 못했다.

`apply-cs2-profile.py`를 수정하여 게임이 생성한 Version 필드가 없는 경우 비디오
설정을 미루고 최초 실행 후 재적용하도록 안내한다. 기존 개인 설정을 비공개 로컬 백업하고
초기화된 설정 파일에 원래 의도한 MSAA=0, CMAA2=1을 재적용했다.
테스트 종료 후에도 두 값이 유지됐다. 다른 그래픽 품질과 FPS 상한은 비교를 위해 유지했다.

### 종료 감시를 둔 재현

[진단 도구](../gaming/watch-cs2-memory.py)는 실행 전 CS2가 없는지 확인하고,
같은 사용자·게임 실행 파일·PID 시작 시각이 일치하는 새 게임만 추적한다.
가용 메모리 2560MiB 미만, 또는 가용 메모리 4GiB 미만이면서 1초 구간 I/O full
대기가 30%를 넘으면 게임에 SIGTERM을 보내고 5초 후 잔존 프로세스만 SIGKILL한다.
측정 시간이 끝나도 해당 게임을 종료한다. 상시 게임 런처가 아닌 한시적 진단 도구다.
원본 JSONL은 `~/.local/state/cs2-setup/diagnostics/`에만 저장했다.

- Steam을 정상 종료하고 단일 본체로 재시작했다. 전체 세션 재부팅은 하지 않았다.
- 19:14:33~19:16:58 셰이더 사전 처리 중 여러 Fossilize 작업이 CPU를 사용했다.
  이 구간 가용 메모리는 대체로 5GiB 이상이었고 심한 지속 대기는 관측되지 않았다.
- `+map de_dust2 +bot_quota 0`으로 로컬 맵 실행을 요청했고 실제 게임 인자에서 확인했다.
- 19:17:07~19:17:15 게임 시작 후 약 8.1초 동안 가용 메모리 6837→2431MiB,
  게임 RSS 약 4.24GiB, RssAnon 약 2.93GiB까지 증가했다.
- 같은 구간 user.slice의 파일 workingset refault 카운터는 118471,
  direct scan 카운터는 280818 증가했다. 누적값이 아닌 동일 구간 차분이다.
  파일 재읽기와 직접 메모리 회수의 관측 증거이며, 모두 HDD에서 읽혔다고 단정하지 않는다.
- 메모리 여유 기준으로 감시 도구가 게임을 종료했다. 게임의 자발적 충돌이 아니다.
  관측 구간에 새 터미널 flush 오류나 GNOME 응답 불가 기록은 없었다.
- 전원 balanced, 자원 서비스 inactive 복귀 확인. MSAA 수정만으로 메모리 여유 문제를
  해소했다고 볼 수 없으며, 맵 진입 후 장시간 플레이 안정성은 아직 미검증이다.

### 터미널 종료와 시스템 메모리 정책

설치된 GTK 4.22.4의 [상위 프로젝트 코드](https://github.com/GNOME/gtk/blob/4.22.4/gdk/wayland/gdkeventsource.c#L150)는
Wayland flush가 실패하면 오류를 출력하고 `_exit(1)`한다. EAGAIN 예외 처리도 없다.
실제 Ptyxis 오류 문자열과 일치하므로 화면 통신의 일시적 막힘이 터미널 종료로 이어지는
경로가 확인된다. 무엇이 최초 통신 지연을 유발했는지까지 이 코드만으로 확정하지 않는다.
[동일 버전 계열의 유사 보고](https://bugzilla.redhat.com/show_bug.cgi?id=2477366)도 있지만
재현 조건이 다르므로 같은 근본 버그로 단정하지 않는다.

swap=0이고 systemd-oomd는 실행 중이나 사건 당시 종료 기록은 없었다.
[systemd 공식 설명](https://github.com/systemd/systemd/blob/main/man/systemd-oomd.service.xml)은
swap이 없으면 메모리 압박이 급격해져 대응이 늦을 수 있다고 설명한다.
사용자 권한으로 kubelet의 실제 swap 정책을 조회하지 못해 swap은 추가하지 않았다.
드라이버 Xid나 커널 OOM kill도 확인되지 않아 드라이버 교체를 정당화할 근거는 부족하다.

### 판단과 검증 범위

현재 증거는 게임 로딩의 메모리 증가와 파일 캐시 재읽기가 데스크톱 지연을 유발·악화하고,
GTK/Wayland의 오류 처리가 터미널 종료로 이어지는 복합 경로를 지지한다.
HDD가 유일한 원인이거나 OS SSD 이전이 반드시 필요하다는 결론은 아니다.
Windows 당시 페이지 파일·메모리 사용량·그래픽 설정은 확인되지 않아 직접 비교할 수 없다.

Python 구문 검사, 진단 도구의 PID 재사용/종료 경쟁 관련 안전 검사 4개,
실제 메모리 기준 종료, MSAA/CMAA2 값 유지 검증을 수행했다.
해결되지 않은 작업은 메모리 여유 확보 방안과 터미널 우회책의 검증,
그리고 맵 진입 후 실제 사용 안정성 확인이다. 이슈 #11은 열린 상태로 유지한다.

## 19:57~20:02 메모리 대응과 재실행 검증

사용자는 OS HDD 배치가 원인으로 확정됐는지 먼저 확인하도록 요청했고,
미확정임을 설명한 뒤 실질적인 문제 해결을 지시했다. OS 이전을 보류하고
SSD 스왑 8GiB를 추가했다. 호스트 정책의 원본·복구 절차는
[serverize 운영 문서](https://github.com/Jaeman-Lee/serverize/blob/fix/desktop-host-swap-20260927/docs/runbooks/desktop-host-swap.md)에 둔다.
K3s와 Pod는 스왑을 사용하지 않으며 재시작도 하지 않았다.

터미널에는 [사용자용 설치 도구](../gaming/apply-terminal-workaround.py)로
X11 실행 래퍼와 로컬 desktop override를 적용했다. 별도 application ID를 써서
기존 Wayland 터미널 프로세스는 유지한다. 새로운 아이콘 실행은 X11로 열린다.
DBusActivatable=false로 launcher가 래퍼를 거치도록 하고 창/탭/설정 action도 보존한다.
실제 X11 창과 약 48초 실행 후 정상 종료를 확인했다. 테스트 말미가 게임 로딩과 겹쳤다.
이 변경은 GTK의 Wayland 오류 경로를 우회하며 GTK 자체 수정은 아니다.

### 3분 로컬 맵 측정

이전과 같은 `+map de_dust2 +bot_quota 0`, MSAA=0/CMAA2=1로 요청했다.
실제 화면에서는 Dust II 맵과 봇 경기가 확인되어 봇 없는 부하라고 주장하지 않는다.
가용 메모리 2560MiB/I/O 대기 예방 종료 기준은 동일하게 유지했다.

| 항목 | 스왑 추가 후 관측 |
| --- | --- |
| 게임 측정 | 약 180초, 마지막 표본 179.2초 |
| 가용 메모리 최저 | 4244MiB, 약 4.14GiB |
| SSD 스왑 사용 최대 | 1953MiB, 약 1.91GiB |
| CS2 RSS 최대 | 5896MiB |
| I/O full PSI avg10 최대 / 종료 직전 | 8.27% / 0.40% |
| 메모리 full PSI avg10 최대 / 종료 직전 | 3.37% / 0.00% |
| 종료 이유 | 예정된 180초 만료; 충돌이나 예방 기준 초과 아님 |

Dust II 실제 화면에 HUD 평균 약 226FPS가 표시됐으나 단일 화면 값이므로
벤치마크나 최저 FPS 보장으로 사용하지 않는다. 테스트 구간 사용자 journal에는
새로운 terminal flush 오류, GNOME 응답 불가, Steam broken pipe/fatal assertion이 없었다.
게임 종료 후 balanced 및 자원 서비스 inactive 복귀, MSAA/CMAA2 유지도 확인했다.
K3s Ready, 시스템 Pod 재시작 0, Pod 부모 cgroup swap 사용 0을 확인했다.

스왑 추가 후 이전 예방 종료 구간을 지나 맵 실행을 유지한 것은 실제 개선의 증거다.
다만 실행 전 가용 메모리, 캐시와 다른 앱 상태가 달라 엄밀한 단일 변수 A/B 실험은 아니다.
HDD를 OS의 최초 고장 원인으로 확정하거나, 모든 종료 원인을 해결했다고 주장하지 않는다.
장시간 온라인 플레이와 재부팅 후 상태는 미검증이다. 이슈 #11은 이 확인을 위해 유지한다.
원본 JSONL과 게임 창 캡처는 비공개 로컬 진단 폴더에만 보관했다.

### 터미널 우회 복구

이번 설치 백업은 `~/.local/state/cs2-setup/backups/*-terminal/`에 있다.
기존 파일이 있었다면 백업의 동명 파일을 원래 위치에 복원한다. 새로 만든 파일은
`new-files.txt`와 대조해 `~/.local/bin/ptyxis-x11` 및
`~/.local/share/applications/org.gnome.Ptyxis.desktop`만 제거하고
`update-desktop-database ~/.local/share/applications`를 실행하면 시스템 런처로 돌아간다.
기존 창을 종료할 필요는 없다. `ptyxis` 명령 직접 실행은 이 아이콘용 우회를 거치지 않는다.
