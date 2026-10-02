---
title: CS2 무난한 경쟁전 커스텀
date: 2026-10-02
tags: [gaming, cs2, settings]
---

# CS2 무난한 경쟁전 커스텀

Vault 연결 미설정. 이 문서가 운영 원본이다.
요구사항·진행 상태: [Issue #28](https://github.com/Jaeman-Lee/dotfiles/issues/28).
변경 검토: [draft PR #29](https://github.com/Jaeman-Lee/dotfiles/pull/29).
구현: [71b3192](https://github.com/Jaeman-Lee/dotfiles/commit/71b3192).
설정 원본: [workstation.cfg](../gaming/workstation.cfg).

사용자가 플레이 중 커스텀을 요청하고 “무난한 경쟁전 설정”을 선택했다.
작은 고정 십자와 넓은 레이더를 출발점으로 구성한다. 특정 프로 선수의 정확한
현재 설정을 복제하거나 성능 향상을 보장하는 프로필은 아니다.

## 설정과 이유

| 항목 | 값 | 목적 |
| --- | --- | --- |
| 조준점 | 고정 십자(style 4), 초록 RGB 0/255/0, 불투명 | 배경과 구분하기 쉬운 출발점 |
| 조준점 크기 | FHD 기준 길이 6px, 두께 1px, 간격 3px | 중심을 가리지 않는 작은 십자 |
| 조준점 보조 | 검정 전체 테두리, 중앙 점·T자·반동 추적 끔 | 밝은 배경에서 가독성 보완 |
| 레이더 | 배율 0.4, 중앙 고정 끔, 회전 켬, 동적 배율 끔 | 더 넓은 맵 정보 표시 |
| 레이더 크기 | HUD 1.1, 최소 아이콘 0.7 | 축소된 맵에서도 팀원 구분 |
| 무기 표시 | FOV 68, X 2.5 / Y 0 / Z -1.5 | 화면 중앙 가림을 줄이는 출발점 |
| 적 대비 | r_player_visibility_mode 1 | 기존 대비 강화 유지 |
| 경쟁전 음악 | 사망·MVP·라운드 종료 0, 생존 중 MVP 음소거 | 전투 외 음악 감소 |
| 폭탄 10초 경고 | 기존 엔진 값 0.04 유지 | 시간 정보 유지 |

무기 표시 FOV는 월드 시야각이나 감도를 변경하지 않는다. 감도·줌 감도·DPI,
키보드·마우스 축 바인딩, 효과음·음성·전체 음량, 해상도·FPS·그래픽 설정은
이 변경에서 수정하지 않는다. 모드별 음악 변수가 분리되어 있어 음악 변경은
기본 경쟁전 채널을 대상으로 한다. 다른 모드 전용 음악 값은 유지한다.

## 현재 게임에 적용

1. 게임 설정 → 게임 → 개발자 콘솔 사용 → 예.
2. 기본 콘솔 키인 백틱/물결(`~`, Esc 아래)을 누른다. 열리지 않으면
   키보드/마우스 설정에서 콘솔 열기 키를 지정한다.
3. 콘솔에 `exec workstation`을 입력하고 콘솔을 닫는다.

설치된 실행 래퍼가 다음 시작 시 같은 설정을 자동으로 읽는다.
게임과 Steam을 종료하거나 포커스를 빼앗는 자동 키 입력은 수행하지 않았다.
실행 중 cfg 파일 교체는 메모리의 설정을 자동으로 변경하지 않는다.

## 백업과 되돌리기

개인 백업은 HDD의 `~/.local/state/cs2-setup/backups/competitive-20261002-191409/`에
0700 디렉터리/0600 파일로 보관한다. 기존 사용자·게임 `workstation.cfg`,
저장된 convars·키 설정, 이 작업과 별개인 미커밋 런처 패치가 포함된다.
개인 설정 원본은 Git에 넣지 않는다.

현재 세션에서 변경한 값만 되돌리려면 콘솔에서 `exec cs2-before-custom`을 실행한다.
이 파일은 변경 직전 **디스크에 저장된 값**으로 만들었으며, 저장되지 않은
실행 중 설정까지 캡처한 것으로 보지 않는다. 다음 시작도 복구하려면 백업의
`user-workstation.cfg`를 `~/.config/cs2/workstation.cfg`로 복원하고,
`game-workstation.cfg`를 게임 `game/csgo/cfg/workstation.cfg`로 복원한다.
실행 중 Steam Cloud나 사용자 vcfg 전체를 덮어쓰지 않는다.

## 검증 결과와 한계

- 변경한 31개 변수 이름이 설치된 게임의 `libclient.so` 문자열과 실제 저장된
  설정 모두에 존재함을 확인했다. 이름 존재 확인은 런타임 값 검증과 다르다.
- 구형 `cl_crosshairsize`, `cl_crosshairthickness`, `cl_crosshairgap`,
  `cl_crosshaircolor`, `cl_crosshairusealpha`, `cl_crosshairalpha` 사용을 제거하고
  현재 픽셀 단위 및 RGBA 변수를 사용한다.
- 기존 모든 `bind` 줄 일치, 감도 강제 명령 없음 확인.
- 저장소 원본과 사용자 설정·게임 cfg 두 설치본의 바이트 일치 확인.
- `git diff --check`, 저장소 Git workflow 테스트 3개 통과.
- 선언된 인터프리터 기준 Python/셸 구문 검사 통과. 기존 CI의 일괄 `sh -n`은
  이번 변경 이전부터 Bash 배열을 사용하는 `gaming/install-steam-system.sh`에서
  실패한다. 최초 커밋의 “syntax checks passed”는 이 인터프리터 구분 검사 결과로
  한정하며, 기존 CI 전체가 통과했다는 의미가 아니다. CI 수정은 이 작업 범위에
  포함하지 않았으며 PR에 기존 실패 원인을 명시했다.
- 실제 경기 화면, 콘솔 실행 및 런타임 값은 아직 확인하지 않았다.
  설치 완료와 플레이 중 적용 완료를 구분한다.

## 근거

[Valve 공식 변경 기록](https://steamcommunity.com/app/730/announcements/)의
2026-09-22~30 업데이트에서 조준점 개편, 픽셀 단위 길이·두께·간격,
해상도 변경 시 재조정, 테두리 색상, 모드별 음악 설정을 확인했다.
명령 이름은 로컬 게임 바이너리와 게임이 저장한 설정을 기준으로 검증했다.
숫자는 사용자용 초기 선택값이며 Valve의 권장값이나 인기 순위로 표현하지 않는다.

기존 근거와 장비·성능 관측은 [실전 관측 기록](cs2-live-session-20260927.md),
설치 구조는 [게임 프로필 운영 문서](cs2-gaming-profile.md)를 참조한다.
