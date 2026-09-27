---
title: Ubuntu 게임 설정 세션 마감
date: 2026-09-27
tags: [session, gaming, cs2, closeout]
---

# 세션 마감

사용자 요청으로 게임 설정·문제 해결·실전 관측 작업을 여기서 마감한다.
AMD GPU/LLM 업그레이드 검토는 별도 폴더와 새 세션으로 인계한다.
Vault 연결 미설정. 이 문서가 Git 관리 원본이며
`/mnt/dev-ssd/games/SESSION.md`는 이 문서로 연결되는 로컬 심볼릭 링크다.
연결 재현: `gaming/link-session-note.sh`.

## 완료한 작업과 현재 설정

- Steam과 Linux 게임 실행 환경을 SSD에 준비하고 CS2 실행을 확인했다.
- FHD 전체 화면, 120Hz, CMAA2/MSAA 끔, VSync 끔, 게임 240FPS·메뉴 60FPS 상한.
- GameMode/전원 성능 프로필 및 게임 중 k3s 자원 우선순위 조정과 종료 시 복구.
- 게임 내 프레임 시간·FPS·핑·네트워크 상태 표시, 입력·조준점 기본 설정.
- 초기 자동 감지에 덮어써진 MSAA 설정은 게임 초기화 후 적용하도록 수정했다.
- 실전에서 사용자 메뉴 감도 2.56과 정상 조작감을 확인했다. 시작 cfg의 예전
  감도 1.0 강제를 제거하여 게임 메뉴 값을 보존한다. 마우스 DPI는 미확인이다.
- 호스트 SSD 스왑 8GiB 적용. K3s/Pod의 스왑은 금지하고 서비스 재시작 없이 검증했다.
- 새 터미널 아이콘 실행에 X11 우회를 적용해 관측된 GTK/Wayland flush 종료 경로를 피한다.

## 문제 해결에 대한 결론

메모리 압박·파일 재읽기·HDD 대기와 화면 통신 오류가 관측됐다.
OS가 HDD에 있는 것이 최초 원인이라고 판명된 것은 아니다.
OS·파티션·부팅 구성을 바꾸지 않고 스왑 추가 및 터미널 우회 후 개선을 확인했다.
사용자는 로컬 맵 테스트 및 실전에서 PC 정상 반응과 끊김 없는 조작을 확인했다.

- 예방 감시를 둔 로컬 맵 180초: 가용 RAM 최저 4244MiB, 스왑 최대 1953MiB.
  압박 기준이 아닌 예정된 시간 만료로 테스트 게임을 종료했다.
- 사용자 실전 관측: 245초, 5초 간격 자원 표본 50개, HUD 5장.
  첫 세 HUD는 195/195/208FPS, Max 7.5/8.1/7.5ms, 핑 43ms, tick miss 0.0%.
  나머지 두 장은 메뉴다. 전체 경기 평균이나 1% low로 해석하지 않는다.
- 확인된 게임 화면 120초에서 가용 RAM 최저 5435MiB, GPU 최고 98%/70°C,
  메모리 full PSI avg10 최대 0.00%, I/O full 최대 0.46%.
- 실전 모니터는 사용자 종료 알림 후 중지했다. 게임 종료 이벤트 감지 추가는
  사용자가 취소했으며 GSI 설정이나 수신 서비스를 설치하지 않았다.

## 적용하지 않은 제안과 검증 한계

FPS 200, 낮은 파티클/AO 끄기, 레이더 0.4·중앙 고정 끄기·HUD 1.1,
라운드 종료/MVP 음악 최소화는 다음 비교용 제안으로만 남긴다.
현재 게임 FPS 상한은 240이며 이 제안들은 적용하지 않았다.
장시간·다른 맵·재부팅 후 안정성은 미검증이고 이번 마감 범위 밖이다.
OS SSD 이전은 보류한다. 향후 실행하려면 별도 백업·복구·디스크 작업 계획이 필요하다.

## 원본과 검토 기록

- [설정 및 복구](https://github.com/Jaeman-Lee/dotfiles/blob/feat/cs2-ubuntu-20260927/docs/cs2-gaming-profile.md)
- [먹통·종료 조사와 대응](https://github.com/Jaeman-Lee/dotfiles/blob/feat/cs2-ubuntu-20260927/docs/cs2-desktop-stability-20260927.md)
- [실전 관측과 개인 설정 제안](https://github.com/Jaeman-Lee/dotfiles/blob/feat/cs2-ubuntu-20260927/docs/cs2-live-session-20260927.md)
- [호스트 스왑 운영·복구 원본](https://github.com/Jaeman-Lee/serverize/blob/fix/desktop-host-swap-20260927/docs/runbooks/desktop-host-swap.md)
- 실행 범위 완료로 마감: [dotfiles #11](https://github.com/Jaeman-Lee/dotfiles/issues/11),
  [dotfiles #13](https://github.com/Jaeman-Lee/dotfiles/issues/13),
  [serverize #8](https://github.com/Jaeman-Lee/serverize/issues/8).
- 검토용 draft PR 유지: [dotfiles #12](https://github.com/Jaeman-Lee/dotfiles/pull/12),
  [serverize #10](https://github.com/Jaeman-Lee/serverize/pull/10). main 병합은 하지 않았다.
- 주요 구현: [게임 감도·관측 b0adf4c](https://github.com/Jaeman-Lee/dotfiles/commit/b0adf4c),
  [터미널 de07b27](https://github.com/Jaeman-Lee/dotfiles/commit/de07b27),
  [스왑 04f0bc8](https://github.com/Jaeman-Lee/serverize/commit/04f0bc8).

개인 백업과 원본 측정값은 `~/.local/state/cs2-setup/`, 시스템 스왑 백업은
`/var/lib/serverize-host-swap/backups/`에 보존한다. Git에는 개인 원본을 넣지 않는다.

## 새 세션 인계

새 작업 폴더: `/mnt/dev-ssd/worktrees/serverize-amd-gpu`.
시작 문서: 새 폴더의 `SESSION.md`.
작업 상태: [AMD GPU 검토 이슈 #12](https://github.com/Jaeman-Lee/serverize/issues/12).
요청은 Linux 게임과 LLM 서빙을 함께 고려한 AMD GPU 업그레이드 추천이며,
예산·목표 모델·전원/케이스 및 최신 공식 지원 정보를 다음 세션에서 확인한다.
