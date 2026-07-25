import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { Application } from "@/types/application";
import { isWithinInterval, startOfWeek, subWeeks } from "date-fns";
import { Sparkles, TrendingUp } from "lucide-react";
import { useEffect, useState } from "react";

const STORAGE_KEY = "applywise-last-review";

function getWeekStart(date: Date): string {
  return startOfWeek(date, { weekStartsOn: 1 }).toISOString().split("T")[0];
}

interface WeeklyReviewModalProps {
  applications: Application[];
  weeklyGoal: number;
}

export function WeeklyReviewModal({
  applications,
  weeklyGoal,
}: WeeklyReviewModalProps) {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const lastShown = localStorage.getItem(STORAGE_KEY);
    const currentWeek = getWeekStart(new Date());
    if (lastShown !== currentWeek) {
      // Wait a moment for page to settle
      const timer = setTimeout(() => setOpen(true), 800);
      return () => clearTimeout(timer);
    }
  }, []);

  function handleClose() {
    localStorage.setItem(STORAGE_KEY, getWeekStart(new Date()));
    setOpen(false);
  }

  // Compute last week stats
  const lastWeekStart = startOfWeek(subWeeks(new Date(), 1), {
    weekStartsOn: 1,
  });
  const lastWeekEnd = startOfWeek(new Date(), { weekStartsOn: 1 });

  const lastWeekApps = applications.filter((a) =>
    a.applied_date
      ? isWithinInterval(new Date(a.applied_date), {
          start: lastWeekStart,
          end: lastWeekEnd,
        })
      : false
  );

  const interviews = applications.filter((a) =>
    ["oa_assessment", "phone_screen", "interview", "final_round"].includes(
      a.status
    )
  ).length;

  const hitGoal = lastWeekApps.length >= weeklyGoal;
  const percentage = Math.min(100, (lastWeekApps.length / weeklyGoal) * 100);

  return (
    <Dialog open={open} onOpenChange={(o) => !o && handleClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            Your Weekly Review
          </DialogTitle>
          <DialogDescription>
            Here's how last week went.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="rounded-lg border bg-card p-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">
                Applications Submitted
              </span>
              <span className="text-2xl font-bold">
                {lastWeekApps.length}
                <span className="text-base font-normal text-muted-foreground">
                  /{weeklyGoal}
                </span>
              </span>
            </div>
            <div className="mt-2 h-2 overflow-hidden rounded-full bg-muted">
              <div
                className="h-full bg-primary transition-all"
                style={{ width: `${percentage}%` }}
              />
            </div>
          </div>

          <div className="rounded-lg border bg-card p-4">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-primary" />
              <span className="text-sm">
                <span className="font-medium">{interviews}</span> active
                interviews in your pipeline
              </span>
            </div>
          </div>

          <div className="rounded-lg bg-primary/10 p-4 text-sm">
            {hitGoal ? (
              <p>
                <strong>Crushing it!</strong> You hit your weekly goal of{" "}
                {weeklyGoal} applications. Keep the momentum going.
              </p>
            ) : lastWeekApps.length > 0 ? (
              <p>
                You applied to {lastWeekApps.length} of {weeklyGoal} target this
                week. Try to add{" "}
                <strong>{weeklyGoal - lastWeekApps.length} more</strong> this
                week to stay on track.
              </p>
            ) : (
              <p>
                Last week was quiet. Let's aim for{" "}
                <strong>{weeklyGoal} applications</strong> this week. Small
                consistent action beats sporadic bursts.
              </p>
            )}
          </div>
        </div>

        <Button onClick={handleClose} className="w-full">
          Got it — let's go
        </Button>
      </DialogContent>
    </Dialog>
  );
}
