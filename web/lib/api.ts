/**
 * Typed API client for the Verxlite backend.
 *
 * Usage:
 *   import { api, setAuthToken } from "@/lib/api";
 *   setAuthToken(token);
 *   const workflows = await api.workflows.list();
 */

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

let authToken: string | null = null;

export function setAuthToken(token: string | null) {
  authToken = token;
}

export function getAuthToken() {
  return authToken;
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options.headers as Record<string, string>) || {}),
  };
  if (authToken) {
    headers["Authorization"] = `Bearer ${authToken}`;
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 204) {
    return undefined as T;
  }

  const text = await response.text();
  let data: unknown;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }

  if (!response.ok) {
    const message =
      (data && typeof data === "object" && "message" in data && (data as any).message) ||
      `Request failed with status ${response.status}`;
    const error = new Error(message) as Error & { status: number; body: unknown };
    error.status = response.status;
    error.body = data;
    throw error;
  }

  return data as T;
}

// --------------------------------------------------------------------------- //
// Types
// --------------------------------------------------------------------------- //
export interface User {
  id: string;
  email: string;
  first_name?: string;
  last_name?: string;
  full_name?: string;
  role: string;
  tenant_id: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface Workflow {
  id: string;
  name: string;
  description?: string;
  workflow_type: string;
  is_active: boolean;
  status: string;
  priority: number;
  config: Record<string, unknown>;
  trigger_config: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface WorkflowRun {
  id: string;
  workflow_id: string;
  trigger_type: string;
  status: string;
  total_tokens: number;
  total_duration_ms: number;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface Connection {
  id: string;
  provider: string;
  is_active: boolean;
  is_expired: boolean;
  scope?: string;
  created_at: string;
  updated_at: string;
}

export interface Artifact {
  id: string;
  run_id: string;
  artifact_type: string;
  external_id?: string;
  external_url?: string;
  status: string;
  content_summary?: string;
  created_at: string;
  updated_at: string;
}

// --------------------------------------------------------------------------- //
// API surface
// --------------------------------------------------------------------------- //
export const api = {
  auth: {
    register: (body: { email: string; password: string; first_name?: string; last_name?: string; tenant_name?: string }) =>
      request<AuthResponse>("/auth/register", { method: "POST", body: JSON.stringify(body) }),
    login: (body: { email: string; password: string }) =>
      request<AuthResponse>("/auth/login", { method: "POST", body: JSON.stringify(body) }),
    me: () => request<User>("/auth/me"),
  },

  workflows: {
    list: (params: { page?: number; page_size?: number; search?: string } = {}) => {
      const q = new URLSearchParams();
      if (params.page) q.set("page", String(params.page));
      if (params.page_size) q.set("page_size", String(params.page_size));
      if (params.search) q.set("search", params.search);
      return request<{ workflows: Workflow[]; total: number; page: number; page_size: number }>(
        `/workflows/?${q.toString()}`
      );
    },
    get: (id: string) => request<Workflow>(`/workflows/${id}`),
    create: (body: Partial<Workflow>) =>
      request<Workflow>("/workflows/", { method: "POST", body: JSON.stringify(body) }),
    update: (id: string, body: Partial<Workflow>) =>
      request<Workflow>(`/workflows/${id}`, { method: "PUT", body: JSON.stringify(body) }),
    delete: (id: string) => request<void>(`/workflows/${id}`, { method: "DELETE" }),
    enable: (id: string) => request<Workflow>(`/workflows/${id}/enable`, { method: "POST" }),
    disable: (id: string) => request<Workflow>(`/workflows/${id}/disable`, { method: "POST" }),
    templates: () =>
      request<{ templates: unknown[]; total: number }>("/workflows/templates"),
    triggerRun: (id: string, body: { trigger_type?: string; trigger_data?: Record<string, unknown>; idempotency_key?: string }) =>
      request<WorkflowRun>(`/workflows/${id}/runs`, { method: "POST", body: JSON.stringify(body) }),
    runs: (params: { workflow_id?: string; page?: number; page_size?: number } = {}) => {
      const q = new URLSearchParams();
      if (params.workflow_id) q.set("workflow_id", params.workflow_id);
      if (params.page) q.set("page", String(params.page));
      if (params.page_size) q.set("page_size", String(params.page_size));
      return request<{ runs: WorkflowRun[]; total: number; page: number; page_size: number }>(
        `/workflows/runs?${q.toString()}`
      );
    },
    run: (id: string) => request<WorkflowRun & { steps: unknown[]; artifacts: unknown[] }>(`/workflows/runs/${id}`),
    stats: () => request<Record<string, number>>("/workflows/stats"),
  },

  connections: {
    list: (params: { provider?: string; is_active?: boolean } = {}) => {
      const q = new URLSearchParams();
      if (params.provider) q.set("provider", params.provider);
      if (params.is_active !== undefined) q.set("is_active", String(params.is_active));
      return request<{ connections: Connection[]; total: number; page: number; page_size: number }>(
        `/connections/?${q.toString()}`
      );
    },
    get: (id: string) => request<Connection>(`/connections/${id}`),
    delete: (id: string) => request<void>(`/connections/${id}`, { method: "DELETE" }),
    refresh: (id: string) => request<Connection>(`/connections/${id}/refresh`, { method: "POST" }),
    authorizeGoogle: () =>
      request<{ state: string; provider: string; redirect_url: string }>("/connections/google/authorize"),
    authorizeHubspot: () =>
      request<{ state: string; provider: string; redirect_url: string }>("/connections/hubspot/authorize"),
  },

  artifacts: {
    list: (params: { run_id?: string; artifact_type?: string; limit?: number; offset?: number } = {}) => {
      const q = new URLSearchParams();
      if (params.run_id) q.set("run_id", params.run_id);
      if (params.artifact_type) q.set("artifact_type", params.artifact_type);
      if (params.limit) q.set("limit", String(params.limit));
      if (params.offset) q.set("offset", String(params.offset));
      return request<{ artifacts: Artifact[]; total: number }>(`/artifacts/?${q.toString()}`);
    },
    get: (id: string) => request<Artifact>(`/artifacts/${id}`),
  },

  health: () => request<{ status: string; checks: Record<string, unknown> }>("/health"),
};
