import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { AlertTriangle, ExternalLink } from "lucide-react";
import type { ProblematicDive } from "@/types";

interface Props {
  dive: ProblematicDive;
  rank: number;
}

export function ProblematicDiveCard({ dive, rank }: Props) {
  return (
    <Card className="border-danger/30">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-danger/20 text-sm font-bold text-danger">
            {rank}
          </div>
          <div className="flex-1">
            <CardTitle className="text-base">Dive #{dive.dive_number}</CardTitle>
            <p className="text-xs text-muted-foreground">
              Danger score: {dive.danger_score.toFixed(1)}
            </p>
          </div>
          <AlertTriangle className="h-5 w-5 text-danger" />
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Key stats */}
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div>
            <span className="text-muted-foreground">Max depth: </span>
            <span className="font-medium">{dive.features.max_depth.toFixed(1)}m</span>
          </div>
          <div>
            <span className="text-muted-foreground">Max ascent: </span>
            <span className="font-medium">
              {dive.features.max_ascend_speed.toFixed(1)} m/min
            </span>
          </div>
          <div>
            <span className="text-muted-foreground">Min NDL: </span>
            <span className="font-medium">{dive.features.min_ndl.toFixed(0)} min</span>
          </div>
          <div>
            <span className="text-muted-foreground">SAC rate: </span>
            <span className="font-medium">
              {dive.features.sac_rate.toFixed(1)} L/min
            </span>
          </div>
        </div>

        {/* Issue badges */}
        <div className="flex flex-wrap gap-1.5">
          {dive.issues.map((issue) => (
            <Badge key={issue} variant="destructive" className="text-xs">
              {issue}
            </Badge>
          ))}
        </div>

        {/* DAN issue notes with links */}
        {dive.dan_notes.length > 0 && (
          <>
            <Separator />
            <div className="space-y-2.5">
              {dive.dan_notes.map((note) => (
                <div key={note.issue} className="space-y-1">
                  <p className="text-xs leading-relaxed text-muted-foreground">
                    {note.relevance}
                  </p>
                  <a
                    href={note.search_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
                  >
                    Read DAN incidents
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </div>
              ))}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
