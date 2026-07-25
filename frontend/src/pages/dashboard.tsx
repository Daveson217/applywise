import { useApplications } from "@/features/applications/hooks";
import { ActivityChart } from "@/features/dashboard/components/activity-chart";
import { ActivityHeatmap } from "@/features/dashboard/components/activity-heatmap";
import { RecentApplications } from "@/features/dashboard/components/recent-applications";
import { StatsCards } from "@/features/dashboard/components/stats-cards";
import { StatusDistribution } from "@/features/dashboard/components/status-distribution";
import { WeeklyReviewModal } from "@/features/dashboard/components/weekly-review-modal";
import { useAuthStore } from "@/store/auth-store";

function getGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 17) return "Good afternoon";
  return "Good evening";
}

export function DashboardPage() {
  const user = useAuthStore((s) => s.user);
  const { data, isLoading } = useApplications({ page: 1 });

  const applications = data?.results || [];
  const weeklyGoal = user?.profile?.weekly_goal || 10;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-[family-name:var(--font-display)] text-2xl font-bold">
          {getGreeting()}, {user?.first_name}
        </h1>
        <p className="text-muted-foreground">
          Here&apos;s an overview of your job search.
        </p>
      </div>

      <StatsCards
        applications={applications}
        isLoading={isLoading}
        weeklyGoal={weeklyGoal}
      />

      <ActivityChart applications={applications} />

      <ActivityHeatmap />

      <div className="grid gap-6 lg:grid-cols-2">
        <RecentApplications applications={applications} />
        <StatusDistribution applications={applications} />
      </div>

      <WeeklyReviewModal
        applications={applications}
        weeklyGoal={weeklyGoal}
      />
    </div>
  );
}
