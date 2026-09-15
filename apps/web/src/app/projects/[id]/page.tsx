"use client";

import React, { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Header } from "@/components/layout/Header";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { JobProgress } from "@/components/jobs/JobProgress";
import { PageLoader } from "@/components/ui/Loading";
import { useProject } from "@/hooks/useProject";
import { triggerProcessing, ApiError } from "@/lib/api";
import { projectStatusVariant, formatDate } from "@/lib/utils";

export default function ProjectDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const { project, job, loading, error, refetch } = useProject(id);
  const [triggering, setTriggering] = useState(false);
  const [triggerError, setTriggerError] = useState<string | null>(null);

  async function handleProcess() {
    setTriggering(true);
    setTriggerError(null);
    try {
      await triggerProcessing(id);
      refetch();
    } catch (err) {
      if (err instanceof ApiError) {
        setTriggerError("Error " + err.status + ": " + err.message);
      } else {
        setTriggerError("Failed to start processing.");
      }
    } finally {
      setTriggering(false);
    }
  }

  const canProcess = project && project.status !== "processing" && job?.status !== "running";

  if (loading) {
    return (
      <>
        <Header breadcrumbs={[{ label: "Projects", href: "/projects" }, { label: "Loading..." }]} />
        <main className="flex-1 overflow-y-auto p-6"><PageLoader /></main>
      </>
    );
  }

  if (error || !project) {
    return (
      <>
        <Header breadcrumbs={[{ label: "Projects", href: "/projects" }, { label: "Error" }]} />
        <main className="flex-1 overflow-y-auto p-6">
          <div className="text-sm text-red-400 bg-red-900/20 border border-red-800 rounded-lg px-4 py-3">
            {error ?? "Project not found."}
          </div>
        </main>
      </>
    );
  }

  return (
    <>
      <Header
        breadcrumbs={[
          { label: "Projects", href: "/projects" },
          { label: project.name },
        ]}
        actions={
          <div className="flex gap-2">
            <Link
              href={`/projects/${id}/edit-plan`}
              className="inline-flex items-center justify-center gap-2 font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/50 bg-primary hover:bg-primary/90 text-primary-foreground h-7 px-3 text-xs rounded"
            >
              Edit Plan
            </Link>
            <Link
              href={`/projects/${id}/story-graph`}
              className="inline-flex items-center justify-center gap-2 font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/50 bg-surface-overlay hover:bg-surface-border text-text-primary border border-surface-border h-7 px-3 text-xs rounded"
            >
              Story Graph
            </Link>
            <Link
              href={`/projects/${id}/candidates`}
              className="inline-flex items-center justify-center gap-2 font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/50 bg-surface-overlay hover:bg-surface-border text-text-primary border border-surface-border h-7 px-3 text-xs rounded"
            >
              Candidates
            </Link>
            <Link
              href={`/projects/${id}/analysis`}
              className="inline-flex items-center justify-center gap-2 font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/50 bg-surface-overlay hover:bg-surface-border text-text-primary border border-surface-border h-7 px-3 text-xs rounded"
            >
              Analysis View
            </Link>
            <Button
              size="sm"
              onClick={handleProcess}
              loading={triggering}
              disabled={!canProcess}
            >
              Run Pipeline
            </Button>
          </div>
        }
      />

      <main className="flex-1 overflow-y-auto p-6">
        <div className="max-w-5xl mx-auto space-y-5">
          {triggerError && (
            <div className="text-xs text-red-400 bg-red-900/20 border border-red-800 rounded-lg px-4 py-3">
              {triggerError}
            </div>
          )}

          <Card header="Project Info">
            <dl className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-sm">
              <div>
                <dt className="text-xs text-text-muted mb-1">Status</dt>
                <dd>
                  <Badge variant={projectStatusVariant(project.status)} className="capitalize">
                    {project.status}
                  </Badge>
                </dd>
              </div>
              <div>
                <dt className="text-xs text-text-muted mb-1">Created</dt>
                <dd className="text-text-secondary">{formatDate(project.created_at)}</dd>
              </div>
              <div>
                <dt className="text-xs text-text-muted mb-1">Updated</dt>
                <dd className="text-text-secondary">{formatDate(project.updated_at)}</dd>
              </div>
              {project.description && (
                <div className="col-span-full">
                  <dt className="text-xs text-text-muted mb-1">Description</dt>
                  <dd className="text-text-secondary">{project.description}</dd>
                </div>
              )}
              {project.source_video_path && (
                <div className="col-span-full">
                  <dt className="text-xs text-text-muted mb-1">Source Video</dt>
                  <dd className="text-text-secondary font-mono text-xs break-all">{project.source_video_path}</dd>
                </div>
              )}
            </dl>
          </Card>

          <Card
            header="Pipeline"
            actions={
              job && (
                <Badge
                  variant={job.status === "completed" ? "success" : job.status === "failed" ? "error" : job.status === "running" ? "info" : "pending"}
                  className="capitalize"
                >
                  {job.status}
                </Badge>
              )
            }
          >
            <JobProgress job={job} />
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <PlaceholderCard title="Analysis Results" description="Audio transcription, scene detection, and visual event data will appear here after analysis stages complete." />
            <PlaceholderCard title="Candidate Segments" description="Scored highlight candidates identified by the AI will appear here after GENERATE_CANDIDATES and SCORE_CANDIDATES complete." />
            <PlaceholderCard title="Edit Plan" description="The structured edit plan will appear here after BUILD_STORY_GRAPH and GENERATE_EDIT_PLAN complete." />
            <PlaceholderCard title="Preview" description="The rendered preview video will appear here after RENDER_PREVIEW and HUMAN_REVIEW stages complete." />
          </div>
        </div>
      </main>
    </>
  );
}

function PlaceholderCard({ title, description }: { title: string; description: string }) {
  return (
    <div className="bg-surface-raised border border-surface-border border-dashed rounded-lg p-5">
      <div className="flex items-center gap-3 mb-3">
        <h3 className="text-sm font-semibold text-text-secondary">{title}</h3>
        <span className="ml-auto text-xs text-text-muted bg-surface-overlay px-2 py-0.5 rounded">Coming soon</span>
      </div>
      <p className="text-xs text-text-muted leading-relaxed">{description}</p>
    </div>
  );
}