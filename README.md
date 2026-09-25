# dotfiles

개인 개발 환경 설정 및 재사용 라이브러리 모음.

## Codex 공통 작업 원칙

[Git 기준 작업 지침](codex/AGENTS.md)은 2026-09-25 사용자 결정의 원본이다.
Codex 전역 지침으로 설치하려면 `sh codex/install.sh`를 실행한다.
브랜치 전환에도 유지되도록 `~/.codex/AGENTS.md`에 사본을 설치한다.
기존 내용이 다르면 덮어쓰지 않고 중지한다. 계정 메모리와는 별개인 로컬 지속 설정이다.

## 빠른 시작

```bash
git clone https://github.com/Jaeman-Lee/dotfiles.git
cd dotfiles
bash setup.sh
```

## 구조

```
dotfiles/
├── setup.sh                      # 환경 세팅 자동화
├── claude/
│   └── settings.json.template    # Claude Code MCP 설정 템플릿
└── lib/
    └── notion/
        ├── __init__.py
        └── notion_utils.py       # Notion API 유틸리티
```

## setup.sh 가 하는 것

| 단계 | 내용 |
|---|---|
| 1 | nvm 설치 + Node.js 20 설치 |
| 2 | notion-mcp-server 글로벌 설치 |
| 3 | `~/.claude/settings.json` 템플릿 복사 |

설치 후 `~/.claude/settings.json` 에서 토큰 직접 입력 필요.

## lib/notion

Notion API를 Python으로 쉽게 다루는 유틸리티.

### 사용법

```python
import sys
sys.path.insert(0, "/path/to/dotfiles")

from lib.notion import NotionClient, blocks

client = NotionClient(token="your_notion_token")

# 페이지 생성
page = client.create_page(
    parent_id="your_database_id",
    parent_type="database",
    title="새 페이지",
    properties={
        "상태": {"status": {"name": "진행 중"}},
        "우선순위": {"select": {"name": "높음"}},
    },
    children=[
        blocks.h2("섹션 제목"),
        blocks.quote("요약 내용"),
        blocks.divider(),
        blocks.bullet("항목 1"),
        blocks.todo("할 일", checked=False),
    ]
)

# 블록 삭제
client.delete_block("block_id")

# 페이지 검색
results = client.search("키워드")
```

### blocks 헬퍼 목록

| 메서드 | 설명 |
|---|---|
| `blocks.h1/h2/h3(content)` | 제목 |
| `blocks.p(content, bold)` | 단락 |
| `blocks.bullet(content)` | 불릿 리스트 |
| `blocks.numbered(content)` | 번호 리스트 |
| `blocks.todo(content, checked)` | 체크박스 |
| `blocks.quote(content)` | 인용구 |
| `blocks.code(content, language)` | 코드 블록 |
| `blocks.divider()` | 구분선 |
| `blocks.link(content, url)` | 링크 단락 |
| `blocks.link_to_page(page_id)` | 노션 페이지 링크 |

## Claude Code MCP 설정

`claude/settings.json.template` 참고.

**필요한 토큰:**
- GitHub Personal Access Token: [github.com/settings/tokens](https://github.com/settings/tokens)
- Notion API Token: [notion.so/my-integrations](https://www.notion.so/my-integrations)

**주의:** 실제 토큰이 담긴 `settings.json` 은 `.gitignore` 에 포함되어 있어 커밋되지 않습니다.
