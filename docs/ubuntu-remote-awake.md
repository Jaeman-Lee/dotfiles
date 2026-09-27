# Ubuntu 원격 사용 중 자동 잠금·절전 방지

사용자 요청: 2026-09-25, issue #1. GNOME 사용자 설정에 즉시 적용.

```bash
python3 scripts/ubuntu-remote-awake.py apply
python3 scripts/ubuntu-remote-awake.py status
# 이전 값으로 복구
python3 scripts/ubuntu-remote-awake.py restore
```

sudo 없이 로그인한 사용자로 실행한다. 최초 설정값은 `$XDG_STATE_HOME/dotfiles/ubuntu-remote-awake.json`(기본 `~/.local/state`)에 0600으로 저장하며 Git에 넣지 않는다. 재실행 시 최초 백업을 덮어쓰지 않는다.

| 설정 | 변경 전 관측 | 적용 값 |
|---|---|---|
| 화면 유휴 시간 | 300초 | 0 (자동 화면 꺼짐 없음) |
| 화면 잠금 | true | false |
| AC 자동 절전 종류 | suspend | nothing |
| AC 절전 타이머 | 0 | 0 |
| 유휴 화면 어두워짐 | true | false |

검증: 적용 명령 exit 0 및 gsettings 실제 값 재조회 일치. Tailscale/Codex Pocket active, 사용자 linger yes 확인. SSH/로그인 인증과 배터리 전원 설정, 시스템 sleep targets는 수정하지 않았다.

제한: 전원 차단/수동 절전/재부팅/네트워크 장애를 방지하는 설정이 아니다. 자동 화면 잠금이 꺼지므로 PC 앞의 사람은 로그인된 화면을 사용할 수 있다. 장시간 유휴 및 변경 후 재부팅 유지 여부는 별도 실측 대상이다.
