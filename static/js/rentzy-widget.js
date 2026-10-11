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
    } catch (_) {}
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

  const cssHref = `${assetBaseUrl}/static/css/rentzy-widget.css?v=5.4`;

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
      .rw-pill-btn {
        display: inline-flex !important;
        align-items: center !important;
        gap: 5px !important;
        padding: 4px 10px !important;
        border: 1px solid rgba(197, 160, 89, 0.4) !important;
        border-radius: 999px !important;
        background: #faf5eb !important;
        color: #8c6b2d !important;
        font-size: 11px !important;
        font-weight: 600 !important;
        line-height: 1.3 !important;
        cursor: pointer !important;
        font-family: inherit !important;
      }
      .rw-pill-btn.rw-pill-is-upcoming {
        border-color: rgba(156, 149, 142, 0.35) !important;
        background: #f7f6f4 !important;
        color: #635d57 !important;
      }
      .rw-pill-badge {
        font-size: 8px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.3px !important;
        padding: 1px 4.5px !important;
        border-radius: 3px !important;
        background: rgba(156, 149, 142, 0.18) !important;
        color: #7d766f !important;
        line-height: 1.1 !important;
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
      status: "upcoming"
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
    { label: "💡 Chưa biết, cần tư vấn", query: "Tôi chưa biết chọn trang phục nào, cần tư vấn" }
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

    // 1. Highlight Phone Numbers (Hotline e.g. 0798969040 or 0798 969 040)
    text = text.replace(
      /(?<!\w)(0[2-9]\d{8,9}|0[2-9]\d{1,2}[\s.-]\d{3}[\s.-]\d{3,4}|1[89]00[\s.-]?\d{4,6})(?!\w)/g,
      (match) => {
        const cleanDigits = match.replace(/[\s.-]/g, "");
        return `<a href="tel:${cleanDigits}" class="rw-phone-badge" title="Nhấn để gọi hotline"><svg class="rw-hl-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M6.62 10.79a15.05 15.05 0 006.59 6.59l2.2-2.2a1 1 0 011.02-.24c1.12.37 2.33.57 3.57.57a1 1 0 011 1V20a1 1 0 01-1 1A17 17 0 013 4a1 1 0 011-1h3.5a1 1 0 011 1c0 1.25.2 2.45.57 3.57.1.34.02.72-.25 1.02l-2.2 2.2z"/></svg><span>${match}</span></a>`;
      }
    );

    // 2. Highlight Showroom Address (e.g. 51 đường số 41, phường Khánh Hội, TP. Hồ Chí Minh)
    text = text.replace(
      /(51\s+đường\s+số\s+41[^,\n<]*,\s*(?:phường|p\.)\s*Khánh\s*Hội[^,\n<]*,\s*(?:TP\.\s*Hồ\s*Chí\s*Minh|TPHCM|TP\s+Hồ\s+Chí\s+Minh|Quận\s*4)[^.\n<]*)/gi,
      (match) => {
        return `<span class="rw-address-badge" title="Địa chỉ Showroom Rentzy"><svg class="rw-hl-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5a2.5 2.5 0 110-5 2.5 2.5 0 010 5z"/></svg><span>${match}</span></span>`;
      }
    );

    // 3. Markdown link [Text](URL)
    text = text.replace(
      /\[([^\]]+)\]\((https?:\/\/[^\s\)]+)\)/g,
      '<a href="$2" target="_blank" rel="noopener noreferrer" class="rw-link">$1</a>'
    );

    // 4. Standalone URL (e.g. https://rentzy.vn/member-ship/)
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
      <div class="rw-launcher-tooltip" id="rw-tooltip" role="status">
        <span>Trợ lý thời trang AI</span>
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

    tooltipTimer = window.setTimeout(hideTooltip, 7000);
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

    if (tooltipClose) {
      tooltipClose.addEventListener("click", (event) => {
        event.stopPropagation();
        hideTooltip();
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
            href="https://zalo.me"
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