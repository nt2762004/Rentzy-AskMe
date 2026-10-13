"""
Support Agent Package
=====================
Chịu trách nhiệm xử lý toàn diện intent `contact_support` và `order_support`:
  - Hotline CSKH & tư vấn
  - Kết nối chuyên viên tư vấn / gặp người thật
  - Hỗ trợ và tra cứu đơn hàng
  - Tiếp nhận phản ánh sự cố & khiếu nại

Modules:
--------
- state: SupportAgentState schema
- prompts: Templates, Hotline, Showroom, Sub-intent prompt builder
- nodes: analyze_query, retrieve_knowledge, generate_response
- graph: Sub-graph definition & run() entry point
"""

from app.agents.support.state import SupportAgentState
from app.agents.support.prompts import (
    HOTLINE_NUMBER,
    SHOWROOM_ADDRESS,
    SUPPORT_HOURS,
    ZALO_URL,
    FANPAGE_URL,
    SUPPORT_SUB_INTENTS,
    SUPPORT_FALLBACK_REPLY,
    build_support_prompt,
)
from app.agents.support.nodes import (
    analyze_support_query_node,
    retrieve_support_knowledge_node,
    generate_support_response_node,
)
from app.agents.support.graph import support_graph, run

__all__ = [
    "SupportAgentState",
    "HOTLINE_NUMBER",
    "SHOWROOM_ADDRESS",
    "SUPPORT_HOURS",
    "ZALO_URL",
    "FANPAGE_URL",
    "SUPPORT_SUB_INTENTS",
    "SUPPORT_FALLBACK_REPLY",
    "build_support_prompt",
    "analyze_support_query_node",
    "retrieve_support_knowledge_node",
    "generate_support_response_node",
    "support_graph",
    "run",
]
