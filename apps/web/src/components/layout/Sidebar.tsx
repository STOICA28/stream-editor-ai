"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  {
    href: "/projects",
    label: "Projects",
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 7h18M3 12h18M3 17h18" />
      </svg>
    ),
    enabled: true,
  },
  {
    href: "/research",
    label: "Research",
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
      </svg>
    ),
    enabled: false,
  },
  {
    href: "/settings",
    label: "Settings",
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
    enabled: false,
  },
];

import { useState, useEffect } from "react";

function AIProviderStatus() {
  const [status, setStatus] = useState<any>(null);

  useEffect(() => {
    fetch("http://localhost:8000/api/health/ai")
      .then((res) => res.json())
      .then((data) => setStatus(data))
      .catch(() => setStatus({ status: "error", message: "Failed to fetch" }));
  }, []);

  if (!status) return null;

  return (
    <div className="px-4 py-3 mb-2 mx-2 rounded-md bg-surface-overlay text-xs">
      <div className="flex items-center gap-2 font-medium mb-1">
        <div className={`w-2 h-2 rounded-full ${status.status === "ok" ? "bg-green-500" : "bg-red-500"}`} />
        <span>AI: {status.provider || "Unknown"}</span>
      </div>
      {status.status === "ok" ? (
        <div className="text-text-muted flex flex-col gap-0.5">
          <span>Model: {status.model}</span>
        </div>
      ) : (
        <span className="text-red-400">Offline</span>
      )}
    </div>
  );
}

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex flex-col w-60 min-h-screen bg-surface-raised border-r border-surface-border">
      {/* Logo */}
      <div className="flex items-center gap-2.5 h-14 px-5 border-b border-surface-border">
        <div className="w-7 h-7 rounded-md bg-accent flex items-center justify-center">
          <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <span className="text-sm font-bold text-text-primary tracking-tight">StreamEditor AI</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        {NAV_ITEMS.map((item) => {
          const active = item.enabled && pathname.startsWith(item.href);
          return item.enabled ? (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors",
                active
                  ? "bg-accent/20 text-accent-foreground font-medium"
                  : "text-text-secondary hover:text-text-primary hover:bg-surface-overlay",
              )}
            >
              <span className={active ? "text-accent" : ""}>{item.icon}</span>
              {item.label}
            </Link>
          ) : (
            <div
              key={item.href}
              className="flex items-center gap-3 px-3 py-2 rounded-md text-sm text-text-muted cursor-not-allowed select-none"
              title="Coming soon"
            >
              {item.icon}
              {item.label}
              <span className="ml-auto text-xs text-text-muted">Soon</span>
            </div>
          );
        })}
      </nav>

      <AIProviderStatus />

      {/* Footer */}
      <div className="px-5 py-3 border-t border-surface-border">
        <p className="text-xs text-text-muted">v0.1.0-m0</p>
      </div>
    </aside>
  );
}
