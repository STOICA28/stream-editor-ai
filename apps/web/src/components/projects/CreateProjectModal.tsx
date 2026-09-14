"use client";

import React, { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { createProject, ApiError } from "@/lib/api";

interface CreateProjectModalProps {
  open: boolean;
  onClose: () => void;
}

export function CreateProjectModal({ open, onClose }: CreateProjectModalProps) {
  const router = useRouter();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [sourcePath, setSourcePath] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const nameRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (open) {
      setName("");
      setDescription("");
      setSourcePath("");
      setError(null);
      setTimeout(() => nameRef.current?.focus(), 50);
    }
  }, [open]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;

    setSubmitting(true);
    setError(null);
    try {
      const project = await createProject({
        name: name.trim(),
        description: description.trim() || undefined,
        source_video_path: sourcePath.trim() || undefined,
      });
      onClose();
      router.push(`/projects/${project.id}`);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(`Error ${err.status}: ${err.message}`);
      } else {
        setError("Failed to create project. Please try again.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      role="dialog"
      aria-modal="true"
      aria-label="Create new project"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Panel */}
      <div className="relative z-10 w-full max-w-md bg-surface-raised border border-surface-border rounded-xl shadow-2xl p-6">
        <h2 className="text-base font-semibold text-text-primary mb-5">New Project</h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Name */}
          <div>
            <label className="block text-xs font-medium text-text-secondary mb-1.5" htmlFor="proj-name">
              Name <span className="text-red-400">*</span>
            </label>
            <input
              ref={nameRef}
              id="proj-name"
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="My stream highlight reel"
              className="w-full h-9 px-3 rounded-md bg-surface text-sm text-text-primary placeholder:text-text-muted border border-surface-border focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent"
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-xs font-medium text-text-secondary mb-1.5" htmlFor="proj-desc">
              Description
            </label>
            <textarea
              id="proj-desc"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional notes about this project…"
              rows={3}
              className="w-full px-3 py-2 rounded-md bg-surface text-sm text-text-primary placeholder:text-text-muted border border-surface-border focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent resize-none"
            />
          </div>

          {/* Source video path */}
          <div>
            <label className="block text-xs font-medium text-text-secondary mb-1.5" htmlFor="proj-path">
              Source Video Path
            </label>
            <input
              id="proj-path"
              type="text"
              value={sourcePath}
              onChange={(e) => setSourcePath(e.target.value)}
              placeholder="/data/streams/vod_2024-01-15.mp4"
              className="w-full h-9 px-3 rounded-md bg-surface text-sm text-text-primary placeholder:text-text-muted font-mono border border-surface-border focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent"
            />
            <p className="mt-1 text-xs text-text-muted">Absolute path on the server where the backend can reach the file.</p>
          </div>

          {/* Error */}
          {error && (
            <p className="text-xs text-red-400 bg-red-900/20 border border-red-800 rounded-md px-3 py-2">
              {error}
            </p>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-1">
            <Button type="button" variant="ghost" onClick={onClose} disabled={submitting}>
              Cancel
            </Button>
            <Button type="submit" loading={submitting} disabled={!name.trim()}>
              Create Project
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
