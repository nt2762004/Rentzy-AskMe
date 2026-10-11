/**
 * Rentzy AI Advisor Chatbot Widget
 * v4.5 Persistent Quick Menu Edition
 *
 * Pure Vanilla JS
 * Zero Dependencies
 *
 * States:
 *   CLOSED
 *   OPEN (Conversational stream with persistent Quick Menu sub-bar)
 */

(function () {
  "use strict";

  /* ============================================================
     PREVENT DUPLICATE INITIALIZATION
     ============================================================ */

  if (window.RentzyWidgetInitialized) {
    return;
  }

  window.RentzyWidgetInitialized = true;

  /* ============================================================
     API ORIGIN
     ============================================================ */

  const scriptTag =
    document.currentScript ||
    document.querySelector('script[src*="rentzy-widget.js"]');

  // Base URL for static assets (CSS, etc.) always follows where widget JS is hosted
  let assetBaseUrl = window.location.origin;
  if (scriptTag && scriptTag.src) {
    try {
      const url = new URL(scriptTag.src, window.location.href);
      if (url.origin && url.origin !== "null") {
        assetBaseUrl = url.origin;
      }
    } catch (_) { }
  }

  // Base URL for API requests
  let apiBaseUrl = window.RENTZY_API_URL || "";
  if (!apiBaseUrl && scriptTag) {
    const customApi = scriptTag.getAttribute("data-api-url");
    if (customApi) {
      const isLocalHost = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
      if (isLocalHost && customApi.includes("onrender.com")) {
        apiBaseUrl = window.location.origin;
      } else {
        apiBaseUrl = customApi.replace(/\/+$/, "");
      }
    }
  }
  if (!apiBaseUrl) {
    apiBaseUrl = assetBaseUrl || window.location.origin;
  }

  /* ============================================================
     CSS INJECTION (LINK + INLINE CRITICAL FALLBACK)
     ============================================================ */

  const cssHref = `${assetBaseUrl}/static/css/rentzy-widget.css?v=6.5`;

  if (!document.querySelector(`link[data-rentzy-widget-css="true"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = cssHref;
    link.dataset.rentzyWidgetCss = "true";
    document.head.appendChild(link);
  }

  if (!document.getElementById("rw-critical-styles")) {
    const styleEl = document.createElement("style");
    styleEl.id = "rw-critical-styles";
    styleEl.textContent = `
      #rentzy-widget-root {
        --rw-window-w: 490px !important;
        --rw-window-h: 670px !important;
      }
      .rw-chat-window {
        width: min(490px, calc(100vw - 32px)) !important;
        height: min(670px, calc(100vh - 32px)) !important;
        max-height: calc(100vh - 32px) !important;
      }
      @media (max-width: 480px) {
        .rw-chat-window {
          width: calc(100vw - 20px) !important;
          height: min(670px, calc(100vh - 20px)) !important;
          max-height: calc(100vh - 20px) !important;
        }
      }
      .rw-launcher-btn {
        animation: rw-btn-breathe 4s ease-in-out infinite !important;
      }
      .rw-launcher-btn::before {
        content: "" !important;
        position: absolute !important;
        inset: -5px !important;
        border-radius: 50% !important;
        background: radial-gradient(circle, rgba(224, 82, 99, 0.45) 0%, rgba(197, 160, 89, 0.35) 60%, transparent 100%) !important;
        z-index: -1 !important;
        animation: rw-pulse-ring 2.8s cubic-bezier(0.25, 1, 0.5, 1) infinite !important;
        pointer-events: none !important;
      }
      @keyframes rw-pulse-ring {
        0% { transform: scale(0.92); opacity: 0.85; }
        60%, 100% { transform: scale(1.42); opacity: 0; }
      }
      @keyframes rw-btn-breathe {
        0%, 100% { transform: scale(1); }
        50%      { transform: scale(1.07); }
      }
      .rw-launcher-tooltip {
        position: fixed !important;
        right: 24px !important;
        bottom: calc(24px + var(--rw-fab-size) + 12px) !important;
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
        padding: 8px 12px 8px 14px !important;
        max-width: 320px !important;
        background: linear-gradient(135deg, #1f1d1a 0%, #2f2a24 100%) !important;
        color: #fff !important;
        border: 1px solid rgba(197, 160, 89, 0.5) !important;
        border-radius: 20px !important;
        box-shadow: 0 10px 28px rgba(26, 24, 23, 0.25), 0 2px 8px rgba(197, 160, 89, 0.18) !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        white-space: nowrap !important;
        opacity: 0 !important;
        transform: translateY(8px) scale(0.94);
        pointer-events: none !important;
        cursor: pointer !important;
        transition: opacity 220ms var(--rw-ease), transform 220ms var(--rw-ease) !important;
        z-index: 99998 !important;
      }
      .rw-launcher-tooltip::after {
        content: "" !important;
        position: absolute !important;
        bottom: -6px !important;
        right: 22px !important;
        width: 10px !important;
        height: 10px !important;
        background: #27231f !important;
        border-right: 1px solid rgba(197, 160, 89, 0.5) !important;
        border-bottom: 1px solid rgba(197, 160, 89, 0.5) !important;
        transform: rotate(45deg) !important;
      }
      .rw-launcher-tooltip.rw-show {
        opacity: 1 !important;
        pointer-events: auto !important;
        animation: rw-tooltip-invite 2.8s ease-in-out infinite !important;
      }
      @keyframes rw-tooltip-invite {
        0%, 100% {
          transform: translateY(0) scale(1);
          box-shadow: 0 8px 24px rgba(26, 24, 23, 0.28), 0 0 12px rgba(197, 160, 89, 0.25);
          border-color: rgba(197, 160, 89, 0.5);
        }
        25% {
          transform: translateY(-9px) scale(1.05);
          box-shadow: 0 16px 36px rgba(26, 24, 23, 0.38), 0 0 22px rgba(224, 82, 99, 0.5);
          border-color: #e05263;
        }
        50% {
          transform: translateY(-3px) scale(1.02);
          box-shadow: 0 10px 26px rgba(26, 24, 23, 0.3), 0 0 14px rgba(197, 160, 89, 0.35);
          border-color: #dfba73;
        }
        70% {
          transform: translateY(-7px) scale(1.04);
          box-shadow: 0 14px 32px rgba(26, 24, 23, 0.34), 0 0 18px rgba(224, 82, 99, 0.42);
          border-color: #e05263;
        }
      }
      .rw-launcher-tooltip:hover {
        animation-play-state: paused !important;
        border-color: #c5a059 !important;
      }
      .rw-tooltip-shimmer {
        position: absolute !important;
        inset: 0 !important;
        border-radius: 20px !important;
        overflow: hidden !important;
        pointer-events: none !important;
      }
      .rw-tooltip-shimmer::before {
        content: "" !important;
        position: absolute !important;
        top: 0 !important;
        left: -120% !important;
        width: 65% !important;
        height: 100% !important;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.22), transparent) !important;
        transform: skewX(-25deg) !important;
        animation: rw-shimmer-sweep 3.6s infinite ease-in-out !important;
      }
      @keyframes rw-shimmer-sweep {
        0%, 35% {
          left: -120%;
        }
        65%, 100% {
          left: 220%;
        }
      }
      .rw-tooltip-body {
        display: flex !important;
        align-items: center !important;
        gap: 7px !important;
        user-select: none !important;
        position: relative !important;
        z-index: 1 !important;
      }
      .rw-tooltip-emoji {
        font-size: 16px !important;
        line-height: 1 !important;
        display: inline-block !important;
        transform-origin: center center !important;
        animation: rw-heart-pulse 2.2s infinite ease-in-out !important;
      }
      @keyframes rw-heart-pulse {
        0%, 100% {
          transform: scale(1);
        }
        14% {
          transform: scale(1.35) rotate(-6deg);
        }
        28% {
          transform: scale(1.08) rotate(4deg);
        }
        42% {
          transform: scale(1.28) rotate(-2deg);
        }
        58% {
          transform: scale(1) rotate(0deg);
        }
      }
      .rw-tooltip-text {
        font-size: 12px !important;
        font-weight: 600 !important;
        color: #f7e6c4 !important;
        letter-spacing: 0.2px !important;
      }
      .rw-launcher-tooltip:hover .rw-tooltip-text {
        color: #ffffff !important;
      }
      .rw-tooltip-close {
        width: 18px !important;
        height: 18px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 0 !important;
        border: none !important;
        border-radius: 50% !important;
        background: rgba(255, 255, 255, 0.1) !important;
        color: rgba(255, 255, 255, 0.7) !important;
        cursor: pointer !important;
        font-size: 13px !important;
        line-height: 1 !important;
        margin-left: 2px !important;
      }
      .rw-tooltip-close:hover {
        background: rgba(224, 82, 99, 0.4) !important;
        color: #fff !important;
      }
      #rentzy-widget-root.rw-is-open .rw-launcher-tooltip {
        opacity: 0 !important;
        pointer-events: none !important;
      }
      .rw-welcome-options {
        display: grid !important;
        grid-template-columns: repeat(2, 1fr) !important;
        gap: 6px !important;
        margin-top: 10px !important;
        padding-top: 10px !important;
        border-top: 1px dashed rgba(232, 228, 220, 0.9) !important;
      }
      .rw-welcome-chip {
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        padding: 7px 9px !important;
        background: #ffffff !important;
        border: 1px solid rgba(197, 160, 89, 0.35) !important;
        border-radius: 9px !important;
        cursor: pointer !important;
        text-align: left !important;
        transition: all 0.18s ease !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03) !important;
        min-height: 34px !important;
        box-sizing: border-box !important;
        font-family: inherit !important;
      }
      .rw-welcome-chip:hover {
        background: #fff0f2 !important;
        border-color: #e05263 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 3px 8px rgba(224, 82, 99, 0.12) !important;
      }
      .rw-wchip-label {
        font-size: 11.5px !important;
        font-weight: 600 !important;
        color: #1a1817 !important;
        line-height: 1.25 !important;
      }
      .rw-welcome-chip:hover .rw-wchip-label {
        color: #b82e42 !important;
      }
      .rw-wchip-badge {
        font-size: 8px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.3px !important;
        padding: 1.5px 4.5px !important;
        border-radius: 4px !important;
        background: rgba(156, 149, 142, 0.15) !important;
        color: #7d756d !important;
        flex-shrink: 0 !important;
        margin-left: 4px !important;
        line-height: 1.1 !important;
      }
      .rw-welcome-chip:hover .rw-wchip-badge {
        background: rgba(224, 82, 99, 0.12) !important;
        color: #b82e42 !important;
      }
      .rw-quick-replies {
        display: flex !important;
        flex-direction: column !important;
        gap: 6px !important;
        margin-top: 8px !important;
        padding-top: 8px !important;
        border-top: 1px dashed rgba(232, 228, 220, 0.9) !important;
        width: 100% !important;
      }
      .rw-pill-btn {
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        width: 100% !important;
        padding: 7px 11px !important;
        border: 1px solid rgba(197, 160, 89, 0.35) !important;
        border-radius: 8px !important;
        background: #faf5eb !important;
        color: #8c6b2d !important;
        font-size: 11.5px !important;
        font-weight: 600 !important;
        line-height: 1.3 !important;
        cursor: pointer !important;
        font-family: inherit !important;
        text-align: left !important;
        box-sizing: border-box !important;
        transition: all 0.16s ease !important;
      }
      .rw-pill-btn:hover {
        background: #c5a059 !important;
        color: #ffffff !important;
        transform: translateX(2px) !important;
        box-shadow: 0 2px 6px rgba(197, 160, 89, 0.25) !important;
      }
      .rw-pill-btn.rw-pill-is-upcoming {
        border-color: rgba(156, 149, 142, 0.35) !important;
        background: #f7f6f4 !important;
        color: #635d57 !important;
      }
      .rw-pill-btn.rw-pill-is-upcoming:hover {
        background: #ede9e3 !important;
        border-color: #c5a059 !important;
        color: #1a1817 !important;
      }
      .rw-pill-badge {
        font-size: 8px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.3px !important;
        padding: 1.5px 4.5px !important;
        border-radius: 3px !important;
        background: rgba(156, 149, 142, 0.18) !important;
        color: #7d766f !important;
        line-height: 1.1 !important;
        flex-shrink: 0 !important;
        margin-left: 6px !important;
      }
      .rw-contact-badge,
      .rw-phone-badge,
      .rw-address-badge {
        display: flex !important;
        flex-direction: column !important;
        gap: 3px !important;
        padding: 7px 11px !important;
        margin: 4px 0 2px 0 !important;
        border-radius: 9px !important;
        background: #fdfbf7 !important;
        color: #4a3610 !important;
        border: 1px solid rgba(197, 160, 89, 0.45) !important;
        font-size: 12px !important;
        line-height: 1.4 !important;
        text-decoration: none !important;
        box-shadow: 0 1.5px 5px rgba(197, 160, 89, 0.1) !important;
        transition: all 0.18s ease !important;
        width: 100% !important;
        box-sizing: border-box !important;
      }
      .rw-contact-badge:hover,
      .rw-phone-badge:hover,
      .rw-address-badge:hover {
        background: #fcf6eb !important;
        border-color: #c5a059 !important;
        color: #382705 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 3px 9px rgba(197, 160, 89, 0.22) !important;
      }
      .rw-contact-main,
      .rw-addr-main {
        display: flex !important;
        align-items: flex-start !important;
        gap: 6px !important;
      }
      .rw-contact-main .rw-hl-icon,
      .rw-addr-main .rw-hl-icon {
        width: 13px !important;
        height: 13px !important;
        flex-shrink: 0 !important;
        margin-top: 2px !important;
      }
      .rw-phone-badge .rw-hl-icon {
        color: #e05263 !important;
      }
      .rw-address-badge .rw-hl-icon {
        color: #c5a059 !important;
      }
      .rw-contact-text,
      .rw-addr-text {
        font-weight: 600 !important;
        color: #2b2620 !important;
      }
      .rw-contact-hint,
      .rw-addr-hint {
        display: inline-flex !important;
        align-items: center !important;
        gap: 3px !important;
        font-size: 10.5px !important;
        font-weight: 600 !important;
        margin-left: 19px !important;
        letter-spacing: 0.2px !important;
        transition: color 0.15s ease !important;
      }
      .rw-phone-badge .rw-contact-hint,
      .rw-phone-badge .rw-addr-hint {
        color: #e05263 !important;
      }
      .rw-address-badge .rw-contact-hint,
      .rw-address-badge .rw-addr-hint {
        color: #b3862b !important;
      }
      .rw-phone-badge:hover .rw-contact-hint,
      .rw-phone-badge:hover .rw-addr-hint {
        color: #b82e42 !important;
      }
      .rw-address-badge:hover .rw-contact-hint,
      .rw-address-badge:hover .rw-addr-hint {
        color: #e05263 !important;
      }
      .rw-membership-card {
        margin-top: 10px !important;
        padding-top: 8px !important;
        border-top: 1px dashed rgba(232, 228, 220, 0.9) !important;
        width: 100% !important;
      }
      .rw-membership-btn {
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        width: 100% !important;
        padding: 9px 13px !important;
        border-radius: 9px !important;
        background: linear-gradient(135deg, #1f1d1a 0%, #2f2a24 100%) !important;
        color: #f7e6c4 !important;
        border: 1px solid #c5a059 !important;
        text-decoration: none !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.12) !important;
        transition: all 0.2s ease !important;
        box-sizing: border-box !important;
      }
      .rw-membership-btn:hover {
        background: linear-gradient(135deg, #2b2722 0%, #3d362e 100%) !important;
        color: #ffffff !important;
        border-color: #dfba73 !important;
        transform: translateY(-1.5px) !important;
        box-shadow: 0 5px 14px rgba(197, 160, 89, 0.28) !important;
      }
      .rw-mbtn-left {
        display: flex !important;
        align-items: center !important;
        gap: 7px !important;
        min-width: 0 !important;
      }
      .rw-mbtn-icon {
        font-size: 14px !important;
        line-height: 1 !important;
        flex-shrink: 0 !important;
      }
      .rw-mbtn-text {
        font-size: 12px !important;
        font-weight: 600 !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
      }
      .rw-mbtn-arrow {
        width: 14px !important;
        height: 14px !important;
        flex-shrink: 0 !important;
        color: #c5a059 !important;
        transition: transform 0.18s ease !important;
      }
      .rw-membership-btn:hover .rw-mbtn-arrow {
        transform: translateX(3px) !important;
        color: #ffffff !important;
      }
    `;
    document.head.appendChild(styleEl);
  }

  /* ============================================================
     SESSION
     ============================================================ */

  function getOrCreateSessionId() {
    const key = "rentzy_askme_session_id";
    let id = localStorage.getItem(key);

    if (!id) {
      id = "rz_" + Math.random().toString(36).slice(2, 10) + "_" + Date.now();
      localStorage.setItem(key, id);
    }

    return id;
  }

  const SESSION_ID = getOrCreateSessionId();

  /* ============================================================
     STATE
     ============================================================ */

  let isOpen = false;
  let isSending = false;
  let quickMenuVisible = true;
  let tooltipTimer = null;

  /* ============================================================
     QUICK ACTIONS MENU DATA
     ============================================================ */

  /* ============================================================
     QUICK ACTIONS MENU DATA (4 mục chính + mục "Xem thêm")
     ============================================================ */

  const PRIMARY_MENU = [
    {
      emoji: "👗",
      title: "Tìm trang phục",
      query: "Tôi muốn tìm trang phục phù hợp cho sự kiện",
      status: "upcoming"
    },
    {
      emoji: "🏷️",
      title: "Xem giá và lịch thuê",
      query: "Cho tôi xem bảng giá thuê và cách tính ngày thuê đồ",
      status: "upcoming"
    },
    {
      emoji: "📋",
      title: "Chính sách thuê đồ",
      query: "Chính sách đặt cọc và quy định thuê đồ như thế nào?",
      status: "upcoming"
    }
  ];

  const MORE_MENU = [
    {
      emoji: "🛍️",
      title: "Sản phẩm thanh lý",
      query: "Rentzy có bán các sản phẩm thanh lý không?",
      status: "upcoming"
    },
    {
      emoji: "📦",
      title: "Theo dõi đơn hàng",
      query: "Tôi muốn kiểm tra và theo dõi đơn hàng của tôi",
      status: "upcoming"
    },
    {
      emoji: "📞",
      title: "Liên hệ Rentzy",
      query: "Tôi cần liên hệ chuyên viên tư vấn hoặc hotline Rentzy",
      status: "active"
    },
    {
      emoji: "ℹ️",
      title: "Giới thiệu Rentzy",
      query: "Cho tôi biết thông tin tổng quan về dịch vụ Rentzy",
      status: "active"
    },
    {
      emoji: "💎",
      title: "Gói thành viên",
      query: "Các gói Membership thành viên tại Rentzy gồm những gì?",
      status: "active"
    }
  ];

  const WELCOME_OCCASIONS = [
    { label: "🥂 Đi tiệc", query: "Tôi đang tìm trang phục đi tiệc" },
    { label: "📸 Chụp ảnh", query: "Tôi đang tìm trang phục chụp ảnh" },
    { label: "✈️ Du lịch", query: "Tôi đang tìm trang phục du lịch" },
    { label: "💼 Công sở", query: "Tôi đang tìm trang phục công sở" },
    { label: "🌸 Áo dài", query: "Tôi đang tìm áo dài" },
    { label: "💡 Cần tư vấn", query: "Tôi chưa biết chọn trang phục nào, cần tư vấn" }
  ];

  let isMoreExpanded = false;


  /* ============================================================
     HELPERS
     ============================================================ */

  function esc(value) {
    if (value == null) return "";
    if (typeof value === "object") {
      value = value.title || value.name || JSON.stringify(value);
    }
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function now() {
    return new Date().toLocaleTimeString("vi-VN", {
      hour: "2-digit",
      minute: "2-digit"
    });
  }

  /* ============================================================
     MINIMAL MARKDOWN PARSER & ENTITY HIGHLIGHTER
     ============================================================ */

  function renderMarkdown(raw) {
    if (!raw) return "";

    let text = esc(raw);

    // 1. Detect and strip membership link so we can render it as a luxury CTA button
    let hasMembershipLink = false;
    if (/https:\/\/rentzy\.vn\/member-ship\/?/i.test(text)) {
      hasMembershipLink = true;
      // Strip any preceding sentence referencing the link or the link itself
      text = text.replace(
        /(?:(?:[-•*]\s*)?(?:Nàng|Bạn|Khách hàng)?\s*[^.\n]*?(?:tham khảo|đăng ký|quyền lợi|xem thêm|tại đây)[^:\n]*?:\s*)?(?:\[[^\]]*\]\()?https:\/\/rentzy\.vn\/member-ship\/?\)?/gi,
        ""
      );
    }

    // 2. Highlight Phone Numbers -> Click to call hotline
    text = text.replace(
      /(?<!\w)(0[2-9]\d{8,9}|0[2-9]\d{1,2}[\s.-]\d{3}[\s.-]\d{3,4}|1[89]00[\s.-]?\d{4,6})(?!\w)/g,
      (match) => {
        const cleanDigits = match.replace(/[\s.-]/g, "");
        return `<a href="tel:${cleanDigits}" class="rw-contact-badge rw-phone-badge" title="Nhấn để gọi hotline Rentzy"><span class="rw-contact-main rw-addr-main"><svg class="rw-hl-icon rw-phone-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M6.62 10.79a15.05 15.05 0 006.59 6.59l2.2-2.2a1 1 0 011.02-.24c1.12.37 2.33.57 3.57.57a1 1 0 011 1V20a1 1 0 01-1 1A17 17 0 013 4a1 1 0 011-1h3.5a1 1 0 011 1c0 1.25.2 2.45.57 3.57.1.34.02.72-.25 1.02l-2.2 2.2z"/></svg><span class="rw-contact-text rw-addr-text">${match}</span></span><span class="rw-contact-hint rw-addr-hint">Gọi hotline ngay ↗</span></a>`;
      }
    );

    // 3. Highlight Showroom Address -> Click to open Google Maps
    const RENTZY_SHOWROOM_MAP_URL = "https://maps.app.goo.gl/ShHNabftWGUSmy6N6";
    text = text.replace(
      /(51\s+(?:đường\s+số|đ\.\s*số|đường)?\s*41[^,\n<]*,\s*(?:phường|p\.)\s*Khánh\s*Hội[^,\n<]*,\s*(?:TP\.\s*Hồ\s*Chí\s*Minh|TPHCM|TP\s+Hồ\s+Chí\s+Minh|Quận\s*4)[^.\n<]*)/gi,
      (match) => {
        return `<a href="${RENTZY_SHOWROOM_MAP_URL}" target="_blank" rel="noopener noreferrer" class="rw-contact-badge rw-address-badge" title="Nhấn để mở chỉ đường trên Google Maps"><span class="rw-contact-main rw-addr-main"><svg class="rw-hl-icon rw-addr-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5a2.5 2.5 0 110-5 2.5 2.5 0 010 5z"/></svg><span class="rw-contact-text rw-addr-text">${match}</span></span><span class="rw-contact-hint rw-addr-hint">Chỉ đường Google Maps ↗</span></a>`;
      }
    );

    // 4. Markdown link [Text](URL)
    text = text.replace(
      /\[([^\]]+)\]\((https?:\/\/[^\s\)]+)\)/g,
      '<a href="$2" target="_blank" rel="noopener noreferrer" class="rw-link">$1</a>'
    );

    // 5. Standalone URL
    text = text.replace(
      /(^|[\s\(\[\{])(https?:\/\/[^\s<>\)\]\}]+)/g,
      '$1<a href="$2" target="_blank" rel="noopener noreferrer" class="rw-link">$2</a>'
    );

    text = text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    text = text.replace(/(?<!\*)\*(?!\*)([^*]+)\*(?!\*)/g, "<em>$1</em>");

    const lines = text.split(/\n/);
    const htmlLines = lines.map((line) => {
      const bulletMatch = line.match(/^\s*[-•*]\s+(.+)/);
      if (bulletMatch) {
        return `<div class="rw-bullet-item"><span class="rw-bullet-dot">•</span><span class="rw-bullet-text">${bulletMatch[1]}</span></div>`;
      }
      const numMatch = line.match(/^\s*(\d+)\.\s+(.+)/);
      if (numMatch) {
        return `<div class="rw-num-item"><span class="rw-num-idx">${numMatch[1]}.</span><span class="rw-num-text">${numMatch[2]}</span></div>`;
      }
      return line;
    });

    let joined = htmlLines.join("\n");
    joined = joined.replace(/\n\s*\n/g, '<div class="rw-para-gap"></div>');
    joined = joined.replace(/\n/g, "<br>");
    joined = joined.replace(/^(<br>|<div class="rw-para-gap"><\/div>)+/, "");
    joined = joined.replace(/(<br>|<div class="rw-para-gap"><\/div>)+$/, "");

    // 6. Append luxury Membership CTA Button if message relates to membership
    if (hasMembershipLink) {
      joined += `
        <div class="rw-membership-card">
          <a href="https://rentzy.vn/member-ship/" target="_blank" rel="noopener noreferrer" class="rw-membership-btn" title="Nhấn để xem chi tiết và đăng ký gói thành viên Rentzy">
            <span class="rw-mbtn-left">
              <span class="rw-mbtn-icon">👑</span>
              <span class="rw-mbtn-text">Xem chi tiết &amp; Đăng ký Gói thành viên</span>
            </span>
            <svg class="rw-mbtn-arrow" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M5 12h14M12 5l7 7-7 7" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </a>
        </div>
      `;
    }

    return joined;
  }

  /* ============================================================
     STARTER MENU HTML BUILDER (4 mục chính + mục "Xem thêm")
     ============================================================ */

  function renderChipButton(item) {
    const isUpcoming = item.status === "upcoming";
    const sublineHtml = isUpcoming
      ? `<span class="rw-chip-subline rw-subline-upcoming">Upcoming</span>`
      : `<span class="rw-chip-subline rw-subline-active">Sẵn sàng trải nghiệm</span>`;

    return `
      <button
        type="button"
        class="rw-menu-chip ${isUpcoming ? "rw-chip-is-upcoming" : "rw-chip-is-active"}"
        data-query="${esc(item.query)}"
        data-title="${esc(item.title)}"
        data-upcoming="${isUpcoming ? "true" : "false"}"
      >
        <div class="rw-chip-text-group">
          <div class="rw-chip-title-line">
            <span class="rw-chip-emoji">${item.emoji}</span>
            <span class="rw-chip-label">${esc(item.title)}</span>
          </div>
          ${sublineHtml}
        </div>
        <svg class="rw-chip-arrow" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6z"/>
        </svg>
      </button>
    `;
  }

  function buildStarterMenuHTML() {
    const primaryHtml = PRIMARY_MENU.map(renderChipButton).join("");
    const moreChipsHtml = MORE_MENU.map(renderChipButton).join("");

    const moreToggleHtml = `
      <button
        type="button"
        class="rw-menu-chip rw-chip-toggle-more ${isMoreExpanded ? "rw-more-is-open" : ""}"
        id="rw-btn-more-toggle"
        aria-expanded="${isMoreExpanded ? "true" : "false"}"
        title="${isMoreExpanded ? "Thu gọn danh mục" : "Xem thêm các chủ đề khác"}"
      >
        <div class="rw-chip-text-group">
          <div class="rw-chip-title-line">
            <span class="rw-chip-emoji">${isMoreExpanded ? "📂" : "➕"}</span>
            <span class="rw-chip-label">${isMoreExpanded ? "Thu gọn" : "Xem thêm"}</span>
          </div>
          <span class="rw-chip-subline rw-subline-more">${isMoreExpanded ? "Đóng danh mục" : "5 chủ đề khác"}</span>
        </div>
        <svg class="rw-chip-arrow rw-more-arrow-icon" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/>
        </svg>
      </button>
    `;

    return `
      <div class="rw-starter-primary-grid">
        ${primaryHtml}
        ${moreToggleHtml}
      </div>
      <div class="rw-more-menu-panel ${isMoreExpanded ? "rw-more-panel-open" : ""}" id="rw-more-panel" aria-hidden="${!isMoreExpanded}">
        <div class="rw-more-panel-header">
          <span class="rw-more-panel-title">Chủ đề khác (${MORE_MENU.length}):</span>
        </div>
        <div class="rw-more-grid">
          ${moreChipsHtml}
        </div>
      </div>
    `;
  }

  /* ============================================================
     INITIAL WELCOME BUBBLE HTML
     ============================================================ */

  function buildWelcomeHTML() {
    const occasionsHtml = WELCOME_OCCASIONS.map(
      (item) => `
        <button
          type="button"
          class="rw-welcome-chip"
          data-query="${esc(item.query)}"
          title="${esc(item.label)} (Upcoming)"
        >
          <span class="rw-wchip-label">${esc(item.label)}</span>
          <span class="rw-wchip-badge">Upcoming</span>
        </button>
      `
    ).join("");

    return `
      <div class="rw-welcome-area" id="rw-welcome-card" aria-label="Lời chào Rentzy">
        <div class="rw-msg rw-msg-bot">
          <div class="rw-bot-icon" aria-hidden="true">R</div>
          <div class="rw-msg-content">
            <div class="rw-msg-bubble">
              <div class="rw-welcome-text">
                Chào Nàng, hôm nay Nàng đang tìm trang phục cho dịp nào ạ?
              </div>
              <div class="rw-welcome-options">
                ${occasionsHtml}
              </div>
            </div>
            <span class="rw-msg-time">${now()}</span>
          </div>
        </div>
      </div>
    `;
  }

  /* ============================================================
     CREATE DOM
     ============================================================ */

  function createWidgetDOM() {
    if (document.getElementById("rentzy-widget-root")) {
      return;
    }

    const root = document.createElement("div");
    root.id = "rentzy-widget-root";

    root.innerHTML = `
      <!-- LAUNCHER TOOLTIP -->
      <div class="rw-launcher-tooltip" id="rw-tooltip" role="status" title="Nhấn để trò chuyện cùng Trợ lý thời trang AI">
        <div class="rw-tooltip-shimmer" aria-hidden="true"></div>
        <div class="rw-tooltip-body" id="rw-tooltip-body">
          <span class="rw-tooltip-emoji" aria-hidden="true">😍</span>
          <span class="rw-tooltip-text">Cần hỗ trợ không người đẹp?</span>
        </div>
        <button class="rw-tooltip-close" id="rw-tooltip-close" type="button" aria-label="Đóng thông báo">&times;</button>
      </div>

      <!-- LAUNCHER FAB -->
      <button class="rw-launcher-btn" id="rw-launcher" type="button" aria-label="Mở Trợ lý thời trang AI" aria-expanded="false">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.2L4 17.2V4h16v12z"/>
        </svg>
        <span class="rw-launcher-badge">AI</span>
      </button>

      <!-- CHAT WINDOW -->
      <section
        class="rw-chat-window"
        id="rw-window"
        role="dialog"
        aria-modal="false"
        aria-label="Trợ lý thời trang AI"
        aria-hidden="true"
      >
        <!-- HEADER -->
        <header class="rw-header">
          <div class="rw-header-profile">
            <div class="rw-avatar-wrapper">
              <div class="rw-avatar" aria-hidden="true">R</div>
              <span class="rw-online-dot" title="Đang trực tuyến" aria-label="Đang trực tuyến"></span>
            </div>
            <div class="rw-header-title">
              <h4>Trợ lý thời trang AI</h4>
              <p>Trực tuyến</p>
            </div>
          </div>
          <div class="rw-header-actions">
            <button id="rw-btn-reset" type="button" title="Làm mới cuộc trò chuyện" aria-label="Làm mới cuộc trò chuyện">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/>
              </svg>
            </button>
            <button id="rw-btn-close" type="button" title="Đóng chat" aria-label="Đóng cửa sổ tư vấn">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
              </svg>
            </button>
          </div>
        </header>

        <!-- PERSISTENT QUICK MENU SUB-BAR & ACCORDION -->
        <div class="rw-quick-menu-wrapper" id="rw-quick-menu-wrapper">
          <button
            type="button"
            class="rw-quick-menu-toggle"
            id="rw-quick-menu-toggle"
            title="Ẩn chủ đề nhanh"
            aria-expanded="true"
          >
            <span class="rw-toggle-left">
              <span class="rw-toggle-icon">💬</span>
              <span class="rw-toggle-text">Chủ đề nhanh</span>
            </span>
            <svg class="rw-toggle-chevron" id="rw-toggle-chevron" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/>
            </svg>
          </button>
          <div class="rw-quick-menu-body" id="rw-quick-menu-body">
            <div class="rw-starter-menu" id="rw-starter-menu">
              ${buildStarterMenuHTML()}
            </div>
          </div>
        </div>

        <!-- CONVERSATION STREAM BODY -->
        <main
          class="rw-messages-body"
          id="rw-messages"
          aria-live="polite"
          aria-relevant="additions"
        >
          ${buildWelcomeHTML()}
        </main>

        <!-- FOOTER INPUT -->
        <div class="rw-footer">
          <textarea
            class="rw-input-box"
            id="rw-input"
            placeholder="Nhập câu hỏi cho Rentzy..."
            rows="1"
            autocomplete="off"
            aria-label="Nhập câu hỏi cho Rentzy"
          ></textarea>
          <button class="rw-send-btn" id="rw-send" type="button" aria-label="Gửi tin nhắn">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
            </svg>
          </button>
        </div>

        <div class="rw-footer-brand">
          Powered by <a href="https://rentzy.vn" target="_blank" rel="noopener noreferrer">Rentzy</a> · Fashion AI
        </div>
      </section>
    `;

    document.body.appendChild(root);

    setupEventListeners();

    // Show tooltip after 1.2s delay if not previously dismissed
    const isDismissed = sessionStorage.getItem("rentzy_tooltip_dismissed") === "true";
    if (!isDismissed) {
      setTimeout(() => {
        const tooltipEl = document.getElementById("rw-tooltip");
        if (tooltipEl && !isOpen) {
          tooltipEl.classList.add("rw-show");
        }
      }, 1200);

      // Auto-hide after 35 seconds of inactivity
      tooltipTimer = window.setTimeout(hideTooltip, 35000);
    }
  }

  /* ============================================================
     EVENT LISTENERS SETUP
     ============================================================ */

  function setupEventListeners() {
    const launcher = document.getElementById("rw-launcher");
    const closeBtn = document.getElementById("rw-btn-close");
    const resetBtn = document.getElementById("rw-btn-reset");
    const sendBtn = document.getElementById("rw-send");
    const input = document.getElementById("rw-input");
    const tooltip = document.getElementById("rw-tooltip");
    const tooltipClose = document.getElementById("rw-tooltip-close");
    const quickToggleBtn = document.getElementById("rw-quick-menu-toggle");
    const starterMenu = document.getElementById("rw-starter-menu");

    if (launcher) launcher.addEventListener("click", toggleChat);
    if (closeBtn) closeBtn.addEventListener("click", closeChat);
    if (resetBtn) resetBtn.addEventListener("click", resetChat);
    if (sendBtn) sendBtn.addEventListener("click", handleSend);

    if (input) {
      input.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
          event.preventDefault();
          handleSend();
        }
      });
      input.addEventListener("input", () => autoResize(input));
    }

    if (tooltip) {
      tooltip.addEventListener("click", (event) => {
        if (event.target.closest("#rw-tooltip-close")) return;
        openChat();
      });

      tooltip.addEventListener("mouseenter", () => {
        if (tooltipTimer) {
          clearTimeout(tooltipTimer);
          tooltipTimer = null;
        }
      });
    }

    if (tooltipClose) {
      tooltipClose.addEventListener("click", (event) => {
        event.stopPropagation();
        event.preventDefault();
        hideTooltip();
        sessionStorage.setItem("rentzy_tooltip_dismissed", "true");
      });
    }

    if (quickToggleBtn) {
      quickToggleBtn.addEventListener("click", toggleQuickMenu);
    }

    if (starterMenu) {
      starterMenu.addEventListener("click", handleStarterClick);
    }

    const messages = document.getElementById("rw-messages");
    if (messages) {
      messages.addEventListener("click", handleMessagesClick);
    }

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && isOpen) {
        closeChat();
      }
    });
  }

  /* ============================================================
     PERSISTENT QUICK MENU TOGGLE LOGIC
     ============================================================ */

  function toggleQuickMenu() {
    quickMenuVisible = !quickMenuVisible;
    updateQuickMenuUI();
  }

  function updateQuickMenuUI() {
    const wrapper = document.getElementById("rw-quick-menu-wrapper");
    const toggleBtn = document.getElementById("rw-quick-menu-toggle");
    if (!wrapper || !toggleBtn) return;

    if (quickMenuVisible) {
      wrapper.classList.remove("rw-menu-collapsed");
      toggleBtn.setAttribute("title", "Ẩn chủ đề nhanh");
      toggleBtn.setAttribute("aria-expanded", "true");
    } else {
      wrapper.classList.add("rw-menu-collapsed");
      toggleBtn.setAttribute("title", "Hiện chủ đề nhanh");
      toggleBtn.setAttribute("aria-expanded", "false");
    }
  }

  function updateStarterMenuUI() {
    const starterMenu = document.getElementById("rw-starter-menu");
    if (starterMenu) {
      starterMenu.innerHTML = buildStarterMenuHTML();
    }
  }

  function handleStarterClick(event) {
    const moreToggleBtn = event.target.closest("#rw-btn-more-toggle");
    if (moreToggleBtn) {
      event.preventDefault();
      event.stopPropagation();
      isMoreExpanded = !isMoreExpanded;
      updateStarterMenuUI();
      return;
    }

    const button = event.target.closest(".rw-menu-chip");
    if (!button || isSending) return;

    const query = button.dataset.query;
    if (query) {
      sendMessage(query);
    }
  }

  function handleMessagesClick(event) {
    const welcomeChip = event.target.closest(".rw-welcome-chip");
    if (welcomeChip && !isSending) {
      const query = welcomeChip.dataset.query;
      if (query) {
        sendMessage(query);
      }
      return;
    }

    const pillBtn = event.target.closest(".rw-pill-btn");
    if (pillBtn && !isSending) {
      const opt = pillBtn.dataset.opt || pillBtn.dataset.raw;
      if (opt) {
        sendMessage(opt);
      }
      return;
    }
  }

  /* ============================================================
     TOOLTIP HIDE
     ============================================================ */

  function hideTooltip() {
    if (tooltipTimer) {
      clearTimeout(tooltipTimer);
      tooltipTimer = null;
    }
    const tooltip = document.getElementById("rw-tooltip");
    if (tooltip) {
      tooltip.classList.remove("rw-show");
    }
  }

  /* ============================================================
     AUTO RESIZE INPUT
     ============================================================ */

  function autoResize(element) {
    element.style.height = "36px";
    const height = Math.min(element.scrollHeight, 80);
    element.style.height = `${height}px`;
  }

  function handleSend() {
    const input = document.getElementById("rw-input");
    const text = input.value.trim();

    if (!text || isSending) return;

    input.value = "";
    input.style.height = "36px";

    sendMessage(text);
  }

  /* ============================================================
     OPEN / CLOSE CHAT WIDGET
     ============================================================ */

  function toggleChat() {
    if (isOpen) {
      closeChat();
    } else {
      openChat();
    }
  }

  function openChat() {
    isOpen = true;

    const root = document.getElementById("rentzy-widget-root");
    const windowEl = document.getElementById("rw-window");
    const launcher = document.getElementById("rw-launcher");

    root.classList.add("rw-is-open");
    windowEl.classList.add("rw-open");
    windowEl.setAttribute("aria-hidden", "false");
    launcher.setAttribute("aria-expanded", "true");

    hideTooltip();

    window.setTimeout(() => {
      const input = document.getElementById("rw-input");
      if (input) input.focus();
    }, 180);
  }

  function closeChat() {
    isOpen = false;

    const root = document.getElementById("rentzy-widget-root");
    const windowEl = document.getElementById("rw-window");
    const launcher = document.getElementById("rw-launcher");

    root.classList.remove("rw-is-open");
    windowEl.classList.remove("rw-open");
    windowEl.setAttribute("aria-hidden", "true");
    launcher.setAttribute("aria-expanded", "false");

    launcher.focus();
  }

  /* ============================================================
     RESET CHAT HISTORY
     ============================================================ */

  function resetChat() {
    if (isSending) return;

    isMoreExpanded = false;
    quickMenuVisible = true;
    updateQuickMenuUI();
    updateStarterMenuUI();

    const messages = document.getElementById("rw-messages");
    if (messages) {
      messages.innerHTML = buildWelcomeHTML();
    }

    const input = document.getElementById("rw-input");
    if (input) {
      input.value = "";
      input.style.height = "36px";
      requestAnimationFrame(() => input.focus());
    }
  }

  /* ============================================================
     SCROLL STREAM
     ============================================================ */

  function scrollToBottom() {
    const container = document.getElementById("rw-messages");
    if (!container) return;

    requestAnimationFrame(() => {
      container.scrollTop = container.scrollHeight;
    });
  }

  /* ============================================================
     APPEND USER MESSAGE
     ============================================================ */

  function appendUserMessage(text) {
    const container = document.getElementById("rw-messages");
    if (!container) return;

    const element = document.createElement("div");
    element.className = "rw-msg rw-msg-user";
    element.innerHTML = `
      <div class="rw-msg-content">
        <div class="rw-msg-bubble">
          ${esc(text)}
        </div>
        <span class="rw-msg-time">${now()}</span>
      </div>
    `;

    container.appendChild(element);
    scrollToBottom();
  }

  /* ============================================================
     TYPING INDICATOR
     ============================================================ */

  function showTyping() {
    const container = document.getElementById("rw-messages");
    if (!container) return;

    hideTyping();

    const element = document.createElement("div");
    element.id = "rw-typing";
    element.className = "rw-typing-wrap";
    element.innerHTML = `
      <div class="rw-bot-icon" aria-hidden="true">R</div>
      <div class="rw-typing" aria-label="Rentzy đang trả lời">
        <div class="rw-typing-dot"></div>
        <div class="rw-typing-dot"></div>
        <div class="rw-typing-dot"></div>
      </div>
    `;

    container.appendChild(element);
    scrollToBottom();
  }

  function hideTyping() {
    const element = document.getElementById("rw-typing");
    if (element) {
      element.remove();
    }
  }

  /* ============================================================
     APPEND BOT RESPONSE
     ============================================================ */

  function appendBotResponse(data) {
    hideTyping();

    const container = document.getElementById("rw-messages");
    if (!container) return;

    const element = document.createElement("div");
    element.className = "rw-msg rw-msg-bot";

    const text = renderMarkdown(data.reply_message || "");

    let inner = `
      <div class="rw-bot-icon" aria-hidden="true">R</div>
      <div class="rw-msg-content">
        <div class="rw-msg-bubble">
          <div class="rw-message-text">${text}</div>
    `;

    if (
      data.need_clarification &&
      Array.isArray(data.suggested_options) &&
      data.suggested_options.length > 0
    ) {
      inner += `
        <div class="rw-quick-replies">
          ${data.suggested_options
          .map((option) => {
            const isUpcoming = /\((?:upcoming|sắp ra mắt)\)|\[(?:upcoming|sắp ra mắt)\]/i.test(option);
            const cleanText = option.replace(/\s*[\(\[](?:upcoming|sắp ra mắt)[\)\]]\s*/gi, "").trim();
            return `
                <button
                  type="button"
                  class="rw-pill-btn ${isUpcoming ? "rw-pill-is-upcoming" : ""}"
                  data-opt="${esc(cleanText)}"
                  data-raw="${esc(option)}"
                  title="${isUpcoming ? "Tính năng sắp ra mắt (Upcoming)" : esc(cleanText)}"
                >
                  <span class="rw-pill-text">${esc(cleanText)}</span>
                  ${isUpcoming ? `<span class="rw-pill-badge">Upcoming</span>` : ""}
                </button>
              `;
          })
          .join("")}
        </div>
      `;
    }

    if (data.suggest_sales) {
      inner += `
        <div class="rw-sales-banner">
          <div class="rw-sales-text">💬 Cần hỗ trợ giữ đồ ngay?</div>
          <a
            href="https://zalo.me/3199663178050331455"
            target="_blank"
            rel="noopener noreferrer"
            class="rw-sales-btn"
          >
            Chat Zalo
          </a>
        </div>
      `;
    }

    inner += `
        </div>
        <span class="rw-msg-time">${now()}</span>
      </div>
    `;

    element.innerHTML = inner;

    element.querySelectorAll(".rw-pill-btn").forEach((button) => {
      button.addEventListener("click", () => {
        if (!isSending) {
          sendMessage(button.dataset.opt || button.dataset.raw);
        }
      });
    });

    container.appendChild(element);
    scrollToBottom();
  }

  /* ============================================================
     SEND MESSAGE TO API
     ============================================================ */

  function sendMessage(text) {
    if (!text || isSending) return;

    isSending = true;

    const sendBtn = document.getElementById("rw-send");
    if (sendBtn) sendBtn.disabled = true;

    appendUserMessage(text);
    showTyping();

    fetch(`${apiBaseUrl}/api/v1/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json"
      },
      body: JSON.stringify({
        session_id: SESSION_ID,
        message: text
      })
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        appendBotResponse(data);
      })
      .catch(() => {
        appendBotResponse({
          reply_message:
            "Dạ hiện tại kết nối máy chủ đang bận. Nàng vui lòng thử lại sau hoặc nhắn trực tiếp Zalo nhé!",
          suggest_sales: true
        });
      })
      .finally(() => {
        isSending = false;
        if (sendBtn) sendBtn.disabled = false;
      });
  }

  /* ============================================================
     INITIALIZATION
     ============================================================ */

  function initialize() {
    createWidgetDOM();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialize, { once: true });
  } else {
    initialize();
  }
})();