import type { ProjectStatus, JobStatus } from "@/types/api";
import type { BadgeVariant } from "@/components/ui/Badge";

// Tailwind class merging helper (lightweight, no clsx dep needed)
export function cn(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(" ");
}

// Date formatting
export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// Status -> badge variant
export function projectStatusVariant(status: ProjectStatus): BadgeVariant {
  const map: Record<ProjectStatus, BadgeVariant> = {
    created: "pending",
    processing: "info",
    ready: "success",
    error: "error",
  };
  return map[status] ?? "default";
}

export function jobStatusVariant(status: JobStatus): BadgeVariant {
  const map: Record<JobStatus, BadgeVariant> = {
    pending: "pending",
    running: "info",
    completed: "success",
    failed: "error",
    skipped: "warning",
  };
  return map[status] ?? "default";
}

export function jobStatusLabel(status: JobStatus): string {
  return status.charAt(0).toUpperCase() + status.slice(1);
}
