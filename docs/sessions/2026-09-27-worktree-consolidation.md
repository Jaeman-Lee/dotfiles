---
title: 기본 프로젝트 폴더로 worktree 통합
date: 2026-09-27
tags: [git, operations, verification]
---

# 기본 폴더 통합

- 사용자 결정: worktree 변경을 기본 github 폴더로 모으고 별도 checkout을 정리한다.
- 작업 상태: https://github.com/Jaeman-Lee/dotfiles/issues/18
- 작업 브랜치: `chore/consolidate-worktrees-20260927`.
- 시작 HEAD: `f1a90a1edf5326d81d931de0e62dc676344dad2b`; 시작 브랜치: `chore/git-first-instructions-20260925`.
- 실행 위치: pc / Linux. 지정 Obsidian Vault 연결 미설정. 이 Markdown이 결과 원본이다.

## 반영

아래 HEAD를 기본 폴더의 통합 작업 브랜치에 병합했다. 모든 HEAD의 조상 관계와 원래 브랜치 보존을 확인한 뒤
`git worktree remove`로 별도 checkout만 제거했다. main/master 직접 병합이나 원격 force push는 수행하지 않았다.

| 제거한 checkout | 보존·통합한 HEAD |
|---|---|
| `dotfiles-cs2` | `efe1266d1fea21041cd0627f859b86b38bb5945c` |
| `dotfiles-hdd-records` | `a025dbc28cce2b5e34cb25550b5d85bea9aa5fd0` |
| `dotfiles-remote-awake` | `d460fdcbb834319c41f2d964efd3647b621f533f` |
| `dotfiles-ssd` | `1baddc0140313362b4f09ebe266468bdf16d6db2` |
| `dotfiles-web-desktop` | `040af28b5b9968b2abbd73f1c6ed4fdbc911c25e` |

## 검증

격리 Git workflow 테스트 3개와 gaming 테스트 8개 통과. remote-desktop에는 unittest 파일이 없어 추가 실행은 0개였으며 성공 테스트 수에 포함하지 않는다. 통합 도중 추가된 모바일 입력 커밋 040af28도 별도로 병합했다. Python/JS 구문을 확인한다.

Git에서 제외된 생성 파일은 HDD의 `~/.local/state/worktree-consolidation-20260927/preserved-artifacts/`에 복사하고 SHA256을 확인했다.
재생성 가능한 node_modules를 제외한 파일과 기존 사용자 변경을 보존했다. 개인 원문·환경 값·스크린샷·실행 로그는 Git에 넣지 않았다.


## 검토 링크

- Draft PR: https://github.com/Jaeman-Lee/dotfiles/pull/19
- 기록 커밋: https://github.com/Jaeman-Lee/dotfiles/commit/e7a0df9f77b3fbe8bdb424b377d6730f1a278f76

통합 후 다른 작업에서 추가한 remote-desktop 변경과 커밋은 보존했다. 이번 기록 커밋은 해당 변경을 다시 수정하거나 별도 커밋으로 복사하지 않는다.
