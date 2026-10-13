"""
Overview Sub-Agent Package
==========================
Chịu trách nhiệm xử lý toàn diện intent `rentzy_overview`:
  - analyze_query: nhận diện sub-intent (brand_intro, showroom_address, hotline_contact, business_model, general)
  - retrieve_knowledge: truy xuất vector database với filter topic=rentzy_overview
  - generate_response: sinh câu trả lời giới thiệu thương hiệu chuẩn, địa chỉ showroom và hotline
"""

from app.agents.overview.state import OverviewAgentState
from app.agents.overview.prompts import (
    SHOWROOM_ADDRESS,
    HOTLINE_NUMBER,
    SHOWROOM_MAPS_URL,
    OVERVIEW_SUB_INTENTS,
    OVERVIEW_SUB_INTENT_FOCUS,
    OVERVIEW_FALLBACK_REPLY,
    build_overview_prompt,
)
from app.agents.overview.nodes import (
    analyze_overview_query_node,
    retrieve_overview_knowledge_node,
    generate_overview_response_node,
)
from app.agents.overview.graph import (
    build_overview_graph,
    overview_graph,
    run,
)

__all__ = [
    "run",
    "overview_graph",
    "build_overview_graph",
    "OverviewAgentState",
    "analyze_overview_query_node",
    "retrieve_overview_knowledge_node",
    "generate_overview_response_node",
    "SHOWROOM_ADDRESS",
    "HOTLINE_NUMBER",
    "SHOWROOM_MAPS_URL",
    "OVERVIEW_SUB_INTENTS",
    "OVERVIEW_SUB_INTENT_FOCUS",
    "OVERVIEW_FALLBACK_REPLY",
    "build_overview_prompt",
]
