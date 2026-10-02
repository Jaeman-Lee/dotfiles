---
title: CS2 donk 조준점·레이더 적용
date: 2026-10-02
tags: [gaming, cs2, settings]
---

# CS2 donk 조준점·레이더 적용

Vault 연결 미설정. 이 문서가 현재 선택의 운영 원본이다.
진행 상태: [Issue #28](https://github.com/Jaeman-Lee/dotfiles/issues/28).
변경 검토: [PR #29](https://github.com/Jaeman-Lee/dotfiles/pull/29).
설정 원본: [workstation.cfg](../gaming/workstation.cfg).
이전 선택과 적용 장애 기록: [기존 커스텀 기록](cs2-competitive-custom-20261002.md).

## 사용자 선택과 출처

사용자는 앞선 임의 조합을 선호하지 않아 상위권 선수 설정을 요청한 뒤 donk를 선택했다.
이전 조합을 가장 보편적인 설정으로 볼 근거는 없다.
[ProSettings donk 페이지](https://prosettings.net/players/donk/)의 2026-10-01 갱신
등록값을 2026-10-02 확인했다. 선수의 설정은 수시로 바뀌므로 현재 순간의 직접
관측값이나 사용 빈도 통계로 표현하지 않는다.

| 항목 | 적용값 |
| --- | --- |
| 조준점 | Static Cross(4), 초록 RGB 0/255/0, 불투명 |
| 크기 | 길이 2, 두께 2, 간격 0 |
| 보조 | 테두리·중앙 점·반동 추적·T자 끔, 스나이퍼 폭 0 |
| 레이더 | 배율 0.7, 플레이어 중앙 고정 켬, 회전 켬 |
| 레이더 HUD | 크기 1, 스코어보드와 모양 전환 켬 |
| 무기 표시 | FOV 68, X 2.5 / Y 0 / Z -1.5 (기존과 같음) |

donk의 등록 해상도는 1280×960 늘림, 조준점 기준 높이는 960이다.
이 PC는 1920×1080과 기준 높이 1080을 유지하고 2px 길이/두께를 적용한다.
따라서 **donk의 조준점·레이더를 FHD에 적용한 프로필**이며 4:3 화면의 모양까지
완전히 동일하게 복제한 것은 아니다. 감도 3.59·DPI·키/마우스 축·성능 설정은
그대로 유지한다. 음향은 기존 사용자 프로필이며 donk 설정으로 주장하지 않는다.

## 적용 및 복구

실행 중에는 콘솔에서 `exec workstation; host_writeconfig`로 적용할 수 있다.
다음 적용부터 재실행이 필수가 되지 않도록 `con_enable 1`을 추가했다.
기본 콘솔 키는 Esc 아래 백틱/물결 키이며 기존 키 바인딩은 변경하지 않는다.
설정 파일 설치만으로 진행 중인 경기의 설정이 바뀌지는 않는다.

사용자가 경기 중임을 알린 동안은 종료하지 않았다. 이어 경기 종료를 알린 후,
기존 재실행 승인에 따라 CS2에 종료 요청을 보내고 Steam으로 다시 실행했다.
Steam·OS 재시작이나 SIGKILL은 사용하지 않는다.

변경 직전 cfg와 개인 저장 설정은 HDD의
`~/.local/state/cs2-setup/backups/donk-20261002-192357/`에 보관하며 Git에서 제외한다.
복구는 `user-workstation.cfg`를 `~/.config/cs2/workstation.cfg`로,
`game-workstation.cfg`를 게임 `game/csgo/cfg/workstation.cfg`로 복원한 뒤
콘솔에서 `exec workstation`을 실행한다.

## 검증

- 원본과 두 설치본의 바이트 일치, `git diff --check` 통과.
- 재실행 PID 17205에서 `+exec workstation.cfg +host_writeconfig` 확인.
- 게임이 직접 저장한 설정을 숫자/불리언 정규화 후 비교하여 프로필 convar
  **41개 전체 일치** 확인. 개인 vcfg에 원하는 값을 직접 써 넣지 않았다.
- 조준점 2/2/0, 테두리 0, 스나이퍼 폭 0, 레이더 0.7/중앙 고정/HUD 1,
  개발자 콘솔 켬을 확인했다.
- 감도 3.59, 전체 키/마우스 축, 기존 미커밋 런처 패치 보존 확인.
- 사용자 화면/조작감 평가는 별도다.
