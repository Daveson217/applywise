import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Application } from "@/types/application";
import { format, startOfWeek, subWeeks } from "date-fns";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface ActivityChartProps {
  applications: Application[];
}

export function ActivityChart({ applications }: ActivityChartProps) {
  const now = new Date();
  const weeks = Array.from({ length: 12 }, (_, i) => {
    const weekStart = startOfWeek(subWeeks(now, 11 - i), { weekStartsOn: 1 });
    return {
      week: format(weekStart, "MMM d"),
      count: 0,
    };
  });

  for (const app of applications) {
    const created = new Date(app.created_at);
    for (let i = 0; i < weeks.length; i++) {
      const weekStart = startOfWeek(subWeeks(now, 11 - i), {
        weekStartsOn: 1,
      });
      const weekEnd = new Date(weekStart);
      weekEnd.setDate(weekEnd.getDate() + 7);
      if (created >= weekStart && created < weekEnd) {
        weeks[i].count++;
        break;
      }
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Application Activity</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={250}>
          <AreaChart data={weeks}>
            <defs>
              <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="hsl(var(--border))"
            />
            <XAxis
              dataKey="week"
              stroke="hsl(var(--muted-foreground))"
              fontSize={12}
              tickLine={false}
            />
            <YAxis
              stroke="hsl(var(--muted-foreground))"
              fontSize={12}
              tickLine={false}
              allowDecimals={false}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(var(--card))",
                borderColor: "hsl(var(--border))",
                borderRadius: "8px",
                color: "hsl(var(--foreground))",
              }}
            />
            <Area
              type="monotone"
              dataKey="count"
              stroke="#3B82F6"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorCount)"
              name="Applications"
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
