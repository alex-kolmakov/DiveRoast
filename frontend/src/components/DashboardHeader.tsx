import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { MessageCircle, Waves } from "lucide-react";
import type { AggregateStats } from "@/types";

interface Props {
  stats: AggregateStats;
  onToggleChat: () => void;
}

export function DashboardHeader({ stats, onToggleChat }: Props) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <Waves className="h-7 w-7 text-primary" />
        <h1 className="text-2xl font-bold tracking-tight">DiveRoast</h1>
        <Badge variant="secondary" className="text-sm">
          {stats.total_dives} dives
        </Badge>
      </div>
      <Button variant="outline" size="sm" onClick={onToggleChat}>
        <MessageCircle className="mr-2 h-4 w-4" />
        Chat
      </Button>
    </div>
  );
}
