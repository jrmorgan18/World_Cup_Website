(function () {
  const root = document.getElementById("wcg-chat");
  if (!root) return;

  const workerUrl = root.dataset.workerUrl;
  const launcher = root.querySelector(".wcg-chat-launcher");
  const panel = root.querySelector(".wcg-chat-panel");
  const closeBtn = root.querySelector(".wcg-chat-close");
  const messagesEl = root.querySelector(".wcg-chat-messages");
  const form = root.querySelector(".wcg-chat-form");
  const input = root.querySelector(".wcg-chat-input");
  const sendBtn = root.querySelector(".wcg-chat-send");

  const STORAGE_KEY = "wcg-chat-history-v1";
  let history = loadHistory();
  let busy = false;

  if (history.length === 0) {
    pushMessage(
      "assistant",
      "Hi — I can answer questions about anything published on this site. Try asking about a team's group, a player's role, or how a country qualified."
    );
  } else {
    history.forEach((m) => renderMessage(m.role, m.content));
  }

  launcher.addEventListener("click", () => togglePanel(true));
  closeBtn.addEventListener("click", () => togglePanel(false));

  input.addEventListener("input", autoresize);
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      form.requestSubmit();
    }
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text || busy) return;
    input.value = "";
    autoresize();
    await send(text);
  });

  function togglePanel(open) {
    panel.hidden = !open;
    launcher.setAttribute("aria-expanded", String(open));
    launcher.classList.toggle("wcg-chat-launcher--open", open);
    if (open) {
      setTimeout(() => input.focus(), 50);
      scrollToBottom();
    }
  }

  function autoresize() {
    input.style.height = "auto";
    input.style.height = Math.min(input.scrollHeight, 140) + "px";
  }

  async function send(text) {
    busy = true;
    sendBtn.disabled = true;
    pushMessage("user", text);
    const typing = renderTyping();

    try {
      const res = await fetch(workerUrl, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ message: text, history: history.slice(0, -1) }),
      });
      typing.remove();
      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}));
        pushMessage("assistant", `Sorry — something went wrong (${res.status}). ${errBody.error || ""}`.trim());
      } else {
        const data = await res.json();
        pushMessage("assistant", data.reply || "(empty reply)");
      }
    } catch (err) {
      typing.remove();
      pushMessage("assistant", "Network error — please try again in a moment.");
    } finally {
      busy = false;
      sendBtn.disabled = false;
      input.focus();
    }
  }

  function pushMessage(role, content) {
    history.push({ role, content });
    history = history.slice(-20);
    saveHistory();
    renderMessage(role, content);
  }

  function renderMessage(role, content) {
    const wrap = document.createElement("div");
    wrap.className = `wcg-msg wcg-msg--${role}`;
    const bubble = document.createElement("div");
    bubble.className = "wcg-msg-bubble";
    bubble.innerHTML = renderMarkdown(content);
    wrap.appendChild(bubble);
    messagesEl.appendChild(wrap);
    scrollToBottom();
    return wrap;
  }

  function renderTyping() {
    const wrap = document.createElement("div");
    wrap.className = "wcg-msg wcg-msg--assistant wcg-msg--typing";
    wrap.innerHTML =
      '<div class="wcg-msg-bubble"><span class="wcg-dot"></span><span class="wcg-dot"></span><span class="wcg-dot"></span></div>';
    messagesEl.appendChild(wrap);
    scrollToBottom();
    return wrap;
  }

  function scrollToBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function loadHistory() {
    try {
      const raw = sessionStorage.getItem(STORAGE_KEY);
      if (!raw) return [];
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  }

  function saveHistory() {
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(history));
    } catch {}
  }

  function escapeHtml(s) {
    return s
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function renderMarkdown(text) {
    let s = escapeHtml(text);
    s = s.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    s = s.replace(/(?<!\*)\*([^*\n]+)\*(?!\*)/g, "<em>$1</em>");
    s = s.replace(/`([^`]+)`/g, "<code>$1</code>");
    const blocks = s.split(/\n{2,}/).map((block) => {
      const lines = block.split("\n");
      if (lines.every((l) => /^\s*[-*]\s+/.test(l))) {
        const items = lines.map((l) => `<li>${l.replace(/^\s*[-*]\s+/, "")}</li>`).join("");
        return `<ul>${items}</ul>`;
      }
      if (lines.every((l) => /^\s*\d+\.\s+/.test(l))) {
        const items = lines.map((l) => `<li>${l.replace(/^\s*\d+\.\s+/, "")}</li>`).join("");
        return `<ol>${items}</ol>`;
      }
      return `<p>${lines.join("<br>")}</p>`;
    });
    return blocks.join("");
  }
})();
