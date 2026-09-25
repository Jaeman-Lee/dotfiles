---
title: Obsidian 기반 문서화와 Git 작업 기록
date: 2026-09-25
tags: [workflow, obsidian, git, decision]
---

# Obsidian 기반 문서화와 Git 작업 기록

사용자는 전역 Codex 지침에 “모든 문서화, 프로젝트 등의 기록은 Obsidian을 기반으로 작성”을
추가하되, 반영 전에 효율성을 판단하도록 요청했다.

## 판단과 결정

여러 프로젝트의 개요·결정·조사·작업 배경을 Markdown 노트와 링크로 모으는 방식은 적합하다.
기존 Git 원칙과 결합하되, 동일 본문과 진행 상태를 이중 관리하지 않는 것을 조건으로 채택한다.

| 대상 | 원본과 작성 방식 |
|---|---|
| 프로젝트 개요·설계·결정·조사·작업 기록 | 지정된 Obsidian Vault의 Markdown, Git 버전 관리 |
| README·AGENTS.md·API 명세·운영 문서 | 코드 저장소에 원본 유지, Obsidian에서 링크 |
| 할 일·진행 상태 | GitHub Issues, 노트에는 배경과 링크 |
| 코드 변경·검토 | Git 커밋·PR, 노트에는 결과 요약과 링크 |

현재 경로에서 `fin-advisor/obsidian`, `furiosa-study`의 `.obsidian` 폴더를 확인했다.
확인한 기본 Linux Obsidian 설정 경로에는 Vault 등록 파일이 없었다. 이는 다른 경로의 Vault가
없다는 뜻은 아니다. 공통 Vault 경로를 확정할 근거가 없으므로 기존 Vault를 임의로 확장하거나
문서를 일괄 이동하지 않는다. 이 문서는 dotfiles의 Git 문서 위치에 기록하며 **Vault 연결 미설정**이다.

전역 규칙은 [codex/AGENTS.md](../../codex/AGENTS.md)에 반영하고, 기존 전역 지침과의 차이를
확인한 뒤 로컬 사본에 동일 변경을 설치한다. 계정 메모리를 변경하는 작업은 아니다.

## 근거

- [Obsidian의 저장 방식](https://obsidian.md/help/Files%2Band%2Bfolders/How%2BObsidian%2Bstores%2Bdata): Vault는 로컬 폴더이고 노트는 Markdown 텍스트 파일이다.
- [Obsidian 내부 링크](https://obsidian.md/help/Linking%2Bnotes%2Band%2Bfiles/Internal%2Blinks): 표준 Markdown 링크를 지원하며, 호환성이 중요하면 이를 사용할 수 있다.
- 로컬 `claude-vault-skill/README.md`: 기존 Markdown Vault 검색 도구가 있으나 Codex 공통 연결이 설치된 것은 확인하지 않았다.

Obsidian 앱 실행이나 플러그인 설치를 문서 작성의 필수 조건으로 만들지 않는다.
