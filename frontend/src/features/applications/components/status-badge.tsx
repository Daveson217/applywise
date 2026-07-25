import { Badge } from "@/components/ui/badge";
import { STATUS_COLORS, STATUS_LABELS } from "@/lib/constants";

interface StatusBadgeProps {
  status: string;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  return (
    <Badge
      className={`${STATUS_COLORS[status] || "bg-muted"} border-transparent text-white`}
    >
      {STATUS_LABELS[status] || status}
    </Badge>
  );
}
