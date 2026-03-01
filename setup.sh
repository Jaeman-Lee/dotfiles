#!/bin/bash
# 개발 환경 세팅 스크립트
# 사용법: bash setup.sh

set -e

echo "=== 개발 환경 세팅 시작 ==="

# ── Node.js (nvm) ──────────────────────────────
if [ ! -d "$HOME/.nvm" ]; then
    echo "[1/3] nvm 설치 중..."
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
else
    echo "[1/3] nvm 이미 설치됨"
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
fi

if ! node --version | grep -q "v20"; then
    echo "     Node.js 20 설치 중..."
    nvm install 20
    nvm alias default 20
else
    echo "     Node.js $(node --version) 이미 설치됨"
fi

# ── Notion MCP 서버 ──────────────────────────────
echo "[2/3] notion-mcp-server 설치 중..."
npm install -g @notionhq/notion-mcp-server 2>/dev/null && echo "     완료" || echo "     이미 설치됨"

# ── Claude Code 설정 ──────────────────────────────
echo "[3/3] Claude Code 설정 적용 중..."
SETTINGS_DIR="$HOME/.claude"
TEMPLATE="$(dirname "$0")/claude/settings.json.template"

mkdir -p "$SETTINGS_DIR"

if [ -f "$SETTINGS_DIR/settings.json" ]; then
    echo "     ~/.claude/settings.json 이미 존재 — 건너뜀"
    echo "     수동으로 $TEMPLATE 참고하여 설정하세요"
else
    cp "$TEMPLATE" "$SETTINGS_DIR/settings.json"
    echo "     템플릿 복사 완료"
    echo "     ⚠️  ~/.claude/settings.json 에서 토큰 직접 입력 필요:"
    echo "        - GITHUB_PERSONAL_ACCESS_TOKEN"
    echo "        - Notion Bearer Token"
    echo "        - YOUR_USERNAME → 실제 username으로 변경"
fi

echo ""
echo "=== 세팅 완료 ==="
echo ""
echo "다음 단계:"
echo "  1. ~/.claude/settings.json 에 토큰 입력"
echo "  2. Claude Code 재시작"
