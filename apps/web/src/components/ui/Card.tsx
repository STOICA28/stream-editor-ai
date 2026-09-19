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

export function CardHeader({ children, className }: { children: React.ReactNode, className?: string }) {
  return <div className={cn("px-5 py-4 border-b border-surface-border", className)}>{children}</div>;
}

export function CardTitle({ children, className }: { children: React.ReactNode, className?: string }) {
  return <div className={cn("text-sm font-semibold text-text-primary", className)}>{children}</div>;
}

export function CardContent({ children, className }: { children: React.ReactNode, className?: string }) {
  return <div className={cn("p-5", className)}>{children}</div>;
}
