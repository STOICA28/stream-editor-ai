import type {
  Project,
  Job,
  CreateProjectInput,
  HealthResponse,
} from "@/types/api";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ---------------------------------------------------------------------------
// Core fetch wrapper
// ---------------------------------------------------------------------------

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function apiRequest<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });

  if (!res.ok) {
    const body = await res.text();
    throw new ApiError(res.status, body);
  }

  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Typed API functions
// ---------------------------------------------------------------------------

export function getHealth(): Promise<HealthResponse> {
  return apiRequest<HealthResponse>("/health");
}

export function getProjects(): Promise<Project[]> {
  return apiRequest<Project[]>("/api/v1/projects");
}

export function getProject(id: string): Promise<Project> {
  return apiRequest<Project>(`/api/v1/projects/${id}`);
}

export function createProject(data: CreateProjectInput): Promise<Project> {
  return apiRequest<Project>("/api/v1/projects", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function getJob(id: string): Promise<Job> {
  return apiRequest<Job>(`/api/v1/jobs/${id}`);
}

export function getProjectJobs(projectId: string): Promise<Job[]> {
  return apiRequest<Job[]>(`/api/v1/projects/${projectId}/jobs`);
}

export function triggerProcessing(projectId: string, payload?: { style_policy_id?: string; dry_run?: boolean }): Promise<Job> {
  return apiRequest<Job>(`/api/v1/projects/${projectId}/process`, {
    method: "POST",
    body: payload ? JSON.stringify(payload) : undefined,
  });
}

// ---------------------------------------------------------------------------
// Analysis API
// ---------------------------------------------------------------------------

import type { TimelineEvent, TranscriptSegment, Scene } from "@/types/api";

export function getProjectTimeline(projectId: string): Promise<TimelineEvent[]> {
  return apiRequest<TimelineEvent[]>(`/api/v1/projects/${projectId}/timeline`);
}

export function getProjectTranscripts(projectId: string): Promise<TranscriptSegment[]> {
  return apiRequest<TranscriptSegment[]>(`/api/v1/projects/${projectId}/transcripts`);
}

export function getProjectScenes(projectId: string): Promise<Scene[]> {
  return apiRequest<Scene[]>(`/api/v1/projects/${projectId}/scenes`);
}

