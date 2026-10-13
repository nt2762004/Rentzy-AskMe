"""
Policy Agent Package
====================
Chịu trách nhiệm xử lý toàn diện các quy định & chính sách thuê của Rentzy:
  - deposit_policy: Quy định đặt cọc, cọc CCCD / tiền mặt, phí cọc, hủy cọc đổi mẫu
  - deposit_refund: Thời gian hoàn cọc, hình thức trả lại cọc sau khi kiểm tra đồ
  - rental_pricing: Bảng giá thuê đồ, thời gian thuê tiêu chuẩn và phụ phí trễ hạn
  - receive_return: Giao nhận trang phục, kiểm tra khi nhận, trả đồ không cần giặt

Modules:
--------
- state: PolicyAgentState schema
- prompts: Templates, Key Rules, Sub-intent prompt builder
- nodes: analyze_query, retrieve_knowledge, generate_response
- graph: Sub-graph definition & run() entry point
"""

from app.agents.policy.state import PolicyAgentState
from app.agents.policy.prompts import (
    HOTLINE_NUMBER,
    SHOWROOM_ADDRESS,
    DEPOSIT_RULES_SUMMARY,
    DEPOSIT_REFUND_SUMMARY,
    RECEIVE_RETURN_SUMMARY,
    RENTAL_PRICING_SUMMARY,
    POLICY_SUB_INTENTS,
    POLICY_FALLBACK_REPLY,
    build_policy_prompt,
)
from app.agents.policy.nodes import (
    analyze_policy_query_node,
    retrieve_policy_knowledge_node,
    generate_policy_response_node,
)
from app.agents.policy.graph import policy_graph, run

__all__ = [
    "PolicyAgentState",
    "HOTLINE_NUMBER",
    "SHOWROOM_ADDRESS",
    "DEPOSIT_RULES_SUMMARY",
    "DEPOSIT_REFUND_SUMMARY",
    "RECEIVE_RETURN_SUMMARY",
    "RENTAL_PRICING_SUMMARY",
    "POLICY_SUB_INTENTS",
    "POLICY_FALLBACK_REPLY",
    "build_policy_prompt",
    "analyze_policy_query_node",
    "retrieve_policy_knowledge_node",
    "generate_policy_response_node",
    "policy_graph",
    "run",
]
