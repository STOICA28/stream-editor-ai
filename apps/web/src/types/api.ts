// ---------------------------------------------------------------------------
// Domain types – mirrors the backend Pydantic schemas
// ---------------------------------------------------------------------------

export type ProjectStatus = "created" | "processing" | "ready" | "error";

export interface Project {
  id: string;
  name: string;
  description?: string;
  status: ProjectStatus;
  source_video_path?: string;
  created_at: string;
  updated_at: string;
}

export type JobStatus = "pending" | "running" | "completed" | "failed" | "skipped";

export interface JobStep {
  stage: string;
  status: JobStatus;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  retry_count: number;
}

export interface Job {
  id: string;
  project_id: string;
  status: JobStatus;
  current_stage?: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  steps: JobStep[];
}

export interface MediaAsset {
  id: string;
  project_id: string;
  name: string;
  path: string;
  media_type: string;
  file_size_bytes?: number;
}

export interface CreateProjectInput {
  name: string;
  description?: string;
  source_video_path?: string;
}

export interface HealthResponse {
  status: string;
  version: string;
}

// ---------------------------------------------------------------------------
// Pipeline stage definitions (ordered)
// ---------------------------------------------------------------------------
export const PIPELINE_STAGES = [
  "INGEST",
  "PROBE_MEDIA",
  "CREATE_ANALYSIS_PROXY",
  "EXTRACT_AUDIO",
  "TRANSCRIBE",
  "DETECT_SCENES",
  "DETECT_VISUAL_EVENTS",
  "ANALYZE_AUDIO_EVENTS",
  "IMPORT_OR_ANALYZE_CHAT",
  "GENERATE_CANDIDATES",
  "SCORE_CANDIDATES",
  "BUILD_STORY_GRAPH",
  "GENERATE_EDIT_PLAN",
  "RENDER_PREVIEW",
  "HUMAN_REVIEW",
  "RENDER_FINAL",
] as const;

export type PipelineStage = (typeof PIPELINE_STAGES)[number];

// ---------------------------------------------------------------------------
// Analysis Types
// ---------------------------------------------------------------------------

export interface TimelineEvent {
  id: string;
  project_id: string;
  source_asset_id?: string;
  event_type: string;
  start_time: number;
  end_time: number;
  producer: string;
  producer_version: string;
  confidence?: number;
  data?: Record<string, any>;
}

export interface TranscriptWord {
  id: string;
  start_time: number;
  end_time: number;
  text: string;
  confidence?: number;
}

export interface TranscriptSegment {
  id: string;
  start_time: number;
  end_time: number;
  text: string;
  speaker?: string;
  confidence?: number;
  sequence: number;
  words: TranscriptWord[];
}

export interface Scene {
  id: string;
  project_id: string;
  source_asset_id?: string;
  start_time: number;
  end_time: number;
  duration: number;
  detector: string;
  detector_config?: Record<string, any>;
  confidence?: number;
}
