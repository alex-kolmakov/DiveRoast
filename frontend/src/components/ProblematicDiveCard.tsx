import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { AlertTriangle, MapPin } from "lucide-react";
import type { ProblematicDive } from "@/types";

interface Props {
  dive: ProblematicDive;
  rank: number;
}

export function ProblematicDiveCard({ dive, rank }: Props) {
  const siteName = dive.features.dive_site_name;
  const hasSite = siteName && siteName !== "N/A";
  const hasCoords = dive.features.latitude != null && dive.features.longitude != null;
  const mapsUrl = hasCoords
    ? `https://www.google.com/maps?q=${dive.features.latitude},${dive.features.longitude}`
    : null;
  const osmEmbedUrl = hasCoords
    ? `https://www.openstreetmap.org/export/embed.html?bbox=${Number(dive.features.longitude) - 1.5},${Number(dive.features.latitude) - 1},${Number(dive.features.longitude) + 1.5},${Number(dive.features.latitude) + 1}&layer=mapnik&marker=${dive.features.latitude},${dive.features.longitude}`
    : null;

  const visibleIssues = dive.issues.filter((i) => i !== "adverse conditions");

  return (
    <Card className="border-danger/30">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-danger/20 text-sm font-bold text-danger">
            {rank}
          </div>
          <div className="flex-1">
            <CardTitle className="text-base">
              Dive #{dive.dive_number}
            </CardTitle>
            {hasSite && (
              <p className="flex items-center gap-1 text-xs text-muted-foreground">
                <MapPin className="h-3 w-3" />
                {siteName}
              </p>
            )}
          </div>
          <AlertTriangle className="h-5 w-5 text-danger" />
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Mini map — scaled up to hide controls, clipped by overflow */}
        {osmEmbedUrl && mapsUrl && (
          <a
            href={mapsUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="relative block h-[90px] overflow-hidden rounded-md border border-border"
          >
            <iframe
              src={osmEmbedUrl}
              className="pointer-events-none absolute left-1/2 top-1/2 h-[250px] w-[500px] origin-center -translate-x-1/2 -translate-y-[55%] scale-[0.75]"
              title={`Map of ${siteName || "dive site"}`}
              loading="lazy"
            />
          </a>
        )}

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

        {/* Issue badges — pick reason first, then others */}
        <div className="flex flex-wrap gap-1.5">
          <Badge variant="destructive" className="text-xs font-semibold">
            {dive.pick_reason}
          </Badge>
          {visibleIssues.map((issue) => (
            <Badge key={issue} variant="outline" className="text-xs text-muted-foreground">
              {issue}
            </Badge>
          ))}
        </div>

        {/* Agent-generated explanation */}
        {dive.summary && (
          <>
            <Separator />
            <p className="text-xs leading-relaxed text-muted-foreground">
              {dive.summary}
            </p>
          </>
        )}
      </CardContent>
    </Card>
  );
}
