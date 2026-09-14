"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Header } from "@/components/layout/Header";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { createProject, ApiError } from "@/lib/api";

export default function NewProjectPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [sourcePath, setSourcePath] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  return (
    <>
      <Header
        breadcrumbs={[
          { label: "Projects", href: "/projects" },
          { label: "New Project" },
        ]}
      />

      <main className="flex-1 overflow-y-auto p-6">
        <div className="max-w-lg mx-auto">
          <Card header="Create New Project">
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-text-secondary mb-1.5" htmlFor="name">
                  Name <span className="text-red-400">*</span>
                </label>
                <input
                  id="name"
                  type="text"
                  required
                  autoFocus
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="My stream highlight reel"
                  className="w-full h-9 px-3 rounded-md bg-surface text-sm text-text-primary placeholder:text-text-muted border border-surface-border focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-text-secondary mb-1.5" htmlFor="description">
                  Description
                </label>
                <textarea
                  id="description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Optional notes about this project…"
                  rows={3}
                  className="w-full px-3 py-2 rounded-md bg-surface text-sm text-text-primary placeholder:text-text-muted border border-surface-border focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent resize-none"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-text-secondary mb-1.5" htmlFor="source-path">
                  Source Video Path
                </label>
                <input
                  id="source-path"
                  type="text"
                  value={sourcePath}
                  onChange={(e) => setSourcePath(e.target.value)}
                  placeholder="/data/streams/vod_2024-01-15.mp4"
                  className="w-full h-9 px-3 rounded-md bg-surface text-sm text-text-primary placeholder:text-text-muted font-mono border border-surface-border focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent"
                />
                <p className="mt-1 text-xs text-text-muted">
                  Absolute path on the server where the backend can read the video file.
                </p>
              </div>

              {error && (
                <p className="text-xs text-red-400 bg-red-900/20 border border-red-800 rounded-md px-3 py-2">
                  {error}
                </p>
              )}

              <div className="flex items-center justify-end gap-3 pt-2">
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => router.push("/projects")}
                  disabled={submitting}
                >
                  Cancel
                </Button>
                <Button type="submit" loading={submitting} disabled={!name.trim()}>
                  Create Project
                </Button>
              </div>
            </form>
          </Card>
        </div>
      </main>
    </>
  );
}
