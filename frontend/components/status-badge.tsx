import { Badge } from "@/components/ui/badge";
import { formatStatus } from "@/lib/format";

function statusVariant(value?: string | null) {
  const normalized = (value ?? "").toUpperCase();
  if (normalized.includes("COMPLETED")) return "success";
  if (normalized.includes("FAILED")) return "danger";
  if (normalized.includes("IN_PROGRESS") || normalized.includes("PROCESSING")) return "warning";
  if (normalized.includes("UPLOADED")) return "default";
  return "secondary";
}

export function StatusBadge({ value }: { value?: string | null }) {
  return <Badge variant={statusVariant(value)}>{formatStatus(value)}</Badge>;
}
