"""
State definition for Overview Agent.
"""

from typing import Any, Dict, List, Optional, TypedDict


class OverviewAgentState(TypedDict):
    """
    State container for Overview Sub-Graph execution.
    """
    # Inherited from main supervisor graph
    session_id: str
    message: str
    chat_history: List[Dict[str, str]]

    # Overview-specific fields
    sub_intent: str
    retrieved_chunks: List[str]
    sources: List[Dict[str, Any]]

    # Output fields (returned to main dialogue graph)
    reply_message: str
    suggest_sales: bool
    suggested_options: Optional[List[str]]
    need_clarification: bool
    handled_by: Optional[str]
