import type { ChatMessage } from "../types";

interface Props {
  message: ChatMessage;
}

export function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <div
      style={{
        display: "flex",
        justifyContent: isUser ? "flex-end" : "flex-start",
        marginBottom: "12px",
      }}
    >
      <div
        style={{
          maxWidth: "70%",
          padding: "12px 16px",
          borderRadius: "12px",
          backgroundColor: isUser ? "#2563eb" : "#1e293b",
          color: "#f8fafc",
          whiteSpace: "pre-wrap",
          lineHeight: "1.5",
          fontSize: "14px",
        }}
      >
        {message.content || "..."}
      </div>
    </div>
  );
}
