"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { getProject, getProjectJobs, ApiError } from "@/lib/api";
import type { Project, Job } from "@/types/api";

const POLL_INTERVAL_MS = 4000;

interface UseProjectResult {
  project: Project | null;
  job: Job | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useProject(id: string): UseProjectResult {
  const [project, setProject] = useState<Project | null>(null);
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const [proj, jobs] = await Promise.all([
        getProject(id),
        getProjectJobs(id),
      ]);
      setProject(proj);
      // Most-recent job
      const latestJob = jobs.length > 0 ? jobs[jobs.length - 1] : null;
      setJob(latestJob);
      setError(null);

      // Stop polling when terminal
      const terminal = !latestJob || ["completed", "failed"].includes(latestJob.status);
      if (terminal && intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(`API error ${err.status}: ${err.message}`);
      } else {
        setError("Failed to load project.");
      }
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchData();
    intervalRef.current = setInterval(fetchData, POLL_INTERVAL_MS);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [fetchData]);

  return { project, job, loading, error, refetch: fetchData };
}
