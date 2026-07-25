import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useDailyCounts } from "@/features/applications/hooks";
import { cn } from "@/lib/utils";
import { format, startOfWeek, subDays } from "date-fns";

function getIntensityClass(count: number): string {
  if (count === 0) return "bg-muted/40";
  if (count === 1) return "bg-primary/30";
  if (count === 2) return "bg-primary/50";
  if (count <= 4) return "bg-primary/70";
  return "bg-primary";
}

export function ActivityHeatmap() {
  const { data, isLoading } = useDailyCounts(365);

  // Build 365 daily cells aligned to weeks
  const today = new Date();
  const start = startOfWeek(subDays(today, 364), { weekStartsOn: 0 });

  const countsMap = new Map<string, number>();
  (data || []).forEach((item) => {
    countsMap.set(item.date, item.count);
  });

  const weeks: { date: Date; count: number }[][] = [];
  let cursor = new Date(start);

  for (let w = 0; w < 53; w++) {
    const week: { date: Date; count: number }[] = [];
    for (let d = 0; d < 7; d++) {
      const dateStr = format(cursor, "yyyy-MM-dd");
      week.push({ date: new Date(cursor), count: countsMap.get(dateStr) || 0 });
      cursor.setDate(cursor.getDate() + 1);
    }
    weeks.push(week);
    if (cursor > today) break;
  }

  const total = (data || []).reduce((sum, item) => sum + item.count, 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">
          Activity Heatmap{" "}
          <span className="text-sm font-normal text-muted-foreground">
            ({total} applications in the past year)
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="h-24 animate-pulse rounded bg-muted/40" />
        ) : (
          <div className="space-y-2">
            <div className="flex gap-[3px] overflow-x-auto pb-2">
              {weeks.map((week, wi) => (
                <div key={wi} className="flex flex-col gap-[3px]">
                  {week.map((day, di) => (
                    <div
                      key={di}
                      className={cn(
                        "h-3 w-3 rounded-sm",
                        getIntensityClass(day.count)
                      )}
                      title={`${format(day.date, "MMM d, yyyy")}: ${day.count} ${
                        day.count === 1 ? "application" : "applications"
                      }`}
                    />
                  ))}
                </div>
              ))}
            </div>
            <div className="flex items-center justify-end gap-2 text-xs text-muted-foreground">
              <span>Less</span>
              <div className="h-3 w-3 rounded-sm bg-muted/40" />
              <div className="h-3 w-3 rounded-sm bg-primary/30" />
              <div className="h-3 w-3 rounded-sm bg-primary/50" />
              <div className="h-3 w-3 rounded-sm bg-primary/70" />
              <div className="h-3 w-3 rounded-sm bg-primary" />
              <span>More</span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
