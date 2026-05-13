/** @returns {string} API root without trailing slash, or '' for same-origin */
function apiBase() {
  const meta = document.querySelector('meta[name="api-base"]');
  const c = meta instanceof HTMLMetaElement ? meta.content.trim() : "";
  return c ? c.replace(/\/+$/, "") : "";
}

/** @param {string} path e.g. /chat */
function apiUrl(path) {
  const b = apiBase();
  return b ? b + path : path;
}

const threadEl = document.getElementById("thread");
const formEl = document.getElementById("form");
const inputEl = document.getElementById("input");
const sendBtn = document.getElementById("sendBtn");
const clearBtn = document.getElementById("clearBtn");
const healthPill = document.getElementById("healthPill");
const tplMsg = document.getElementById("tplMsg");

/** @type {{ role: string, content: string, recommendations?: object[], end_of_conversation?: boolean }[]} */
let messages = [];

async function pingHealth() {
  if (location.protocol === "file:" && !apiBase()) {
    healthPill.textContent = "Open via server (not this file)";
    healthPill.title =
      "Start: python run_api.py then open http://127.0.0.1:8080 — or set meta api-base to your API URL.";
    healthPill.className = "pill bad";
    return;
  }
  try {
    const r = await fetch(apiUrl("/health"), { method: "GET" });
    if (!r.ok) throw new Error("bad status");
    healthPill.textContent = "API ready";
    healthPill.className = "pill ok";
  } catch {
    healthPill.textContent = "API unreachable";
    healthPill.className = "pill bad";
  }
}

function scrollBottom() {
  threadEl.scrollTop = threadEl.scrollHeight;
}

/**
 * @param {'user' | 'assistant' | 'system'} role
 * @param {string} content
 * @param {{ recommendations?: object[], typing?: boolean } | undefined} opts
 */
function appendBubble(role, content, opts) {
  const node = tplMsg.content.cloneNode(true);
  const article = /** @type {HTMLElement} */ (node.querySelector(".msg"));
  const meta = /** @type {HTMLElement} */ (node.querySelector(".msg-meta"));
  const body = /** @type {HTMLElement} */ (node.querySelector(".msg-body"));

  article.classList.add(role);
  meta.textContent = role === "user" ? "You" : role === "assistant" ? "Assistant" : "System";

  body.textContent = content;

  if (opts?.typing) {
    article.classList.add("typing");
  }

  if (opts?.recommendations && opts.recommendations.length) {
    const wrap = document.createElement("div");
    wrap.className = "recs";
    wrap.innerHTML = `<div class="recs-head">Catalog matches (${opts.recommendations.length})</div>`;
    opts.recommendations.forEach((rec) => {
      const a = document.createElement("a");
      a.className = "rec-card";
      a.href = rec.url;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      a.innerHTML = `
        <div class="rec-name"></div>
        <div class="rec-meta"></div>
        <div class="rec-link"></div>`;
      a.querySelector(".rec-name").textContent = rec.name || "Assessment";
      a.querySelector(".rec-meta").textContent = rec.test_type
        ? `Type: ${rec.test_type}`
        : "";
      a.querySelector(".rec-link").textContent = rec.url || "";
      wrap.appendChild(a);
    });
    article.appendChild(wrap);
  }

  threadEl.appendChild(article);
  scrollBottom();
  return article;
}

function renderEmptyHint() {
  threadEl.innerHTML = "";
  appendBubble(
    "assistant",
    "Hi — I help you pick SHL assessments from your catalog.\n\n" +
      "Try pasting part of a job description, comparing two named products (e.g. personality vs ability), or saying what to change in your shortlist.",
    {}
  );
}

function setBusy(busy) {
  sendBtn.disabled = busy;
  inputEl.disabled = busy;
}

clearBtn.addEventListener("click", () => {
  messages = [];
  renderEmptyHint();
  inputEl.focus();
});

formEl.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = inputEl.value.trim();
  if (!text) return;

  appendBubble("user", text, {});
  messages.push({ role: "user", content: text });
  inputEl.value = "";
  setBusy(true);

  let typingBubble = appendBubble("assistant", "Thinking…", { typing: true });

  try {
    const payload = {
      messages: messages.map(({ role, content }) => ({ role, content })),
    };
    const res = await fetch(apiUrl("/chat"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    typingBubble.remove();

    if (!res.ok) {
      const errTxt = await res.text();
      throw new Error(errTxt || res.statusText);
    }

    const data = await res.json();
    const reply =
      typeof data.reply === "string" ? data.reply : JSON.stringify(data, null, 2);

    messages.push({
      role: "assistant",
      content: reply,
      recommendations: data.recommendations || [],
      end_of_conversation: data.end_of_conversation,
    });

    appendBubble("assistant", reply, {
      recommendations: data.recommendations || [],
    });
  } catch (err) {
    typingBubble.remove();
    const msg = err instanceof Error ? err.message : String(err);
    appendBubble(
      "assistant",
      "Something went wrong calling /chat:\n\n" + msg,
      {}
    );
  } finally {
    setBusy(false);
    scrollBottom();
  }
});

pingHealth();
renderEmptyHint();
inputEl.focus();
