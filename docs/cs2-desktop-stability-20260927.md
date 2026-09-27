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
