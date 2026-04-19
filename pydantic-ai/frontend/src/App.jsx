import { useState, useRef, useEffect } from "react";

const S = {
  app: {
    display: "flex",
    flexDirection: "column",
    height: "100vh",
    overflow: "hidden",
  },
  header: {
    display: "flex",
    alignItems: "center",
    padding: "16px 24px",
    gap: 10,
    flexShrink: 0,
  },
  headerLogo: {
    width: 28,
    height: 28,
    borderRadius: "50%",
    background: "linear-gradient(135deg, #4285f4, #9b72cb, #d96570)",
    flexShrink: 0,
  },
  headerTitle: {
    fontSize: "1.1rem",
    fontWeight: 500,
    background: "linear-gradient(90deg, #4285f4, #9b72cb, #d96570)",
    WebkitBackgroundClip: "text",
    WebkitTextFillColor: "transparent",
    backgroundClip: "text",
  },
  chatArea: {
    flex: 1,
    overflowY: "auto",
    padding: "24px 0",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    scrollbarWidth: "thin",
    scrollbarColor: "#3c3c3c transparent",
  },
  messages: {
    width: "100%",
    maxWidth: 760,
    padding: "0 24px",
    display: "flex",
    flexDirection: "column",
    gap: 24,
    flex: 1,
  },
  emptyState: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    height: "100%",
    gap: 16,
    color: "#9aa0a6",
    paddingTop: 80,
  },
  emptyGem: {
    width: 56,
    height: 56,
    borderRadius: "50%",
    background: "linear-gradient(135deg, #4285f4, #9b72cb, #d96570)",
  },
  emptyText: {
    fontSize: "1rem",
  },
  inputArea: {
    flexShrink: 0,
    padding: "16px 24px 24px",
    display: "flex",
    justifyContent: "center",
  },
  inputWrapper: {
    width: "100%",
    maxWidth: 760,
  },
  inputBox: {
    background: "#1e1f20",
    border: "1px solid #3c3c3c",
    borderRadius: 24,
    padding: "12px 16px",
    display: "flex",
    alignItems: "flex-end",
    gap: 8,
  },
  textarea: {
    flex: 1,
    background: "transparent",
    border: "none",
    outline: "none",
    color: "#e3e3e3",
    fontFamily: "inherit",
    fontSize: "0.95rem",
    lineHeight: 1.5,
    resize: "none",
    minHeight: 24,
    maxHeight: 200,
    padding: 0,
    overflowY: "auto",
  },
  sendBtn: {
    width: 36,
    height: 36,
    borderRadius: "50%",
    border: "none",
    background: "linear-gradient(135deg, #4285f4, #9b72cb)",
    color: "#fff",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0,
  },
  sendBtnDisabled: {
    background: "#3c3c3c",
    cursor: "not-allowed",
    opacity: 0.6,
  },
  inputFooter: {
    textAlign: "center",
    fontSize: "0.75rem",
    color: "#5f6368",
    marginTop: 10,
  },
};

function Message({ role, text }) {
  if (role === "user") {
    return (
      <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end" }}>
        <div style={{
          padding: "12px 18px",
          borderRadius: 20,
          borderBottomRightRadius: 6,
          background: "#2a2b2e",
          color: "#e3e3e3",
          maxWidth: "80%",
          lineHeight: 1.6,
          fontSize: "0.95rem",
          whiteSpace: "pre-wrap",
          wordBreak: "break-word",
        }}>
          {text}
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start", gap: 4 }}>
      {role !== "error" && (
        <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: "0.8rem", color: "#9aa0a6" }}>
          <div style={{ width: 16, height: 16, borderRadius: "50%", background: "linear-gradient(135deg, #4285f4, #9b72cb)", flexShrink: 0 }} />
          langgraph-example
        </div>
      )}
      <div style={{
        color: role === "error" ? "#f28b82" : role === "thinking" ? "#9aa0a6" : "#e3e3e3",
        background: role === "error" ? "#3c1a1a" : "transparent",
        padding: role === "error" ? "12px 18px" : 0,
        borderRadius: role === "error" ? 12 : 0,
        fontStyle: role === "thinking" ? "italic" : "normal",
        lineHeight: 1.6,
        fontSize: "0.95rem",
        whiteSpace: "pre-wrap",
        wordBreak: "break-word",
      }}>
        {text || (role === "thinking" ? "Thinking..." : "")}
      </div>
    </div>
  );
}

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const chatAreaRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    if (chatAreaRef.current) {
      chatAreaRef.current.scrollTop = chatAreaRef.current.scrollHeight;
    }
  }, [messages]);

  function autoResize(e) {
    const el = e.target;
    el.style.height = "24px";
    el.style.height = Math.min(el.scrollHeight, 200) + "px";
  }

  async function send() {
    const message = input.trim();
    if (!message || loading) return;
    setInput("");
    if (textareaRef.current) textareaRef.current.style.height = "24px";
    setLoading(true);

    const userId = Date.now();
    const agentId = userId + 1;
    setMessages((prev) => [
      ...prev,
      { role: "user", text: message, id: userId },
      { role: "thinking", text: "", id: agentId },
    ]);

    try {
      const res = await fetch("/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, thread_id: "react-app", user_id: "user" }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        setMessages((prev) =>
          prev.map((m) =>
            m.id === agentId ? { ...m, role: "error", text: "Blocked: " + (err.detail || res.statusText) } : m
          )
        );
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let accumulated = "";

      setMessages((prev) =>
        prev.map((m) => (m.id === agentId ? { ...m, role: "agent", text: "" } : m))
      );

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        accumulated += decoder.decode(value, { stream: true });
        const current = accumulated;
        setMessages((prev) =>
          prev.map((m) => (m.id === agentId ? { ...m, text: current } : m))
        );
      }

      if (!accumulated.trim()) {
        setMessages((prev) =>
          prev.map((m) => (m.id === agentId ? { ...m, text: "(no response)" } : m))
        );
      }
    } catch (e) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === agentId ? { ...m, role: "error", text: "Error: " + e.message } : m
        )
      );
    } finally {
      setLoading(false);
      textareaRef.current?.focus();
    }
  }

  function handleKey(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  return (
    <div style={S.app}>
      <div style={S.header}>
        <div style={S.headerLogo} />
        <h1 style={S.headerTitle}>langgraph-example</h1>
      </div>

      <div style={S.chatArea} ref={chatAreaRef}>
        <div style={S.messages}>
          {messages.length === 0 ? (
            <div style={S.emptyState}>
              <div style={S.emptyGem} />
              <p style={S.emptyText}>How can I help you today?</p>
            </div>
          ) : (
            messages.map((m) => <Message key={m.id} role={m.role} text={m.text} />)
          )}
        </div>
      </div>

      <div style={S.inputArea}>
        <div style={S.inputWrapper}>
          <div style={S.inputBox}>
            <textarea
              ref={textareaRef}
              style={S.textarea}
              placeholder="Ask me anything..."
              value={input}
              onChange={(e) => { setInput(e.target.value); autoResize(e); }}
              onKeyDown={handleKey}
              disabled={loading}
              rows={1}
            />
            <button
              style={{ ...S.sendBtn, ...(loading ? S.sendBtnDisabled : {}) }}
              onClick={send}
              disabled={loading}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="12" y1="19" x2="12" y2="5" />
                <polyline points="5 12 12 5 19 12" />
              </svg>
            </button>
          </div>
          <div style={S.inputFooter}>langgraph-example can make mistakes. Verify important info.</div>
        </div>
      </div>
    </div>
  );
}
