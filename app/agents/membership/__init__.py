"""
Membership Sub-Agent Package
============================
Chịu trách nhiệm xử lý toàn diện intent `membership`:
  - analyze_query: nhận diện sub-intent (overview, pricing, benefits, register, compare, renew)
  - retrieve_knowledge: truy xuất vector database với filter topic=membership
  - generate_response: sinh câu trả lời với giọng điệu Rentzy chuẩn & link đăng ký bắt buộc
"""

from app.agents.membership.state import MembershipAgentState
from app.agents.membership.prompts import (
    MEMBERSHIP_REGISTER_URL,
    MEMBERSHIP_SUB_INTENTS,
    SUB_INTENT_FOCUS,
    build_membership_prompt,
)
from app.agents.membership.nodes import (
    analyze_membership_query_node,
    retrieve_membership_knowledge_node,
    generate_membership_response_node,
)
from app.agents.membership.graph import (
    build_membership_graph,
    membership_graph,
    run,
)

__all__ = [
    "run",
    "membership_graph",
    "build_membership_graph",
    "MembershipAgentState",
    "analyze_membership_query_node",
    "retrieve_membership_knowledge_node",
    "generate_membership_response_node",
    "MEMBERSHIP_REGISTER_URL",
    "MEMBERSHIP_SUB_INTENTS",
    "SUB_INTENT_FOCUS",
    "build_membership_prompt",
]
