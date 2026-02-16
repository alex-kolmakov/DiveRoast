import { useState, useRef, useEffect } from "react";
import { useChat } from "../hooks/useChat";
import { MessageBubble } from "./MessageBubble";

interface Props {
  sessionId: string | null;
}

export function ChatInterface({ sessionId }: Props) {
  const { messages, isLoading, sendMessage } = useChat(sessionId);
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    sendMessage(input.trim());
    setInput("");
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        backgroundColor: "#0f172a",
      }}
    >
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "16px",
        }}
      >
        {messages.length === 0 && (
          <div
            style={{
              textAlign: "center",
              color: "#64748b",
              marginTop: "40%",
            }}
          >
            <p style={{ fontSize: "24px" }}>
              Upload a dive log and start chatting
            </p>
            <p style={{ fontSize: "14px" }}>
              DiveRoast will analyze your dives and roast your questionable
              decisions
            </p>
          </div>
        )}
        {messages.map((msg, i) => (
          <MessageBubble key={i} message={msg} />
        ))}
        <div ref={messagesEndRef} />
      </div>

      <form
        onSubmit={handleSubmit}
        style={{
          display: "flex",
          padding: "16px",
          gap: "8px",
          borderTop: "1px solid #1e293b",
        }}
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={
            sessionId
              ? "Ask about your dives..."
              : "Upload a dive log first..."
          }
          disabled={!sessionId}
          style={{
            flex: 1,
            padding: "12px 16px",
            borderRadius: "8px",
            border: "1px solid #334155",
            backgroundColor: "#1e293b",
            color: "#f8fafc",
            fontSize: "14px",
            outline: "none",
          }}
        />
        <button
          type="submit"
          disabled={!sessionId || isLoading || !input.trim()}
          style={{
            padding: "12px 24px",
            borderRadius: "8px",
            border: "none",
            backgroundColor:
              sessionId && !isLoading ? "#2563eb" : "#334155",
            color: "#f8fafc",
            cursor:
              sessionId && !isLoading ? "pointer" : "not-allowed",
            fontSize: "14px",
            fontWeight: "bold",
          }}
        >
          {isLoading ? "..." : "Send"}
        </button>
      </form>
    </div>
  );
}
