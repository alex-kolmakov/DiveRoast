import { Waves } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { UploadResponse } from "@/types";

interface Props {
  uploadResponse: UploadResponse | null;
}

export function AnalyzingScreen({ uploadResponse }: Props) {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-8 px-4">
      {/* Animated wave spinner */}
      <div className="relative">
        <div className="h-20 w-20 animate-spin rounded-full border-4 border-muted border-t-primary" style={{ animationDuration: "2s" }} />
        <Waves className="absolute inset-0 m-auto h-8 w-8 text-primary animate-pulse" />
      </div>

      <div className="text-center">
        <h2 className="text-2xl font-semibold">Analyzing your dives...</h2>
        <p className="mt-2 text-muted-foreground">
          Crunching numbers, checking safety thresholds, and preparing your roast
        </p>
      </div>

      {/* Show upload data immediately */}
      {uploadResponse && (
        <Card className="w-full max-w-md">
          <CardContent className="pt-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Dives loaded</p>
                <p className="text-3xl font-bold text-primary">{uploadResponse.dive_count}</p>
              </div>
              <div className="flex flex-wrap justify-end gap-1.5">
                {uploadResponse.dive_numbers.slice(0, 8).map((num) => (
                  <Badge key={num} variant="secondary" className="text-xs">
                    #{num}
                  </Badge>
                ))}
                {uploadResponse.dive_numbers.length > 8 && (
                  <Badge variant="secondary" className="text-xs">
                    +{uploadResponse.dive_numbers.length - 8} more
                  </Badge>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
