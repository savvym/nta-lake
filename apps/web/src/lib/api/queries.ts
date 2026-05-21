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

export interface SnapshotRead {
  hash: string;
  repo_id: string;
  tree_hash: string;
  parent: string | null;
  author_id: string;
  created_at: string;
  message: string | null;
  lineage: unknown | null;
  tree: TreeRead;
  deduplicated: boolean;
}

export interface RefRead {
  name: string;
  snapshot_hash: string;
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
  schema_id?: string | null;
  row_format?: 'parquet' | 'jsonl' | null;
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

export function useSnapshot(owner: string, name: string, hash: string) {
  return useQuery({
    queryKey: ["snapshot", owner, name, hash],
    queryFn: () =>
      fetchJson<SnapshotRead>(
        `/api/repos/${encodeURIComponent(owner)}/${encodeURIComponent(name)}/snapshots/${encodeURIComponent(hash)}`,
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

// --- tree-nested-domain-20260520 接入：按 hash 取任意子层 ---

export function useSubtree(owner: string, name: string, treeHash: string) {
  return useQuery({
    queryKey: ["subtree", owner, name, treeHash],
    queryFn: async (): Promise<TreeRead> => {
      const r = await fetchJson<TreeRead>(
        `/api/repos/${encodeURIComponent(owner)}/${encodeURIComponent(name)}/trees/${encodeURIComponent(treeHash)}`,
      );
      if (r === null) {
        throw new Error(`subtree ${treeHash.slice(0, 12)}… not found`);
      }
      return r;
    },
    enabled: !!treeHash && /^[0-9a-f]{64}$/.test(treeHash),
  });
}

// 按路径解析到当前层 subtree（HF 风导航支撑）
//
// 算法：fetch root tree → split path by "/" → 每段在当前层 entries 找
// type=="tree" && name==seg → 拿 target_hash → fetch /trees/{hash} → 重复。
// 任一段不存在 / 不是 tree → throw 含 segment 与现有 entries。
// path == "" 直接返 root tree。
export function useSubtreeByPath(
  owner: string,
  name: string,
  commitHash: string,
  path: string,
) {
  return useQuery({
    queryKey: ["subtree-by-path", owner, name, commitHash, path],
    queryFn: async (): Promise<TreeRead> => {
      const baseUrl = `/api/repos/${encodeURIComponent(owner)}/${encodeURIComponent(name)}`;
      const root = await fetchJson<TreeRead>(
        `${baseUrl}/tree/${encodeURIComponent(commitHash)}`,
      );
      if (root === null) {
        throw new Error(`commit ${commitHash.slice(0, 12)}… tree not found`);
      }
      const segments = path ? path.split("/").filter((s) => s.length > 0) : [];
      let current: TreeRead = root;
      for (const seg of segments) {
        const sub = current.entries.find(
          (e) => e.name === seg && e.entry_type === "tree",
        );
        if (!sub) {
          throw new Error(
            `路径段 ${JSON.stringify(seg)} 在当前层不存在或不是目录；现有 entries：${current.entries
              .map((e) => `${e.name}(${e.entry_type})`)
              .join(", ")}`,
          );
        }
        const next = await fetchJson<TreeRead>(
          `${baseUrl}/trees/${encodeURIComponent(sub.target_hash)}`,
        );
        if (next === null) {
          throw new Error(
            `subtree ${sub.target_hash.slice(0, 12)}… (for segment ${seg}) not found`,
          );
        }
        current = next;
      }
      return current;
    },
    enabled: !!commitHash && /^[0-9a-f]{64}$/.test(commitHash),
  });
}

export interface JobsListResponse {
  items: JobRead[];
  total: number;
  limit: number;
  offset: number;
}

// web-jobs-list-page-20260520: admin 列表 hook
// enabled 由调用方控制（非 admin 不发请求，避免 403 噪声）
export function useJobs(
  filters: {
    status?: string;
    type?: string;
    limit: number;
    offset: number;
  },
  opts?: { enabled?: boolean },
) {
  return useQuery({
    queryKey: [
      "jobs",
      filters.status ?? "",
      filters.type ?? "",
      filters.limit,
      filters.offset,
    ],
    queryFn: async (): Promise<JobsListResponse> => {
      const qs = new URLSearchParams();
      if (filters.status) qs.set("status", filters.status);
      if (filters.type) qs.set("type", filters.type);
      qs.set("limit", String(filters.limit));
      qs.set("offset", String(filters.offset));
      const r = await fetchJson<JobsListResponse>(`/api/jobs?${qs.toString()}`);
      if (r === null) throw new Error("jobs list not accessible");
      return r;
    },
    enabled: opts?.enabled ?? true,
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

// --- repo-files-tab-v2-20260518 ---

export interface BlobMetaResponse {
  sha256: string;
  size: number;
}

// 新增 W4-1：snapshot rows 分页查询
export interface SilverRowRead {
  text: string;
  images: unknown[];
  source_ref: Record<string, unknown>;
  stats: Record<string, unknown>;
  lineage_ops: unknown[];
}

export interface SnapshotRowsResponse {
  rows: SilverRowRead[];
  total: number;
  offset: number;
  limit: number;
  blob_sha: string;
}

export function useSnapshotRows(
  owner: string,
  name: string,
  hash: string,
  opts: { offset: number; limit: number; blobSha?: string },
) {
  return useQuery({
    queryKey: [
      "snapshot-rows",
      owner,
      name,
      hash,
      opts.offset,
      opts.limit,
      opts.blobSha ?? "",
    ],
    queryFn: () => {
      const params = new URLSearchParams({
        offset: String(opts.offset),
        limit: String(opts.limit),
      });
      if (opts.blobSha) params.set("blob_sha", opts.blobSha);
      return fetchJson<SnapshotRowsResponse>(
        `/api/repos/${encodeURIComponent(owner)}/${encodeURIComponent(name)}/snapshots/${encodeURIComponent(hash)}/rows?${params.toString()}`,
      );
    },
    enabled: !!hash && /^[0-9a-f]{64}$/.test(hash),
  });
}

export function useBlobMeta(owner: string, name: string, sha256: string) {
  return useQuery({
    queryKey: ["blob-meta", owner, name, sha256],
    queryFn: () =>
      fetchJson<BlobMetaResponse>(
        `/api/repos/${encodeURIComponent(owner)}/${encodeURIComponent(name)}/blobs/${encodeURIComponent(sha256)}/meta`,
      ),
    enabled: /^[0-9a-f]{64}$/.test(sha256),
  });
}

// --- W4-4: snapshot export mutation hook ---

export interface SnapshotExportResult {
  blob: Blob;
  rowCount: string | null;
  blobSha: string | null;
}

export interface SnapshotExportArgs {
  owner: string;
  name: string;
  hash: string;
  format: "hf_datasets" | "jsonl" | "parquet";
  blobSha?: string;
  split?: string;
}

// --- W4-7: observability metrics ---

export interface OperatorMetrics {
  operator_name: string;
  runs: number;
  rows_in: number;
  rows_out: number;
  errors: number;
  duration_ms_total: number;
  duration_ms_avg: number;
}

export interface MetricsResponse {
  operators: OperatorMetrics[];
  collected_at: string;
}

export function useMetrics(opts?: { enabled?: boolean }) {
  return useQuery({
    queryKey: ["metrics"],
    queryFn: () => fetchJson<MetricsResponse>("/api/metrics"),
    refetchInterval: 5000,
    enabled: opts?.enabled ?? true,
  });
}

export function useSnapshotExport() {
  return useMutation({
    mutationFn: async (args: SnapshotExportArgs): Promise<SnapshotExportResult> => {
      const { owner, name, hash, format, blobSha, split } = args;
      const resp = await fetch(
        `/api/repos/${encodeURIComponent(owner)}/${encodeURIComponent(name)}/snapshots/${encodeURIComponent(hash)}/exports`,
        {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            format,
            blob_sha: blobSha ?? null,
            split: split ?? "train",
          }),
        },
      );
      if (!resp.ok) {
        let detail = `export failed ${resp.status}`;
        try {
          const j = await resp.json() as { detail?: string };
          if (j.detail) detail = j.detail;
        } catch {
          // ignore parse errors
        }
        throw new Error(detail);
      }
      const blob = await resp.blob();
      const rowCount = resp.headers.get("X-Snapshot-Row-Count");
      const blobShaHeader = resp.headers.get("X-Snapshot-Blob-Sha");
      return { blob, rowCount, blobSha: blobShaHeader };
    },
  });
}
