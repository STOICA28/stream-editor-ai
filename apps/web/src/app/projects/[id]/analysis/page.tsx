"use client";

import React, { useRef } from "react";
import { useParams } from "next/navigation";
import { Header } from "@/components/layout/Header";
import { PageLoader } from "@/components/ui/Loading";
import { useProject } from "@/hooks/useProject";
import { useAnalysis } from "@/hooks/useAnalysis";
import { Card } from "@/components/ui/Card";

export default function AnalysisPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  
  const { project, loading: projectLoading, error: projectError } = useProject(id);
  const { timeline, transcripts, scenes, loading: analysisLoading, error: analysisError } = useAnalysis(id);
  
  const videoRef = useRef<HTMLVideoElement>(null);

  const handleSeek = (time: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = time;
      videoRef.current.play().catch(() => {});
    }
  };

  const loading = projectLoading || analysisLoading;
  const error = projectError || analysisError;

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
    <div className="flex flex-col h-screen">
      <Header
        breadcrumbs={[
          { label: "Projects", href: "/projects" },
          { label: project.name, href: `/projects/${id}` },
          { label: "Analysis" },
        ]}
      />

      <main className="flex-1 flex overflow-hidden">
        {/* Left pane: Video & Timeline */}
        <div className="flex-1 flex flex-col border-r border-surface-border">
          {/* Video Player */}
          <div className="bg-black aspect-video relative flex-shrink-0">
            {project.source_video_path ? (
              <video
                ref={videoRef}
                controls
                src={project.source_video_path}
                className="w-full h-full object-contain"
              />
            ) : (
              <div className="absolute inset-0 flex items-center justify-center text-text-muted">
                No video source available
              </div>
            )}
          </div>

          {/* Timeline Events */}
          <div className="flex-1 overflow-y-auto p-4 bg-surface-base">
            <h3 className="text-sm font-semibold text-text-secondary mb-3">Timeline Events</h3>
            {timeline.length === 0 ? (
              <p className="text-xs text-text-muted">No timeline events found.</p>
            ) : (
              <div className="space-y-2">
                {timeline.map((event) => (
                  <div key={event.id} className="text-xs p-2 bg-surface-raised border border-surface-border rounded-md flex justify-between items-center hover:bg-surface-overlay transition cursor-pointer" onClick={() => handleSeek(event.start_time)}>
                    <div>
                      <span className="font-mono text-text-muted mr-2">
                        [{event.start_time.toFixed(1)}s - {event.end_time.toFixed(1)}s]
                      </span>
                      <span className="font-semibold capitalize">{event.event_type}</span>
                    </div>
                    <div className="text-text-muted">
                      {event.producer}
                    </div>
                  </div>
                ))}
              </div>
            )}

            <h3 className="text-sm font-semibold text-text-secondary mt-6 mb-3">Scenes</h3>
            {scenes.length === 0 ? (
              <p className="text-xs text-text-muted">No scenes found.</p>
            ) : (
              <div className="space-y-2">
                {scenes.map((scene) => (
                  <div key={scene.id} className="text-xs p-2 bg-surface-raised border border-surface-border rounded-md flex justify-between items-center hover:bg-surface-overlay transition cursor-pointer" onClick={() => handleSeek(scene.start_time)}>
                    <div>
                      <span className="font-mono text-text-muted mr-2">
                        [{scene.start_time.toFixed(1)}s - {scene.end_time.toFixed(1)}s]
                      </span>
                      <span className="font-semibold capitalize">Scene ({scene.duration.toFixed(1)}s)</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right pane: Transcripts */}
        <div className="w-96 flex-shrink-0 flex flex-col bg-surface-base">
          <div className="p-4 border-b border-surface-border">
            <h3 className="text-sm font-semibold text-text-secondary">Transcript</h3>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {transcripts.length === 0 ? (
              <p className="text-xs text-text-muted">No transcript available.</p>
            ) : (
              transcripts.map((segment) => (
                <div key={segment.id} className="text-sm group">
                  <div 
                    className="font-mono text-xs text-primary-400 cursor-pointer hover:underline mb-1"
                    onClick={() => handleSeek(segment.start_time)}
                  >
                    {segment.start_time.toFixed(1)}s
                  </div>
                  <div className="text-text-secondary">
                    {segment.words && segment.words.length > 0 ? (
                      segment.words.map((word) => (
                        <span 
                          key={word.id} 
                          className="cursor-pointer hover:bg-primary-900/30 hover:text-primary-300 rounded px-0.5 transition-colors"
                          onClick={() => handleSeek(word.start_time)}
                        >
                          {word.text}{' '}
                        </span>
                      ))
                    ) : (
                      <span 
                        className="cursor-pointer hover:text-primary-300 transition-colors"
                        onClick={() => handleSeek(segment.start_time)}
                      >
                        {segment.text}
                      </span>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
