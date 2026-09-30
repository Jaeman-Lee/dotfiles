# Ptyxis 아이콘 실행 실패 수정 — 2026-09-30

Vault 연결 미설정. 이 문서가 운영 원본이다.
진행 상태: [Issue #24](https://github.com/Jaeman-Lee/dotfiles/issues/24).

## 원인과 변경

사용자 X11 wrapper가 `--gapplication-app-id`를 전달하면서 현재 설치된 Ptyxis에서
`Unknown option`으로 종료됐다. 로컬 `ptyxis --help`로 지원 여부를 확인하고,
독립 실행을 위한 공식 CLI 옵션 `--standalone`으로 교체했다.
`GDK_BACKEND=x11`을 유지하며 기존 터미널 인스턴스는 종료하지 않는다.

`python3 gaming/apply-terminal-workaround.py`로 사용자 wrapper와 desktop override를 적용했다.
변경 전 파일은 `~/.local/state/cs2-setup/backups/20260930-215741-terminal/`에 보존했다.

## 검증

- `bash -n gaming/ptyxis-x11` 통과.
- 설치된 wrapper의 `--help` 정상 출력, 지원하지 않는 옵션 오류 없음.
- 실제 X11 터미널에서 Python 명령 실행 및 로컬 완료 표식 생성 확인, GUI 프로세스 종료 코드 0.
- 검증 표식은 `~/.local/state/os-ssd-migration/20260930/`에 두고 Git에는 포함하지 않는다.

이는 터미널 실행 오류의 수정 결과다. PC 전체 지연, 스왑 압박, OS SSD 이전 완료를 뜻하지 않는다.
아이콘·키보드 단축키 사용에 대한 사용자 확인은 별도다.

## 복구

위 백업의 `ptyxis-x11`과 `org.gnome.Ptyxis.desktop`을 각각 기존 사용자 경로로 복원하고
`update-desktop-database ~/.local/share/applications`를 실행한다.
복원하면 지원하지 않는 옵션도 돌아오므로 장애 재현이 필요할 때만 사용한다.
