import React from "react";
import Link from "next/link";
import { Badge } from "@/components/ui/Badge";
import { formatDate, projectStatusVariant } from "@/lib/utils";
import type { Project } from "@/types/api";

interface ProjectCardProps {
  project: Project;
}

export function ProjectCard({ project }: ProjectCardProps) {
  return (
    <Link href={`/projects/${project.id}`} className="block group">
      <div className="bg-surface-raised border border-surface-border rounded-lg p-5 h-full transition-colors hover:border-accent/50 hover:bg-surface-overlay">
        {/* Header row */}
        <div className="flex items-start justify-between gap-3 mb-3">
          <h3 className="text-sm font-semibold text-text-primary group-hover:text-accent-foreground line-clamp-2 transition-colors">
            {project.name}
          </h3>
          <Badge variant={projectStatusVariant(project.status)} className="shrink-0 capitalize">
            {project.status}
          </Badge>
        </div>

        {/* Description */}
        {project.description && (
          <p className="text-xs text-text-secondary mb-3 line-clamp-2">
            {project.description}
          </p>
        )}

        {/* Source path */}
        {project.source_video_path && (
          <p className="text-xs text-text-muted font-mono truncate mb-3" title={project.source_video_path}>
            {project.source_video_path}
          </p>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between pt-3 border-t border-surface-border">
          <span className="text-xs text-text-muted">
            {formatDate(project.created_at)}
          </span>
          <svg
            className="w-4 h-4 text-text-muted group-hover:text-accent transition-colors"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
          </svg>
        </div>
      </div>
    </Link>
  );
}
