import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MessageSquare } from "lucide-react";
import type { ChatMessage } from "@/types";

interface Props {
  messages: ChatMessage[];
  isLoading: boolean;
}

export function AgentRoastSummary({ messages, isLoading }: Props) {
  const firstAssistantMsg = messages.find((m) => m.role === "assistant");

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <MessageSquare className="h-4 w-4" />
          Agent Roast
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading && !firstAssistantMsg?.content ? (
          <div className="flex items-center gap-2 text-muted-foreground">
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-muted border-t-primary" />
            <span className="text-sm">Generating roast...</span>
          </div>
        ) : firstAssistantMsg?.content ? (
          <p className="whitespace-pre-wrap text-sm leading-relaxed">
            {firstAssistantMsg.content}
          </p>
        ) : (
          <p className="text-sm text-muted-foreground">
            Waiting for the agent to roast your dives...
          </p>
        )}
      </CardContent>
    </Card>
  );
}
