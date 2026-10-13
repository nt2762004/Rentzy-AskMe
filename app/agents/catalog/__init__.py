"""
Catalog & Product Agent Package
================================
Chịu trách nhiệm xử lý toàn diện các vấn đề về sản phẩm, váy đầm & thanh lý của Rentzy:
  - product_search: Tìm kiếm mẫu váy/đầm theo màu sắc, size, phong cách, dịp tiệc
  - product_price: Báo giá thuê và giá mua trang phục cụ thể
  - rent_or_liquidation: Phân biệt, tư vấn nên thuê hay mua thanh lý
  - liquidation: Danh mục và chính sách mua lại đồ thanh lý của Rentzy

Modules:
--------
- state: CatalogAgentState schema
- prompts: Templates, URLs, Sub-intent prompt builder
- nodes: analyze_query, retrieve_knowledge, generate_response
- graph: Sub-graph definition & run() entry point
"""

from app.agents.catalog.state import CatalogAgentState
from app.agents.catalog.prompts import (
    HOTLINE_NUMBER,
    SHOWROOM_ADDRESS,
    COLLECTIONS_URL,
    LIQUIDATION_URL,
    CATALOG_SUB_INTENTS,
    CATALOG_FALLBACK_REPLY,
    build_catalog_prompt,
)
from app.agents.catalog.nodes import (
    analyze_catalog_query_node,
    retrieve_catalog_knowledge_node,
    generate_catalog_response_node,
)
from app.agents.catalog.graph import catalog_graph, run

__all__ = [
    "CatalogAgentState",
    "HOTLINE_NUMBER",
    "SHOWROOM_ADDRESS",
    "COLLECTIONS_URL",
    "LIQUIDATION_URL",
    "CATALOG_SUB_INTENTS",
    "CATALOG_FALLBACK_REPLY",
    "build_catalog_prompt",
    "analyze_catalog_query_node",
    "retrieve_catalog_knowledge_node",
    "generate_catalog_response_node",
    "catalog_graph",
    "run",
]
