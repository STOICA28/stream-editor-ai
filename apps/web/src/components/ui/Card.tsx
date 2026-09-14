import React from "react";
import { cn } from "@/lib/utils";

interface CardProps {
  children: React.ReactNode;
  className?: string;
  header?: React.ReactNode;
  actions?: React.ReactNode;
}

export function Card({ children, className, header, actions }: CardProps) {
  return (
    <div
      className={cn(
        "bg-surface-raised border border-surface-border rounded-lg overflow-hidden",
        className,
      )}
    >
      {header && (
        <div className="flex items-center justify-between px-5 py-4 border-b border-surface-border">
          <div className="text-sm font-semibold text-text-primary">{header}</div>
          {actions && <div className="flex items-center gap-2">{actions}</div>}
        </div>
      )}
      <div className="p-5">{children}</div>
    </div>
  );
}
