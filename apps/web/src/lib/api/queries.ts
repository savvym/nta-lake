import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { fetchJson } from "./client";

export interface MeResponse {
  user_id: string;
  username: string;
  email: string | null;
  role: string;
  is_active: boolean;
}

export interface RepoListItem {
  id: string;
  owner: string;
  name: string;
  layer: string;
  subtype: string;
  visibility: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface RepoListResponse {
  items: RepoListItem[];
  total: number;
}

export interface BlobUploadResponse {
  sha256: string;
  size: number;
  storage_key: string;
  deduplicated: boolean;
}

export interface TreeEntryRead {
  name: string;
  mode: number;
  entry_type: string;
  target_hash: string;
}

export interface TreeRead {
  hash: string;
  entries: TreeEntryRead[];
}

export interface CommitRead {
  hash: string;
  repo_id: string;
  tree_hash: string;
  parents: string[];
  author_id: string;
  created_at: string;
  message: string | null;
  lineage: unknown | null;
  tree: TreeRead;
  deduplicated: boolean;
}

export interface RefRead {
  name: string;
  commit_hash: string;
}

export interface JobRead {
  id: string;
  type: string;
  status: string;
  payload: Record<string, unknown>;
  result: Record<string, unknown> | null;
  error: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface CreateRepoRequest {
  owner: string;
  name: string;
  layer: string;
  subtype: string;
  visibility: string;
  description?: string | null;
}

export interface UpdateRepoRequest {
  visibility?: string | null;
  description?: string | null;
}

export interface IngestFileSpec {
  path: string;
  sha256: string;
}

export interface EnqueueIngestRequest {
  owner: string;
  name: string;
  request: {
    adapter_name: string;
    adapter_version: string;
    spec: { files: IngestFileSpec[] };
    author_id: string;
    message?: string | null;
    ref?: string | null;
  };
}

// --- queries ---

export function useMe() {
  return useQuery({
    queryKey: ["me"],
    queryFn: () =>
      fetchJson<MeResponse>("/api/auth/me", undefined, { allowAnon: true }),
    staleTime: 30_000,
  });
}

export function useRepos() {
  return useQuery({
    queryKey: ["repos"],
    queryFn: () => fetchJson<RepoListResponse>("/api/repos?limit=200"),
  });
}

export function useRepo(owner: string, name: string) {
  return useQuery({
    queryKey: ["repo", owner, name],
    queryFn: () =>
      fetchJson<RepoListItem>(
        `/api/repos/${encodeURIComponent(owner)}/${encodeURIComponent(name)}`,
      ),
  });
}

export function useCommit(owner: string, name: string, hash: string) {
  return useQuery({
    queryKey: ["commit", owner, name, hash],
    queryFn: () =>
      fetchJson<CommitRead>(
        `/api/repos/${encodeURIComponent(owner)}/${encodeURIComponent(name)}/commits/${encodeURIComponent(hash)}`,
      ),
    enabled: !!hash && /^[0-9a-f]{64}$/.test(hash),
  });
}

export function useRepoRef(owner: string, name: string, refName: string) {
  return useQuery({
    queryKey: ["ref", owner, name, refName],
    queryFn: () =>
      fetchJson<RefRead>(
        `/api/repos/${encodeURIComponent(owner)}/${encodeURIComponent(name)}/refs/${encodeURIComponent(refName)}`,
      ),
    enabled: !!refName,
  });
}

export function useJob(jobId: string) {
  return useQuery({
    queryKey: ["job", jobId],
    queryFn: () =>
      fetchJson<JobRead>(`/api/jobs/${encodeURIComponent(jobId)}`),
    refetchInterval: (query) => {
      const data = query.state.data as JobRead | null | undefined;
      if (!data) return 1000;
      if (data.status === "queued" || data.status === "running") return 1000;
      return false;
    },
  });
}

// --- mutations ---

export function useCreateRepo() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: CreateRepoRequest) =>
      fetchJson<RepoListItem>("/api/repos", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["repos"] });
    },
  });
}

export function useUpdateRepo(owner: string, name: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: UpdateRepoRequest) =>
      fetchJson<RepoListItem>(
        `/api/repos/${encodeURIComponent(owner)}/${encodeURIComponent(name)}`,
        {
          method: "PATCH",
          body: JSON.stringify(body),
        },
      ),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["repos"] });
      qc.invalidateQueries({ queryKey: ["repo", owner, name] });
    },
  });
}

export function useDeleteRepo(owner: string, name: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () =>
      fetchJson<null>(
        `/api/repos/${encodeURIComponent(owner)}/${encodeURIComponent(name)}`,
        { method: "DELETE" },
      ),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["repos"] });
      qc.invalidateQueries({ queryKey: ["repo", owner, name] });
    },
  });
}

export function useUploadBlob(owner: string, name: string) {
  return useMutation({
    mutationFn: async (file: File | Blob): Promise<BlobUploadResponse> => {
      // 不走 fetchJson 因为它默认 Content-Type: application/json；
      // blob 上传需 application/octet-stream + raw body。
      const resp = await fetch(
        `/api/repos/${encodeURIComponent(owner)}/${encodeURIComponent(name)}/blobs`,
        {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/octet-stream" },
          body: file,
        },
      );
      if (!resp.ok) {
        const text = await resp.text();
        throw new Error(`upload blob failed ${resp.status}: ${text}`);
      }
      return (await resp.json()) as BlobUploadResponse;
    },
  });
}

export function useEnqueueIngest() {
  return useMutation({
    mutationFn: async (body: EnqueueIngestRequest) =>
      fetchJson<JobRead>("/api/jobs/ingest", {
        method: "POST",
        body: JSON.stringify(body),
      }),
  });
}

// --- pipeline-ui-tab-20260518 ---

export interface PipelineNodeRunResponse {
  node_id: string;
  processor_name: string;
  processor_version: string;
  config: Record<string, unknown>;
  status: string;
  cache_hit: boolean;
  output_commit_hash: string | null;
  input_commits: string[] | null;
  cache_key: string | null;
  error: string | null;
}

export interface PipelineRunResponse {
  run_id: string;
  recipe_name: string;
  status: string;
  error: string | null;
  created_by: string;
  node_runs: PipelineNodeRunResponse[];
}

export interface PipelineRunCreatedResponse {
  run_id: string;
  job_id: string;
}

export function useCreatePipelineRun() {
  return useMutation({
    mutationFn: async (
      recipeYaml: string,
    ): Promise<PipelineRunCreatedResponse> => {
      // 不走 fetchJson 因为它默认 Content-Type: application/json；
      // pipeline:from-yaml 路由需 Content-Type: text/yaml + raw body。
      const resp = await fetch("/api/pipelines/runs:from-yaml", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "text/yaml" },
        body: recipeYaml,
      });
      if (!resp.ok) {
        const text = await resp.text();
        throw new Error(`create pipeline run failed ${resp.status}: ${text}`);
      }
      return (await resp.json()) as PipelineRunCreatedResponse;
    },
  });
}

export function usePipelineRun(runId: string | null) {
  return useQuery({
    queryKey: ["pipeline-run", runId],
    queryFn: () =>
      fetchJson<PipelineRunResponse>(
        `/api/pipelines/runs/${encodeURIComponent(runId ?? "")}`,
      ),
    enabled: !!runId,
    refetchInterval: (query) => {
      const data = query.state.data as PipelineRunResponse | null | undefined;
      if (!data) return 1000;
      if (data.status === "succeeded" || data.status === "failed") return false;
      return 1000;
    },
  });
}
