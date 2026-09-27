# 실행 데이터와 기록의 저장 위치

2026-09-27 사용자 결정에 따라 실행 데이터는 SSD, 기록·보관물·패키지 다운로드 캐시는 HDD에 둡니다.
지정된 Obsidian Vault 연결은 미설정입니다.

정책·실제 이동 결과의 원본은 [serverize 운영 문서](https://github.com/Jaeman-Lee/serverize/blob/chore/hdd-records-20260927/docs/runbooks/storage-placement.md)입니다.
작업 상태: [Issue #15](https://github.com/Jaeman-Lee/dotfiles/issues/15).

```bash
sh storage/use-hdd-records.sh
```

이 스크립트는 npm/pip/uv의 이후 실행에 사용할 캐시 경로를 `$HOME/.cache/dev-packages/`로 설정합니다.
사용자 environment.d 파일과 npm의 cache 키, systemd 사용자 관리자 환경을 갱신합니다.
기존 프로세스를 종료하거나 그 프로세스의 환경을 바꾸지 않습니다.
기존 SSD 경로의 파일 이동은 serverize의 별도 checksum 검증 도구가 수행합니다.

`use-ssd.sh`는 호환 진입점이며 같은 HDD 설정을 실행합니다. SSD 캐시 설정을 다시 적용하지 않습니다.
`prepare-ssd.sh`는 과거 초기 설치용 스크립트입니다. 이번 작업에서 실행·변경하지 않습니다.
현재 배치를 조정하기 위해 디스크를 다시 포맷하거나 초기화할 필요가 없습니다.

로컬 지속 지침 원본은 [codex/AGENTS.md](../codex/AGENTS.md)입니다.
검증: 두 설정 스크립트의 shellcheck, 실제 npm cache 조회와 systemd 사용자 환경 조회 통과.
