"""
State schema for Catalog Agent (Multi-Agent Architecture).
"""

from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class CatalogAgentState(TypedDict):
    session_id: str
    message: str
    chat_history: List[Dict[str, str]]
    sub_intent: str
    retrieved_chunks: List[str]
    sources: List[Dict[str, Any]]
    reply_message: str
    suggest_sales: bool
    suggested_options: Optional[List[str]]
    need_clarification: bool
    handled_by: Optional[str]
