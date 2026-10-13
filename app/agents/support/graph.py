"""
StateGraph definition and execution entry point for Support Agent.
"""

import logging
from typing import Any, Dict
from langgraph.graph import StateGraph, END

from app.agents.support.state import SupportAgentState
from app.agents.support.nodes import (
    analyze_support_query_node,
    retrieve_support_knowledge_node,
    generate_support_response_node,
)

logger = logging.getLogger(__name__)


def build_support_graph():
    """
    Xây dựng Sub-Graph cho Support Agent:
    analyze_query -> retrieve_knowledge -> generate_response -> END
    """
    workflow = StateGraph(SupportAgentState)

    workflow.add_node("analyze_query", analyze_support_query_node)
    workflow.add_node("retrieve_knowledge", retrieve_support_knowledge_node)
    workflow.add_node("generate_response", generate_support_response_node)

    workflow.set_entry_point("analyze_query")
    workflow.add_edge("analyze_query", "retrieve_knowledge")
    workflow.add_edge("retrieve_knowledge", "generate_response")
    workflow.add_edge("generate_response", END)

    return workflow.compile()


support_graph = build_support_graph()


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Entry point thực thi Support Agent từ Main Dialogue Graph (Supervisor).
    """
    logger.info("  ┌── [SupportAgent:Start] Nhận việc từ Supervisor: '%s'", state.get("message"))

    sub_state: SupportAgentState = {
        "session_id": state["session_id"],
        "message": state["message"],
        "chat_history": state.get("chat_history", []),
        "sub_intent": "",
        "retrieved_chunks": [],
        "sources": [],
        "reply_message": "",
        "suggest_sales": True,
        "suggested_options": None,
        "need_clarification": False,
        "handled_by": "support_agent",
    }

    result = support_graph.invoke(sub_state)

    logger.info("  └── [SupportAgent:Exit] Hoàn tất -> Trả kết quả về Supervisor")

    return {
        "reply_message": result.get("reply_message", ""),
        "sources": result.get("sources", []),
        "fallback_count": 0,
        "suggest_sales": True,
        "suggested_options": result.get("suggested_options"),
        "need_clarification": result.get("need_clarification", False),
        "handled_by": "support_agent",
    }
