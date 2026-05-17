"""
PROPRIETARY — ALL RIGHTS RESERVED

Copyright (c) 2026 Allaun Holdings

ADAPTER LAYER — PageIndex → CFF Bridge

This module is the SOLE point of contact between proprietary CFF code
and MIT-licensed PageIndex code. It imports PageIndex as an external
library WITHOUT modifying, copying, or inlining any MIT-licensed source.

All logic in this file is proprietary. The PageIndex library it imports
resides in third_party/pageindex/ under its own MIT license.

ARCHITECTURAL RULE: No other proprietary module may import from PageIndex
directly. All PageIndex access flows through this adapter.
"""

import sys
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

__all__ = [
    "PageIndexBridge",
    "DocumentTreeNode",
    "build_pageindex_for_pdf",
    "search_with_pageindex",
]


# --- Add third_party to path for PageIndex import ---
_THIRD_PARTY_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "third_party", "pageindex")
)
if _THIRD_PARTY_PATH not in sys.path:
    sys.path.insert(0, _THIRD_PARTY_PATH)


@dataclass
class DocumentTreeNode:
    """Proprietary document tree node (bridged from PageIndex)."""
    title: str
    node_id: str
    start_page: int
    end_page: int
    summary: str = ""
    children: List["DocumentTreeNode"] = field(default_factory=list)
    pageindex_raw: Optional[Dict] = field(default=None, repr=False)

    @classmethod
    def from_pageindex_node(cls, node: Dict) -> "DocumentTreeNode":
        return cls(
            title=node.get("title", ""),
            node_id=node.get("node_id", ""),
            start_page=node.get("start_index", 0),
            end_page=node.get("end_index", 0),
            summary=node.get("summary", ""),
            children=[
                cls.from_pageindex_node(child)
                for child in node.get("nodes", [])
            ],
            pageindex_raw=node,
        )


class PageIndexBridge:
    """
    Proprietary bridge between CFF pipeline and MIT-licensed PageIndex.

    Responsibilities:
      1. Build PageIndex trees from academic PDFs
      2. Expose search over those trees
      3. Return DocumentTreeNode objects for downstream CFF ingestion
      4. NEVER expose raw PageIndex internals to proprietary callers
    """

    def __init__(self, llm_api_key: Optional[str] = None,
                 model: str = "gpt-4o-2024-11-20"):
        self._model = model
        self._api_key = llm_api_key or os.environ.get("OPENAI_API_KEY", "")
        self._trees: Dict[str, DocumentTreeNode] = {}

    def build_tree(self, pdf_path: str, toc_pages: int = 20,
                   max_pages_per_node: int = 10,
                   max_tokens_per_node: int = 20000) -> Optional[DocumentTreeNode]:
        """
        Build a PageIndex tree from a PDF.

        Calls PageIndex's run_pageindex module. This is an adapter call —
        proprietary logic determines HOW and WHEN to call it, but the
        tree-building algorithm is PageIndex's (MIT-licensed).
        """
        try:
            from pageindex import generate_tree

            tree_data = generate_tree.generate_pageindex_tree(
                pdf_path=pdf_path,
                model=self._model,
                toc_check_pages=toc_pages,
                max_pages_per_node=max_pages_per_node,
                max_tokens_per_node=max_tokens_per_node,
            )

            if tree_data:
                root = DocumentTreeNode.from_pageindex_node(tree_data)
                self._trees[pdf_path] = root
                return root

        except ImportError:
            pass
        except Exception:
            pass

        return None

    def search(self, pdf_path: str, query: str,
               context_window: int = 4) -> List[Dict[str, Any]]:
        """
        Search a PageIndex tree. Returns relevant sections with page
        numbers and summaries.

        The search logic itself is proprietary routing — we're not
        copying PageIndex's search, just using its tree structure.
        """
        tree = self._trees.get(pdf_path)
        if not tree:
            return []

        results = []
        self._search_node(tree, query.lower(), results)
        results.sort(key=lambda r: r.get("relevance", 0), reverse=True)
        return results[:context_window]

    def _search_node(self, node: DocumentTreeNode, query: str,
                     results: List[Dict[str, Any]]):
        """Proprietary search routing over a PageIndex tree."""
        relevance = max(
            self._term_match(node.title, query),
            self._term_match(node.summary, query),
        )

        if relevance > 0:
            results.append({
                "node_id": node.node_id,
                "title": node.title,
                "start_page": node.start_page,
                "end_page": node.end_page,
                "summary": node.summary,
                "relevance": relevance,
            })

        for child in node.children:
            self._search_node(child, query, results)

    @staticmethod
    def _term_match(text: str, query: str) -> float:
        text_lower = text.lower()
        if query in text_lower:
            return 1.0
        terms = query.split()
        matches = sum(1 for t in terms if t in text_lower)
        return matches / max(len(terms), 1)

    def get_page_range(self, pdf_path: str, node_id: str) -> Optional[tuple]:
        """Get (start_page, end_page) for a node."""
        tree = self._trees.get(pdf_path)
        if not tree:
            return None

        def _find(n: DocumentTreeNode) -> Optional[DocumentTreeNode]:
            if n.node_id == node_id:
                return n
            for child in n.children:
                found = _find(child)
                if found:
                    return found
            return None

        found = _find(tree)
        if found:
            return (found.start_page, found.end_page)
        return None

    def extract_doi_candidates(self, pdf_path: str) -> List[str]:
        """
        Scan PageIndex tree for DOI-like patterns.
        Returns list of candidate DOIs for CFF ingestion.
        """
        tree = self._trees.get(pdf_path)
        if not tree:
            return []

        dois = []
        self._extract_dois(tree, dois)
        return dois

    def _extract_dois(self, node: DocumentTreeNode, acc: List[str]):
        import re
        doi_pattern = re.compile(
            r'\b(10\.\d{4,}(?:[.][^/\s]+)?/[-._;()/:a-zA-Z0-9]+)\b'
        )
        for field in [node.title, node.summary]:
            if field:
                matches = doi_pattern.findall(field)
                acc.extend(matches)
        for child in node.children:
            self._extract_dois(child, acc)


# --- Convenience Functions ---

def build_pageindex_for_pdf(pdf_path: str,
                            api_key: Optional[str] = None) -> Optional[DocumentTreeNode]:
    bridge = PageIndexBridge(llm_api_key=api_key)
    return bridge.build_tree(pdf_path)


def search_with_pageindex(pdf_path: str, query: str,
                          api_key: Optional[str] = None) -> List[Dict[str, Any]]:
    bridge = PageIndexBridge(llm_api_key=api_key)
    return bridge.search(pdf_path, query)
