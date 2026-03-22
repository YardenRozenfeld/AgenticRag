(function () {
  "use strict";

  const token = localStorage.getItem("access_token");
  if (!token) {
    window.location.href = "/";
    return;
  }

  // ── DOM refs ─────────────────────────────────────────────────
  const messagesContainer = document.getElementById("chat-messages");
  const welcomeEl = document.getElementById("chat-welcome");
  const inputEl = document.getElementById("chat-input");
  const sendBtn = document.getElementById("btn-send");
  const threadListEl = document.getElementById("thread-list");
  const topbarTitle = document.getElementById("topbar-title");
  const newChatBtn = document.getElementById("btn-new-chat");
  const signoutBtn = document.getElementById("btn-signout");
  const sidebar = document.getElementById("sidebar");
  const sidebarToggle = document.getElementById("sidebar-toggle");
  const sidebarBackdrop = document.getElementById("sidebar-backdrop");

  let currentThreadId = null;
  let isSending = false;

  // ── Auth header ──────────────────────────────────────────────
  function authHeaders() {
    return {
      "Content-Type": "application/json",
      Authorization: "Bearer " + token,
    };
  }

  function handleAuthError(res) {
    if (res.status === 401) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      localStorage.removeItem("user_id");
      window.location.href = "/";
      return true;
    }
    return false;
  }

  // ── Threads ──────────────────────────────────────────────────
  async function loadThreads() {
    try {
      const res = await fetch("/threads", { headers: authHeaders() });
      if (handleAuthError(res)) return;
      const data = await res.json();
      renderThreads(data.threads || []);
    } catch (err) {
      console.error("Failed to load threads:", err);
    }
  }

  function renderThreads(threads) {
    threadListEl.innerHTML = "";

    if (threads.length === 0) {
      threadListEl.innerHTML =
        '<div style="padding:12px;font-size:0.9rem;color:var(--text-muted);text-align:center;">No conversations yet</div>';
      return;
    }

    threads.forEach((t) => {
      const el = document.createElement("div");
      el.className =
        "thread-item" + (t.thread_id === currentThreadId ? " active" : "");

      const date = new Date(t.created_at);
      const dateStr = date.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
      });

      el.innerHTML =
        '<div class="thread-title">' +
        escapeHtml(t.title) +
        "</div>" +
        '<div class="thread-date">' +
        dateStr +
        "</div>";

      el.addEventListener("click", () => selectThread(t.thread_id, t.title));
      threadListEl.appendChild(el);
    });
  }

  async function selectThread(threadId, title) {
    currentThreadId = threadId;
    topbarTitle.textContent = title || "Conversation";
    clearMessages();
    welcomeEl.classList.add("hidden");
    loadThreads();
    closeSidebar();

    // Load past messages for this thread
    try {
      const res = await fetch("/threads/" + threadId + "/messages", {
        headers: authHeaders(),
      });
      if (handleAuthError(res)) return;
      if (res.ok) {
        const data = await res.json();
        (data.messages || []).forEach((m) => addMessage(m.role, m.content));
      }
    } catch (err) {
      console.error("Failed to load messages:", err);
    }
  }

  function startNewChat() {
    currentThreadId = null;
    topbarTitle.textContent = "New Conversation";
    clearMessages();
    welcomeEl.classList.remove("hidden");
    loadThreads();
    closeSidebar();
    inputEl.focus();
  }

  // ── Messages ─────────────────────────────────────────────────
  function clearMessages() {
    const msgs = messagesContainer.querySelectorAll(".message");
    msgs.forEach((m) => m.remove());
  }

  function addMessage(role, text) {
    welcomeEl.classList.add("hidden");

    const wrapper = document.createElement("div");
    wrapper.className = "message " + role;

    const avatar = document.createElement("div");
    avatar.className = "message-avatar";

    if (role === "bot") {
      avatar.innerHTML =
        '<img src="/static/assets/nexus-logo.svg" alt="Nexus" />';
    } else {
      const userId = localStorage.getItem("user_id") || "";
      avatar.textContent = userId.substring(0, 2).toUpperCase() || "U";
    }

    const bubble = document.createElement("div");
    bubble.className = "message-bubble";
    bubble.textContent = text;

    wrapper.appendChild(avatar);
    wrapper.appendChild(bubble);
    messagesContainer.appendChild(wrapper);

    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    return wrapper;
  }

  function addTypingIndicator() {
    const wrapper = document.createElement("div");
    wrapper.className = "message bot";
    wrapper.id = "typing-indicator";

    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.innerHTML =
      '<img src="/static/assets/nexus-logo.svg" alt="Nexus" />';

    const bubble = document.createElement("div");
    bubble.className = "message-bubble";
    bubble.innerHTML =
      '<div class="typing-indicator"><span></span><span></span><span></span></div>';

    wrapper.appendChild(avatar);
    wrapper.appendChild(bubble);
    messagesContainer.appendChild(wrapper);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  function removeTypingIndicator() {
    const el = document.getElementById("typing-indicator");
    if (el) el.remove();
  }

  // ── Send ─────────────────────────────────────────────────────
  async function sendMessage() {
    const text = inputEl.value.trim();
    if (!text || isSending) return;

    isSending = true;
    sendBtn.disabled = true;
    inputEl.value = "";
    autoResize();

    addMessage("user", text);
    addTypingIndicator();

    try {
      const body = { question: text };
      if (currentThreadId) {
        body.thread_id = currentThreadId;
      }

      const res = await fetch("/chat", {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify(body),
      });

      removeTypingIndicator();

      if (handleAuthError(res)) return;

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        addMessage("bot", "Something went wrong: " + (err.detail || "Unknown error"));
        return;
      }

      const contentType = res.headers.get("content-type") || "";

      if (contentType.includes("text/event-stream")) {
        // Streaming response — read SSE tokens
        const botMsg = addMessage("bot", "");
        const bubble = botMsg.querySelector(".message-bubble");
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });

          const lines = buffer.split("\n");
          buffer = lines.pop(); // keep incomplete line in buffer

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            const payload = JSON.parse(line.slice(6));

            if (payload.token) {
              bubble.textContent += payload.token;
              messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }

            if (payload.done) {
              if (!currentThreadId && payload.thread_id) {
                currentThreadId = payload.thread_id;
                topbarTitle.textContent = text.substring(0, 60);
                loadThreads();
              }
            }
          }
        }
      } else {
        // Non-streaming (e.g. cached) JSON response
        const data = await res.json();

        if (!currentThreadId && data.thread_id) {
          currentThreadId = data.thread_id;
          topbarTitle.textContent = text.substring(0, 60);
          loadThreads();
        }

        addMessage("bot", data.answer);
      }
    } catch (err) {
      removeTypingIndicator();
      addMessage("bot", "Network error. Please check your connection.");
      console.error(err);
    } finally {
      isSending = false;
      updateSendButton();
      inputEl.focus();
    }
  }

  // ── Input handling ───────────────────────────────────────────
  function updateSendButton() {
    sendBtn.disabled = !inputEl.value.trim() || isSending;
  }

  function autoResize() {
    inputEl.style.height = "auto";
    inputEl.style.height = Math.min(inputEl.scrollHeight, 120) + "px";
  }

  inputEl.addEventListener("input", () => {
    updateSendButton();
    autoResize();
  });

  inputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  sendBtn.addEventListener("click", sendMessage);

  // ── Sidebar ──────────────────────────────────────────────────
  function closeSidebar() {
    sidebar.classList.remove("open");
    sidebarBackdrop.classList.remove("visible");
  }

  sidebarToggle.addEventListener("click", () => {
    sidebar.classList.toggle("open");
    sidebarBackdrop.classList.toggle("visible");
  });

  sidebarBackdrop.addEventListener("click", closeSidebar);

  newChatBtn.addEventListener("click", startNewChat);

  // ── Sign out ─────────────────────────────────────────────────
  signoutBtn.addEventListener("click", () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user_id");
    window.location.href = "/";
  });

  // ── Utilities ────────────────────────────────────────────────
  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  // ── Init ─────────────────────────────────────────────────────
  loadThreads();
  inputEl.focus();
})();
