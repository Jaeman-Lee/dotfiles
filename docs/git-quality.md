---
title: Git 품질 기준과 저장 장치 배치
date: 2026-09-25
tags: [git, operations, storage]
---

# Git 품질 기준

Vault 연결 미설정. Git 원본은 이 저장소이며 Obsidian 프로젝트 노트에서 연결한다.

핵심 검증 대상은 dotfiles, personal-agent-system, agent-company, codex-pocket-voice다.
원본 작업 트리와 미커밋 변경을 보존하고 별도 worktree/작업 브랜치에서 변경한다.

## 공통 기준

- `git/workflow.inc`: fast-forward-only pull, fetch 시 사라진 원격 참조 정리, 첫 push 추적 설정,
  zdiff3 충돌 표시, rerere 재사용(자동 stage 비활성).
- `git/install.py --root PATH`: 기존 전역 설정을 지우지 않고 include 추가.
  기존 hooksPath/pre-push가 있으면 보존하고 설치를 건너뛴다.
- 기본 브랜치 직접 push/deletion은 로컬 pre-push에서 차단한다. 이는 서버 규칙을 대체하지 않으며
  `--no-verify`나 다른 clone에는 강제되지 않는다.
- 공유 Actions는 full commit SHA로 고정한다. read-only permissions, checkout credential 비보존,
  Gitleaks 바이너리 SHA-256 검증을 사용한다. fork 코드를 privileged 이벤트에서 실행하지 않는다.
- PR/기본 브랜치 push에서는 새 커밋 범위의 비밀정보와 whitespace를 검사한다.
  수동 workflow_dispatch와 별도 초기 감사는 전체 이력을 검사한다. PR 통과가 과거 이력의 무결성을 뜻하지 않는다.
- 기존 비밀정보는 값을 출력하거나 Git에 보고서를 넣지 않는다. 실제 키라면 먼저 폐기/교체하고
  이력 정리는 별도로 결정한다. 테스트 fixture는 근거를 확인한 경우에만 좁은 예외로 처리한다.
- 공개 저장소는 검증된 검사 이름으로 기본 브랜치를 보호한다. 비공개 저장소의 요금제 제한은
  실패로 기록하며 공개 전환·과금 변경으로 우회하지 않는다.

## 완료와 확장

공통 검사와 핵심 프로젝트 테스트를 통과한 뒤 나머지 저장소에 SHA 고정 호출 workflow를 적용한다.
기존 CI·문서·ignore 규칙은 보존한다. 변경은 draft PR로 제공하며 기본 브랜치에 직접 push/merge하지 않는다.
워크플로의 기본 브랜치 적용은 PR 병합 후다. 보호 규칙·로컬 Git 설정은 별도 적용 상태를 기록한다.

## SSD/HDD

현장 관측: OS와 현재 저장소는 HDD의 100GiB LVM/ext4 볼륨에 있으며 여유 약 76GiB.
Samsung SSD 980 500GB는 NTFS 파티션 상태로 미마운트다. 사용자는 기존 SSD 데이터가 필요 없다고 답했다.

- SSD: 활성 저장소/임시 worktree, npm/pip/build cache. Linux 개발용 ext4 파일시스템으로 준비한 뒤 사용한다.
- HDD: Git bundle·운영 상태 백업, 완료 산출물·보관 자료. 현재 LV에 충분한 여유가 있어 즉시 확장하지 않는다.
- 장치 준비 전에는 HDD에 있는 원본을 이동하지 않는다. 일회성 소형 검사 도구와 redacted 보고서는
  RAM 기반 /tmp를 사용하며 영구 백업으로 간주하지 않는다.
- 이동 시 실행 중인 프로세스를 확인하고 경로 설정·worktree 메타데이터·복구 검증을 함께 처리한다.
  단순 폴더 이동으로 실행 중 서비스와 Git worktree를 끊지 않는다.

근거: [Git 설정](https://git-scm.com/docs/git-config),
[Actions 보안](https://docs.github.com/en/actions/reference/security/secure-use),
[비밀정보 처리](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository).

## 여러 저장소의 현재 상태

`python3 git/portfolio.py --root /path/to/repositories`는 브랜치·HEAD·기준 커밋,
미커밋 개수·upstream 대비 ahead/behind·worktree 개수를 JSON으로 출력한다.
원문이나 파일 내용은 읽지 않으며 fetch도 하지 않는다. 원격 비교는 마지막 fetch 기준이다.
upstream이 없으면 ahead/behind를 0으로 오인하지 않도록 null로 표시한다.
임시 worktree는 PR 병합/종료, 미커밋 없음, 필요한 커밋의 원격 보존을 확인한 뒤 정리한다.
강제 worktree 삭제와 실행 중인 작업 폴더 정리는 자동화하지 않는다.

## SSD 준비 실행

관리자 인증이 필요한 현장 작업이다. 다음 명령은 확인된 SSD 전체를 초기화한다.
장치 식별·운영체제·마운트 검사에 실패하면 중단하며 자동 재시도하지 않는다.

```sh
sudo sh storage/prepare-ssd.sh --erase-confirmed-ssd
sh storage/use-ssd.sh
```

첫 명령 완료 후 `/mnt/dev-ssd/worktrees`를 새 작업의 위치로 사용한다.
두 번째 명령은 새 로그인 세션의 npm/pip/uv 캐시 경로를 설정한다.
기존 서비스·작업 트리·캐시는 실행 상태를 확인한 별도 이동 절차가 필요하다.
