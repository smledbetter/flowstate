export interface SprintMetrics {
  active_session_time_s: number;
  active_session_time_display: string;
  total_tokens: number;
  total_tokens_display: string;
  new_work_tokens: number;
  new_work_tokens_display: string;
  cache_hit_rate_pct: number | null;
  opus_pct: number;
  sonnet_pct: number;
  haiku_pct: number;
  subagents: number;
  subagent_note: string | null;
  api_calls: number;
  tests_total: number;
  tests_added: number | null;
  tests_note?: string;
  coverage_pct: number | null;
  lint_errors: number | null;
  gates_first_pass: boolean;
  gates_first_pass_note: string | null;
  loc_added: number;
  loc_added_approx: boolean;
  loc_note?: string;
  rework_rate?: number | null;
  delegation_ratio_pct?: number | null;
  orchestrator_tokens?: number;
  subagent_tokens?: number;
  context_compressions?: number;
}

export interface HypothesisResult {
  id: string;
  name: string;
  result: 'confirmed' | 'partially_confirmed' | 'inconclusive' | 'falsified';
  evidence: string;
}

export interface QualityReview {
  method: string;
  acceptance_criteria: number;
  module_boundaries: number;
  test_first_evidence: number;
  input_validation: number;
  error_messages: number;
  total: number;
  total_pct: number;
}

export interface Sprint {
  project: string;
  sprint: number;
  label: string;
  phase: string;
  experiment?: string;
  metrics: SprintMetrics;
  hypotheses: HypothesisResult[];
  quality_review?: QualityReview;
}

export interface SprintsData {
  _note: string;
  sprints: Sprint[];
}

export interface HypothesesRegistry {
  _note: string;
  valid_results: string[];
  hypotheses: Record<string, string>;
}

/* Session-level analytics types */

export interface SessionBucket {
  sessions: number;
  total_tokens: number;
  new_work_tokens: number;
  active_time_s?: number;
  api_calls?: number;
  context_compressions?: number;
}

export interface ProjectSessions {
  project: string;
  label: string;
  lang: string;
  all: SessionBucket;
  sprint: SessionBucket;
  adhoc: SessionBucket;
}

export interface SessionsData {
  _note: string;
  snapshot_date: string;
  projects: ProjectSessions[];
}

export interface DerivedSprint extends Sprint {
  newWorkTokensPerLoc: number;
  totalTokensPerLoc: number;
  activeMinutes: number;
  projectColor: string;
}
