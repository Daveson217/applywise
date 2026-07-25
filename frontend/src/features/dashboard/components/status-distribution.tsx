import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { STATUS_LABELS } from "@/lib/constants";
import type { Application } from "@/types/application";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

const COLORS: Record<string, string> = {
  saved: "#6B7280",
  applied: "#3B82F6",
  oa_assessment: "#8B5CF6",
  phone_screen: "#06B6D4",
  interview: "#F59E0B",
  final_round: "#F97316",
  offer_received: "#10B981",
  accepted: "#059669",
  rejected: "#EF4444",
  withdrawn: "#9CA3AF",
  ghosted: "#6B7280",
};

interface StatusDistributionProps {
  applications: Application[];
}

export function StatusDistribution({
  applications,
}: StatusDistributionProps) {
  const counts = applications.reduce(
    (acc, app) => {
      acc[app.status] = (acc[app.status] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  const data = Object.entries(counts).map(([status, count]) => ({
    name: STATUS_LABELS[status] || status,
    value: count,
    status,
  }));

  if (data.length === 0) {
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Status Distribution</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={250}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={90}
              paddingAngle={2}
              dataKey="value"
            >
              {data.map((entry) => (
                <Cell
                  key={entry.status}
                  fill={COLORS[entry.status] || "#6B7280"}
                />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(var(--card))",
                borderColor: "hsl(var(--border))",
                borderRadius: "8px",
                color: "hsl(var(--foreground))",
              }}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="mt-2 flex flex-wrap justify-center gap-3">
          {data.map((entry) => (
            <div key={entry.status} className="flex items-center gap-1.5">
              <div
                className="h-2.5 w-2.5 rounded-full"
                style={{
                  backgroundColor: COLORS[entry.status] || "#6B7280",
                }}
              />
              <span className="text-xs text-muted-foreground">
                {entry.name} ({entry.value})
              </span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
