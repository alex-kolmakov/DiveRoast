import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { ChatInterface } from "@/components/ChatInterface";
import type { ChatMessage } from "@/types";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  sessionId: string;
  messages: ChatMessage[];
  isLoading: boolean;
  onSendMessage: (content: string) => void;
}

export function ChatDrawer({
  open,
  onOpenChange,
  sessionId,
  messages,
  isLoading,
  onSendMessage,
}: Props) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="flex w-full flex-col sm:max-w-lg">
        <SheetHeader>
          <SheetTitle>Chat with DiveRoast</SheetTitle>
        </SheetHeader>
        <div className="flex-1 overflow-hidden">
          <ChatInterface
            sessionId={sessionId}
            messages={messages}
            isLoading={isLoading}
            onSendMessage={onSendMessage}
          />
        </div>
      </SheetContent>
    </Sheet>
  );
}
