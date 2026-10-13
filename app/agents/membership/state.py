"""
State definition for Membership Agent.
"""

from typing import Any, Dict, List, Optional, TypedDict


class MembershipAgentState(TypedDict):
    """
    State container for Membership Sub-Graph execution.
    """
    # Inherited from main graph
    session_id: str
    message: str
    chat_history: List[Dict[str, str]]

    # Membership-specific fields
    sub_intent: str
    retrieved_chunks: List[str]
    sources: List[Dict[str, Any]]

    # Output fields (returned to main dialogue graph)
    reply_message: str
    suggest_sales: bool
    suggested_options: Optional[List[str]]
    need_clarification: bool
    handled_by: Optional[str]
