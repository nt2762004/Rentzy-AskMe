"""
StateGraph pipeline and runner for Overview Agent.
"""

import logging
from typing import Any, Dict
from langgraph.graph import StateGraph, END

from app.agents.overview.state import OverviewAgentState
from app.agents.overview.nodes import (
    analyze_overview_query_node,
    retrieve_overview_knowledge_node,
    generate_overview_response_node,
)

logger = logging.getLogger(__name__)


def build_overview_graph():
    """
    Sub-graph Pipeline:
      analyze_query → retrieve_knowledge → generate_response → END
    """
    workflow = StateGraph(OverviewAgentState)

    workflow.add_node("analyze_query", analyze_overview_query_node)
    workflow.add_node("retrieve_knowledge", retrieve_overview_knowledge_node)
    workflow.add_node("generate_response", generate_overview_response_node)

    workflow.set_entry_point("analyze_query")
    workflow.add_edge("analyze_query", "retrieve_knowledge")
    workflow.add_edge("retrieve_knowledge", "generate_response")
    workflow.add_edge("generate_response", END)

    return workflow.compile()


# Compiled singleton instance
overview_graph = build_overview_graph()


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Public entry point called by the main supervisor/dialogue graph.
    Nhận AgentState từ graph chính, invoke sub-graph, trả về output fields.
    """
    logger.info("  ┌── [OverviewAgent:Start] Nhận việc từ Supervisor: '%s'", state.get("message"))

    sub_input: OverviewAgentState = {
        "session_id": state.get("session_id", ""),
        "message": state.get("message", ""),
        "chat_history": state.get("chat_history", []),
        "sub_intent": "",
        "retrieved_chunks": [],
        "sources": [],
        "reply_message": "",
        "suggest_sales": False,
        "suggested_options": None,
        "need_clarification": False,
        "handled_by": None,
    }

    output = overview_graph.invoke(sub_input)

    logger.info("  └── [OverviewAgent:Exit] Hoàn tất -> Trả kết quả về Supervisor")

    return {
        "reply_message": output["reply_message"],
        "sources": output["sources"],
        "suggest_sales": output["suggest_sales"],
        "suggested_options": output["suggested_options"],
        "need_clarification": output["need_clarification"],
        "fallback_count": 0,
        "handled_by": output.get("handled_by", "overview_agent"),
    }
