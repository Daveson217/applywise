import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type { Application } from "@/types/application";
import { Briefcase, CheckCircle, Clock, Target } from "lucide-react";
import { isThisWeek } from "date-fns";

interface StatsCardsProps {
  applications: Application[];
  isLoading: boolean;
  weeklyGoal: number;
}

export function StatsCards({
  applications,
  isLoading,
  weeklyGoal,
}: StatsCardsProps) {
  if (isLoading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i}>
            <CardHeader className="pb-2">
              <Skeleton className="h-4 w-24" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-16" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  const total = applications.length;
  const appliedThisWeek = applications.filter(
    (a) =>
      a.applied_date && isThisWeek(new Date(a.applied_date), { weekStartsOn: 1 })
  ).length;
  const interviewing = applications.filter((a) =>
    ["oa_assessment", "phone_screen", "interview", "final_round"].includes(
      a.status
    )
  ).length;
  const offers = applications.filter((a) =>
    ["offer_received", "accepted"].includes(a.status)
  ).length;

  const stats = [
    {
      title: "Total Applications",
      value: total,
      icon: Briefcase,
    },
    {
      title: "Applied This Week",
      value: `${appliedThisWeek}/${weeklyGoal}`,
      icon: Target,
    },
    {
      title: "Active Interviews",
      value: interviewing,
      icon: Clock,
    },
    {
      title: "Offers",
      value: offers,
      icon: CheckCircle,
    },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {stats.map((stat) => (
        <Card key={stat.title}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {stat.title}
            </CardTitle>
            <stat.icon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stat.value}</div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
