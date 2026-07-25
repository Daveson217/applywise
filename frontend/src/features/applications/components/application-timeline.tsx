import { Skeleton } from "@/components/ui/skeleton";
import { STATUS_LABELS } from "@/lib/constants";
import { format } from "date-fns";
import {
  ArrowRight,
  CheckCircle,
  FileEdit,
  Pencil,
  PlusCircle,
} from "lucide-react";

import { useApplicationActivity } from "../hooks";

const EVENT_ICONS: Record<string, typeof PlusCircle> = {
  created: PlusCircle,
  status_change: ArrowRight,
  note_added: Pencil,
  updated: FileEdit,
  follow_up_set: CheckCircle,
};

const EVENT_LABELS: Record<string, string> = {
  created: "Application created",
  status_change: "Status changed",
  note_added: "Note added",
  updated: "Updated",
  follow_up_set: "Follow-up set",
};

interface ApplicationTimelineProps {
  applicationId: number;
}

export function ApplicationTimeline({
  applicationId,
}: ApplicationTimelineProps) {
  const { data, isLoading } = useApplicationActivity(applicationId);

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    );
  }

  const activities = data?.results || [];

  if (activities.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-muted-foreground">
        No activity recorded yet.
      </p>
    );
  }

  return (
    <ol className="relative space-y-4 border-l border-border pl-6">
      {activities.map((activity) => {
        const Icon = EVENT_ICONS[activity.event_type] || PlusCircle;
        const label = EVENT_LABELS[activity.event_type] || activity.event_type;
        return (
          <li key={activity.id} className="relative">
            <div className="absolute -left-[1.95rem] flex h-6 w-6 items-center justify-center rounded-full bg-primary/10 ring-4 ring-background">
              <Icon className="h-3 w-3 text-primary" />
            </div>
            <div className="rounded-lg border bg-card p-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">{label}</span>
                <span className="text-xs text-muted-foreground">
                  {format(new Date(activity.timestamp), "MMM d, yyyy h:mm a")}
                </span>
              </div>
              {activity.event_type === "status_change" && (
                <p className="mt-1 text-xs text-muted-foreground">
                  <span className="capitalize">
                    {STATUS_LABELS[activity.old_value] || activity.old_value}
                  </span>
                  <ArrowRight className="mx-1 inline h-3 w-3" />
                  <span className="font-medium capitalize text-foreground">
                    {STATUS_LABELS[activity.new_value] || activity.new_value}
                  </span>
                </p>
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
