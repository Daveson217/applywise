import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const priorityConfig: Record<string, { label: string; className: string }> = {
  high: { label: "High", className: "border-red-500/50 text-red-500" },
  medium: {
    label: "Medium",
    className: "border-yellow-500/50 text-yellow-500",
  },
  low: { label: "Low", className: "border-green-500/50 text-green-500" },
};

interface PriorityBadgeProps {
  priority: string;
}

export function PriorityBadge({ priority }: PriorityBadgeProps) {
  const config = priorityConfig[priority] || {
    label: priority,
    className: "",
  };

  return (
    <Badge variant="outline" className={cn("font-medium", config.className)}>
      {config.label}
    </Badge>
  );
}
