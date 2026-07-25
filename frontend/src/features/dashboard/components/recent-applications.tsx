import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StatusBadge } from "@/features/applications/components/status-badge";
import type { Application } from "@/types/application";
import { formatDistanceToNow } from "date-fns";

interface RecentApplicationsProps {
  applications: Application[];
}

export function RecentApplications({
  applications,
}: RecentApplicationsProps) {
  const recent = applications.slice(0, 5);

  if (recent.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Recent Applications</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            No applications yet. Add your first one!
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Recent Applications</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {recent.map((app) => (
          <div
            key={app.id}
            className="flex items-center justify-between rounded-md p-2 transition-colors hover:bg-muted/50"
          >
            <div>
              <p className="font-medium">{app.company}</p>
              <p className="text-sm text-muted-foreground">{app.role}</p>
            </div>
            <div className="flex items-center gap-3">
              <StatusBadge status={app.status} />
              <span className="text-xs text-muted-foreground">
                {formatDistanceToNow(new Date(app.updated_at), {
                  addSuffix: true,
                })}
              </span>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
