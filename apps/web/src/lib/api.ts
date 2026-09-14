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

export function triggerProcessing(projectId: string): Promise<Job> {
  return apiRequest<Job>(`/api/v1/projects/${projectId}/process`, {
    method: "POST",
  });
}
