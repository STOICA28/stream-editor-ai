"use client";

import { useState, useEffect, useCallback } from "react";
import { getProjectTimeline, getProjectTranscripts, getProjectScenes, ApiError } from "@/lib/api";
import type { TimelineEvent, TranscriptSegment, Scene } from "@/types/api";

interface UseAnalysisResult {
  timeline: TimelineEvent[];
  transcripts: TranscriptSegment[];
  scenes: Scene[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useAnalysis(id: string): UseAnalysisResult {
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [transcripts, setTranscripts] = useState<TranscriptSegment[]>([]);
  const [scenes, setScenes] = useState<Scene[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [tl, tr, sc] = await Promise.all([
        getProjectTimeline(id),
        getProjectTranscripts(id),
        getProjectScenes(id),
      ]);
      setTimeline(tl);
      setTranscripts(tr);
      setScenes(sc);
      setError(null);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(`API error ${err.status}: ${err.message}`);
      } else {
        setError("Failed to load analysis data.");
      }
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { timeline, transcripts, scenes, loading, error, refetch: fetchData };
}
