"use client";

import React, { useState } from "react";
import { Header } from "@/components/layout/Header";
import { Button } from "@/components/ui/Button";
import { ProjectCard } from "@/components/projects/ProjectCard";
import { CreateProjectModal } from "@/components/projects/CreateProjectModal";
import { Skeleton } from "@/components/ui/Loading";
import { useProjects } from "@/hooks/useProjects";

export default function ProjectsPage() {
  const { projects, loading, error, refetch } = useProjects();
  const [modalOpen, setModalOpen] = useState(false);

  return (
    <>
      <Header
        breadcrumbs={[{ label: "Projects" }]}
        actions={
          <Button onClick={() => setModalOpen(true)} size="sm">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
            </svg>
            New Project
          </Button>
        }
      />

      <main className="flex-1 overflow-y-auto p-6">
        {/* Error state */}
        {error && (
          <div className="mb-6 flex items-start gap-3 bg-red-900/20 border border-red-800 text-red-400 rounded-lg px-4 py-3 text-sm">
            <svg className="w-4 h-4 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <div>
              <p className="font-medium">Failed to load projects</p>
              <p className="text-xs text-red-300 mt-0.5">{error}</p>
              <button
                onClick={refetch}
                className="text-xs text-red-300 underline mt-1 hover:text-red-200"
              >
                Try again
              </button>
            </div>
          </div>
        )}

        {/* Loading skeletons */}
        {loading && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="bg-surface-raised border border-surface-border rounded-lg p-5 space-y-3">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-full" />
                <Skeleton className="h-3 w-2/3" />
                <div className="pt-2">
                  <Skeleton className="h-2 w-1/3" />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Empty state */}
        {!loading && !error && projects.length === 0 && (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div className="w-16 h-16 rounded-2xl bg-surface-raised border border-surface-border flex items-center justify-center mb-5">
              <svg className="w-8 h-8 text-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 10l4.553-2.069A1 1 0 0121 8.82v6.362a1 1 0 01-1.447.894L15 14M3 8a2 2 0 012-2h8a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V8z" />
              </svg>
            </div>
            <h2 className="text-base font-semibold text-text-primary mb-2">No projects yet</h2>
            <p className="text-sm text-text-secondary mb-6 max-w-sm">
              Create your first project to start processing stream recordings into highlight reels.
            </p>
            <Button onClick={() => setModalOpen(true)}>
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
              </svg>
              Create First Project
            </Button>
          </div>
        )}

        {/* Project grid */}
        {!loading && projects.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {projects.map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>
        )}
      </main>

      <CreateProjectModal
        open={modalOpen}
        onClose={() => {
          setModalOpen(false);
          refetch();
        }}
      />
    </>
  );
}
