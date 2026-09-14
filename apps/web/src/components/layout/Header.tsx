import React from "react";
import Link from "next/link";
import { cn } from "@/lib/utils";

export interface Breadcrumb {
  label: string;
  href?: string;
}

interface HeaderProps {
  breadcrumbs?: Breadcrumb[];
  actions?: React.ReactNode;
  className?: string;
}

export function Header({ breadcrumbs, actions, className }: HeaderProps) {
  return (
    <header
      className={cn(
        "flex items-center justify-between h-14 px-6 border-b border-surface-border bg-surface-raised shrink-0",
        className,
      )}
    >
      {/* Breadcrumbs */}
      <nav className="flex items-center gap-1.5 text-sm">
        {breadcrumbs?.map((crumb, i) => (
          <React.Fragment key={i}>
            {i > 0 && (
              <svg className="w-3.5 h-3.5 text-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            )}
            {crumb.href ? (
              <Link
                href={crumb.href}
                className="text-text-secondary hover:text-text-primary transition-colors"
              >
                {crumb.label}
              </Link>
            ) : (
              <span className="text-text-primary font-medium">{crumb.label}</span>
            )}
          </React.Fragment>
        ))}
      </nav>

      {/* Actions slot */}
      {actions && <div className="flex items-center gap-3">{actions}</div>}
    </header>
  );
}
