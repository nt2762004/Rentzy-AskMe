"""
Rentzy Multi-Agent System Package
=================================
Mỗi sub-agent chịu trách nhiệm một domain nghiệp vụ riêng biệt, được tổ chức
thành từng folder module hóa chuẩn (state, prompts, nodes, graph):

Available Sub-Agents:
---------------------
- `membership`: Quản lý gói hội viên & quyền lợi thành viên
- `overview`: Quản lý thông tin giới thiệu thương hiệu, showroom, hotline
- `support`: Quản lý tư vấn, CSKH, hotline và hỗ trợ đơn hàng
- `policy`: Quản lý chính sách đặt cọc, hoàn cọc, giá thuê, giao nhận
- `catalog`: Quản lý tìm kiếm sản phẩm, báo giá trang phục, thanh lý đồ
"""

from app.agents import membership, overview, support, policy, catalog

__all__ = ["membership", "overview", "support", "policy", "catalog"]



