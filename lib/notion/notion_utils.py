"""
Notion API 유틸리티
사용법:
    from lib.notion import NotionClient, blocks

    client = NotionClient(token="your_token")
    page = client.create_page(
        parent_id="db_or_page_id",
        parent_type="database",  # or "page"
        title="페이지 제목",
        properties={...},
        children=[
            blocks.h2("섹션 제목"),
            blocks.bullet("항목"),
        ]
    )
"""

import json
import urllib.request
import urllib.error
from typing import Any


# ─────────────────────────────────────────────
# 클라이언트
# ─────────────────────────────────────────────

class NotionClient:
    BASE_URL = "https://api.notion.com/v1"
    NOTION_VERSION = "2022-06-28"

    def __init__(self, token: str):
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": self.NOTION_VERSION,
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, data: dict = None) -> dict:
        url = f"{self.BASE_URL}{path}"
        body = json.dumps(data, ensure_ascii=False).encode() if data else None
        req = urllib.request.Request(url, data=body, headers=self.headers, method=method)
        try:
            with urllib.request.urlopen(req) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            return json.loads(e.read())

    # ── 페이지 ──────────────────────────────

    def create_page(
        self,
        parent_id: str,
        title: str,
        parent_type: str = "database",
        properties: dict = None,
        children: list = None,
    ) -> dict:
        """DB 또는 페이지 하위에 새 페이지 생성 (children 최대 100개)"""
        parent_key = "database_id" if parent_type == "database" else "page_id"
        props = properties or {}
        props["title"] = {"title": [{"text": {"content": title}}]}

        payload = {
            "parent": {parent_key: parent_id},
            "properties": props,
        }
        first_batch = (children or [])[:50]
        if first_batch:
            payload["children"] = first_batch

        result = self._request("POST", "/pages", payload)

        # 50개 초과 시 추가 append
        if result.get("object") == "page" and children and len(children) > 50:
            remaining = children[50:]
            self.append_blocks(result["id"], remaining)

        return result

    def update_page_properties(self, page_id: str, properties: dict) -> dict:
        """페이지 속성 업데이트 (제목, 상태, select 등)

        예시:
            # 상태 변경
            client.update_page_properties(page_id, {"상태": {"status": {"name": "진행 중"}}})
            # 제목 변경
            client.update_page_properties(page_id, {"이름": {"title": [{"type": "text", "text": {"content": "새 제목"}}]}})
            # select 변경
            client.update_page_properties(page_id, {"우선순위": {"select": {"name": "높음"}}})
        """
        return self._request("PATCH", f"/pages/{page_id}", {"properties": properties})

    def archive_page(self, page_id: str) -> dict:
        """페이지 삭제 (아카이브)"""
        return self._request("PATCH", f"/pages/{page_id}", {"archived": True})

    def search(self, query: str = "", filter_type: str = None) -> list:
        """페이지/DB 검색"""
        data = {"query": query}
        if filter_type:
            data["filter"] = {"value": filter_type, "property": "object"}
        result = self._request("POST", "/search", data)
        return result.get("results", [])

    # ── 블록 ──────────────────────────────

    def get_blocks(self, block_id: str) -> list:
        """블록 자식 목록 조회"""
        result = self._request("GET", f"/blocks/{block_id}/children?page_size=100")
        return result.get("results", [])

    def append_blocks(self, block_id: str, children: list) -> dict:
        """블록 하위에 children 추가"""
        return self._request("PATCH", f"/blocks/{block_id}/children", {"children": children})

    def update_block(self, block_id: str, data: dict) -> dict:
        """블록 내용 수정"""
        return self._request("PATCH", f"/blocks/{block_id}", data)

    def delete_block(self, block_id: str) -> dict:
        """블록 삭제"""
        return self._request("DELETE", f"/blocks/{block_id}")

    def delete_blocks(self, block_ids: list) -> list:
        """블록 여러 개 일괄 삭제"""
        return [self.delete_block(bid) for bid in block_ids]

    # ── DB ──────────────────────────────

    def get_database(self, db_id: str) -> dict:
        """DB 속성 및 옵션 조회"""
        return self._request("GET", f"/databases/{db_id}")

    def query_database(self, db_id: str, filter: dict = None) -> list:
        """DB 항목 조회"""
        data = {}
        if filter:
            data["filter"] = filter
        result = self._request("POST", f"/databases/{db_id}/query", data)
        return result.get("results", [])


# ─────────────────────────────────────────────
# 블록 헬퍼
# ─────────────────────────────────────────────

class blocks:
    """Notion 블록 생성 헬퍼"""

    @staticmethod
    def _text(content: str, bold: bool = False, color: str = None, link: str = None) -> dict:
        t = {"type": "text", "text": {"content": content}}
        if link:
            t["text"]["link"] = {"url": link}
        annotations = {}
        if bold:
            annotations["bold"] = True
        if color:
            annotations["color"] = color
        if annotations:
            t["annotations"] = annotations
        return t

    @staticmethod
    def h1(content: str) -> dict:
        return {"object": "block", "type": "heading_1",
                "heading_1": {"rich_text": [blocks._text(content)]}}

    @staticmethod
    def h2(content: str) -> dict:
        return {"object": "block", "type": "heading_2",
                "heading_2": {"rich_text": [blocks._text(content)]}}

    @staticmethod
    def h3(content: str) -> dict:
        return {"object": "block", "type": "heading_3",
                "heading_3": {"rich_text": [blocks._text(content)]}}

    @staticmethod
    def p(content: str, bold: bool = False) -> dict:
        return {"object": "block", "type": "paragraph",
                "paragraph": {"rich_text": [blocks._text(content, bold=bold)]}}

    @staticmethod
    def bullet(content: str) -> dict:
        return {"object": "block", "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [blocks._text(content)]}}

    @staticmethod
    def numbered(content: str) -> dict:
        return {"object": "block", "type": "numbered_list_item",
                "numbered_list_item": {"rich_text": [blocks._text(content)]}}

    @staticmethod
    def todo(content: str, checked: bool = False) -> dict:
        return {"object": "block", "type": "to_do",
                "to_do": {"rich_text": [blocks._text(content)], "checked": checked}}

    @staticmethod
    def quote(content: str) -> dict:
        return {"object": "block", "type": "quote",
                "quote": {"rich_text": [blocks._text(content)]}}

    @staticmethod
    def code(content: str, language: str = "plain text") -> dict:
        return {"object": "block", "type": "code",
                "code": {"rich_text": [blocks._text(content)], "language": language}}

    @staticmethod
    def divider() -> dict:
        return {"object": "block", "type": "divider", "divider": {}}

    @staticmethod
    def link(content: str, url: str, bold: bool = True, color: str = "blue") -> dict:
        """클릭 가능한 링크 paragraph"""
        return {"object": "block", "type": "paragraph",
                "paragraph": {"rich_text": [blocks._text(content, bold=bold, color=color, link=url)]}}

    @staticmethod
    def link_to_page(page_id: str) -> dict:
        """노션 페이지 링크 블록"""
        return {"object": "block", "type": "link_to_page",
                "link_to_page": {"type": "page_id", "page_id": page_id}}
