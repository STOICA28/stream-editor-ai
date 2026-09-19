import React from "react";
import { cn } from "@/lib/utils";

export type BadgeVariant = "default" | "success" | "warning" | "error" | "info" | "pending" | "outline";

interface BadgeProps {
  variant?: BadgeVariant;
  children: React.ReactNode;
  className?: string;
}

const variantStyles: Record<BadgeVariant, string> = {
  default:  "bg-surface-overlay text-text-secondary border border-surface-border",
  success:  "bg-green-900/40  text-green-400  border border-green-800",
  warning:  "bg-amber-900/40  text-amber-400  border border-amber-800",
  error:    "bg-red-900/40    text-red-400    border border-red-800",
  info:     "bg-sky-900/40    text-sky-400    border border-sky-800",
  pending:  "bg-slate-800/60  text-slate-400  border border-slate-700",
  outline:  "bg-transparent text-text-secondary border border-surface-border",
};

export function Badge({ variant = "default", children, className }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium",
        variantStyles[variant],
        className,
      )}
    >
      {children}
    </span>
  );
}
