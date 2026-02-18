import Markdown from "react-markdown";
import type { ChatMessage } from "@/types";

interface Props {
  message: ChatMessage;
}

export function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <div className={`mb-3 flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[70%] rounded-xl px-4 py-3 text-sm leading-relaxed ${
          isUser
            ? "bg-primary text-primary-foreground"
            : "bg-secondary text-secondary-foreground"
        }`}
      >
        {isUser ? (
          <span className="whitespace-pre-wrap">{message.content || "..."}</span>
        ) : (
          <div className="prose prose-sm prose-invert max-w-none">
            <Markdown>{message.content || "..."}</Markdown>
          </div>
        )}
      </div>
    </div>
  );
}
