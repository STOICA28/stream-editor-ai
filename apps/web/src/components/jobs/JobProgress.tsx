"use client";

import React from "react";
import { Badge } from "@/components/ui/Badge";
import { PIPELINE_STAGES } from "@/types/api";
import { jobStatusVariant } from "@/lib/utils";
import type { Job, JobStatus } from "@/types/api";
import { cn } from "@/lib/utils";

interface JobProgressProps {
  job: Job | null;
}

const STATUS_ICONS: Record<JobStatus, React.ReactNode> = {
  completed: (
    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
    </svg>
  ),
  running: (
    <svg className="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <circle className="opacity-25" cx="12" cy="12" r="10" strokeWidth={4} />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4l3-3-3-3v4a8 8 0 00-8 8h4z" />
    </svg>
  ),
  failed: (
    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
    </svg>
  ),
  pending: (
    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <circle cx="12" cy="12" r="9" />
    </svg>
  ),
  skipped: (
    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M13 5l7 7-7 7M6 5l7 7-7 7" />
    </svg>
  ),
};

const STATUS_COLORS: Record<JobStatus, string> = {
  completed: "bg-green-500 text-white",
  running:   "bg-sky-500 text-white",
  failed:    "bg-red-500 text-white",
  pending:   "bg-surface-border text-text-muted",
  skipped:   "bg-amber-700 text-amber-200",
};

function stageStatus(job: Job, stage: string): JobStatus {
  const step = job.steps.find((s) => s.stage === stage);
  if (step) return step.status;
  // Infer pending vs not-yet-reached
  if (job.current_stage === stage) return "running";
  return "pending";
}

function completedCount(job: Job): number {
  return job.steps.filter((s) => s.status === "completed").length;
}

export function JobProgress({ job }: JobProgressProps) {
  if (!job) {
    return (
      <div className="text-sm text-text-muted py-6 text-center">
        No processing job yet. Click &ldquo;Run Pipeline&rdquo; to start.
      </div>
    );
  }

  const done = completedCount(job);
  const total = PIPELINE_STAGES.length;
  const pct = Math.round((done / total) * 100);

  return (
    <div className="space-y-5">
      {/* Progress bar */}
      <div>
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-xs text-text-secondary font-medium">
            Pipeline Progress
          </span>
          <span className="text-xs text-text-secondary">
            {done}/{total} stages &middot; {pct}%
          </span>
        </div>
        <div className="h-2 rounded-full bg-surface-overlay overflow-hidden">
          <div
            className="h-full rounded-full bg-accent transition-all duration-500"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      {/* Stage list */}
      <div className="grid grid-cols-1 gap-1.5">
        {PIPELINE_STAGES.map((stage, idx) => {
          const status = stageStatus(job, stage);
          return (
            <div
              key={stage}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-md text-xs transition-colors",
                status === "running"
                  ? "bg-sky-900/30 border border-sky-800/50"
                  : status === "failed"
                  ? "bg-red-900/20 border border-red-800/40"
                  : "bg-surface-overlay border border-transparent",
              )}
            >
              {/* Step number circle */}
              <div
                className={cn(
                  "w-5 h-5 rounded-full flex items-center justify-center shrink-0 transition-colors",
                  STATUS_COLORS[status],
                )}
              >
                {STATUS_ICONS[status]}
              </div>

              {/* Stage name */}
              <span
                className={cn(
                  "flex-1 font-mono tracking-wide",
                  status === "completed" ? "text-text-secondary" : "",
                  status === "running" ? "text-sky-300 font-semibold" : "",
                  status === "pending" ? "text-text-muted" : "",
                  status === "failed" ? "text-red-400 font-semibold" : "",
                  status === "skipped" ? "text-amber-400" : "",
                )}
              >
                {stage}
              </span>

              {/* Badge */}
              <Badge variant={jobStatusVariant(status)} className="ml-auto shrink-0 capitalize">
                {status}
              </Badge>
            </div>
          );
        })}
      </div>

      {/* Error message */}
      {job.error_message && (
        <div className="text-xs text-red-400 bg-red-900/20 border border-red-800 rounded-md px-3 py-2">
          <span className="font-semibold">Error: </span>
          {job.error_message}
        </div>
      )}
    </div>
  );
}
