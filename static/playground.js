const chatArea = document.getElementById("chatArea");
const messagesEl = document.getElementById("messages");
const emptyState = document.getElementById("emptyState");
const textarea = document.getElementById("input");
const sendBtn = document.getElementById("sendBtn");

// Auto-resize textarea
textarea.addEventListener("input", () => {
  textarea.style.height = "24px";
  textarea.style.height = Math.min(textarea.scrollHeight, 200) + "px";
});

function scrollToBottom() {
  chatArea.scrollTop = chatArea.scrollHeight;
}

function addMessage(role, text) {
  if (emptyState) emptyState.style.display = "none";

  const msg = document.createElement("div");
  msg.className = "msg " + role;

  if (role === "agent") {
    const label = document.createElement("div");
    label.className = "msg-label";
    label.innerHTML = '<div class="dot"></div> langgraph-example';
    msg.appendChild(label);
  }

  const bubble = document.createElement("div");
  bubble.className = "msg-bubble";
  bubble.textContent = text;
  msg.appendChild(bubble);

  messagesEl.appendChild(msg);
  scrollToBottom();
  return bubble;
}

function handleKey(e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    send();
  }
}

async function send() {
  const message = textarea.value.trim();
  if (!message) return;
  textarea.value = "";
  textarea.style.height = "24px";
  sendBtn.disabled = true;

  addMessage("user", message);
  const agentBubble = addMessage("agent", "");
  agentBubble.parentElement.classList.add("thinking");
  agentBubble.textContent = "Thinking...";

  try {
    const res = await fetch("/chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        thread_id: "playground",
        user_id: "user",
      }),
    });

    agentBubble.parentElement.classList.remove("thinking");

    if (!res.ok) {
      const err = await res.json();
      agentBubble.parentElement.classList.add("error");
      agentBubble.textContent = "Blocked: " + (err.detail || res.statusText);
      return;
    }

    agentBubble.textContent = "";
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      agentBubble.textContent += decoder.decode(value);
      scrollToBottom();
    }
    if (!agentBubble.textContent.trim()) agentBubble.textContent = "(no response)";
  } catch (e) {
    agentBubble.parentElement.classList.add("error");
    agentBubble.textContent = "Error: " + e.message;
  } finally {
    sendBtn.disabled = false;
    textarea.focus();
  }
}
