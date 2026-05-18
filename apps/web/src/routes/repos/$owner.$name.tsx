import { createFileRoute, Link, useRouter } from "@tanstack/react-router";
import { useState } from "react";

import { Button } from "../../components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import { Textarea } from "../../components/ui/textarea";
import {
  useCommit,
  useCreatePipelineRun,
  useDeleteRepo,
  useEnqueueIngest,
  useMe,
  usePipelineRun,
  useRepoRef,
  useRepo,
  useUpdateRepo,
  useUploadBlob,
} from "../../lib/api/queries";

// URL search param: ?tab=files|ingest|pipelines （默认 files）
type TabKey = "files" | "ingest" | "pipelines";
const TAB_KEYS: readonly TabKey[] = ["files", "ingest", "pipelines"];

export const Route = createFileRoute("/repos/$owner/$name")({
  component: RepoDetailPage,
  validateSearch: (search: Record<string, unknown>): { tab: TabKey } => {
    const raw = String(search.tab ?? "");
    return {
      tab: (TAB_KEYS as readonly string[]).includes(raw)
        ? (raw as TabKey)
        : "files",
    };
  },
});

const VISIBILITIES = ["private", "internal", "public"] as const;

function RepoDetailPage() {
  const { owner, name } = Route.useParams();
  const search = Route.useSearch();
  const navigate = Route.useNavigate();
  const onTabChange = (t: TabKey) => navigate({ search: { tab: t } });
  const router = useRouter();
  const { data: me } = useMe();
  const { data: repo, isLoading, isError, refetch } = useRepo(owner, name);
  const isAdmin = me?.role === "admin";

  // 非 admin 直接访问 ?tab=ingest|pipelines URL 时，强制回退到 files
  // 防止 Tab Trigger 被 admin gate 隐藏 + Tab 面板被 hidden 后内容空白。
  const activeTab: TabKey =
    !isAdmin && search.tab !== "files" ? "files" : search.tab;

  const [editing, setEditing] = useState(false);

  if (isLoading) return <div className="text-gray-500">加载中…</div>;
  if (isError) {
    return (
      <div className="flex flex-col items-start gap-2">
        <div className="text-red-600">加载失败</div>
        <Button variant="outline" size="sm" onClick={() => refetch()}>
          重试
        </Button>
      </div>
    );
  }
  if (!repo) {
    return (
      <div className="flex flex-col items-start gap-2">
        <div className="text-gray-700">
          Repository {owner}/{name} 不存在或无权访问。
        </div>
        <Link to="/repos">
          <Button variant="outline" size="sm">
            回列表
          </Button>
        </Link>
      </div>
    );
  }

  const fields: { label: string; value: string }[] = [
    { label: "owner", value: repo.owner },
    { label: "name", value: repo.name },
    { label: "layer", value: repo.layer },
    { label: "subtype", value: repo.subtype },
    { label: "visibility", value: repo.visibility },
    { label: "description", value: repo.description ?? "—" },
    {
      label: "created_at",
      value: new Date(repo.created_at).toLocaleString(),
    },
    {
      label: "updated_at",
      value: new Date(repo.updated_at).toLocaleString(),
    },
  ];

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">
          {repo.owner}/{repo.name}
        </h1>
        <div className="flex gap-2">
          {isAdmin && !editing && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setEditing(true)}
            >
              Edit
            </Button>
          )}
          {isAdmin && (
            <DeleteRepoButton
              owner={owner}
              name={name}
              onDeleted={() => router.navigate({ to: "/repos" })}
            />
          )}
          <Link to="/repos">
            <Button variant="outline" size="sm">
              回列表
            </Button>
          </Link>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Metadata</CardTitle>
        </CardHeader>
        <CardContent>
          {editing ? (
            <EditRepoForm
              owner={owner}
              name={name}
              initial={{
                visibility: repo.visibility,
                description: repo.description ?? "",
              }}
              onSaved={() => {
                setEditing(false);
                refetch();
              }}
              onCancel={() => setEditing(false)}
            />
          ) : (
            <dl className="grid grid-cols-[8rem_1fr] gap-y-2 gap-x-4 text-sm">
              {fields.map((f) => (
                <div key={f.label} className="contents">
                  <dt className="text-gray-500">{f.label}</dt>
                  <dd className="text-gray-900 break-words">{f.value}</dd>
                </div>
              ))}
            </dl>
          )}
        </CardContent>
      </Card>

      <Tabs activeTab={activeTab} onChange={onTabChange} isAdmin={isAdmin} />

      <div hidden={activeTab !== "files"}>
        <FilesSection owner={owner} name={name} />
      </div>
      {isAdmin && (
        <>
          <div hidden={activeTab !== "ingest"}>
            <IngestSection owner={owner} name={name} />
          </div>
          <div hidden={activeTab !== "pipelines"}>
            <PipelinesSection owner={owner} name={name} />
          </div>
        </>
      )}
    </div>
  );
}

function Tabs({
  activeTab,
  onChange,
  isAdmin,
}: {
  activeTab: TabKey;
  onChange: (t: TabKey) => void;
  isAdmin: boolean;
}) {
  const tabs: { key: TabKey; label: string; adminOnly: boolean }[] = [
    { key: "files", label: "Files", adminOnly: false },
    { key: "ingest", label: "Ingest", adminOnly: true },
    { key: "pipelines", label: "Pipelines", adminOnly: true },
  ];
  return (
    <div className="border-b border-gray-200 flex gap-1" role="tablist">
      {tabs
        .filter((t) => !t.adminOnly || isAdmin)
        .map((t) => {
          const active = t.key === activeTab;
          return (
            <button
              key={t.key}
              role="tab"
              aria-selected={active}
              onClick={() => onChange(t.key)}
              className={
                "px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors " +
                (active
                  ? "border-blue-600 text-blue-700"
                  : "border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300")
              }
            >
              {t.label}
            </button>
          );
        })}
    </div>
  );
}

function FilesSection({ owner, name }: { owner: string; name: string }) {
  const refQuery = useRepoRef(owner, name, "main");
  const commitHash = refQuery.data?.commit_hash ?? "";
  const commitQuery = useCommit(owner, name, commitHash);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-3">
          <span>Files</span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-800">
            main
          </span>
          {commitQuery.data && (
            <span className="text-sm text-gray-500 font-normal">
              {commitQuery.data.tree.entries.length} files
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {refQuery.isLoading || commitQuery.isLoading ? (
          <div className="text-gray-500 text-sm">加载中…</div>
        ) : !refQuery.data ? (
          <div className="text-gray-500 text-sm">
            暂无 commit
            <span className="text-gray-400">（admin 可在 Ingest 区上传文件创建第一个 commit）</span>
          </div>
        ) : !commitQuery.data ? (
          <div className="text-red-600 text-sm">
            commit {refQuery.data.commit_hash.slice(0, 12)}… 加载失败
          </div>
        ) : commitQuery.data.tree.entries.length === 0 ? (
          <div className="text-gray-500 text-sm">commit 为空 tree</div>
        ) : (
          <>
            <div className="mb-3 text-sm text-gray-600 flex items-center gap-2">
              <Link
                to="/commits/$owner/$name/$hash"
                params={{
                  owner,
                  name,
                  hash: commitQuery.data.hash,
                }}
                className="font-mono text-xs text-blue-700 hover:underline"
              >
                {commitQuery.data.hash.slice(0, 8)}
              </Link>
              <span className="text-gray-700">
                {commitQuery.data.message ?? "(no message)"}
              </span>
              <span className="text-gray-400">·</span>
              <span className="text-gray-500 text-xs">
                {new Date(commitQuery.data.created_at).toLocaleString()}
              </span>
              <span className="text-gray-400">·</span>
              <span className="text-gray-500 text-xs">
                by {commitQuery.data.author_id}
              </span>
            </div>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left border-b border-gray-200">
                  <th className="py-2 pr-4 font-medium text-gray-600">path</th>
                  <th className="py-2 pr-4 font-medium text-gray-600">type</th>
                  <th className="py-2 pr-4 font-medium text-gray-600 font-mono">
                    sha256
                  </th>
                  <th className="py-2 font-medium text-gray-600 text-right">
                    操作
                  </th>
                </tr>
              </thead>
              <tbody>
                {commitQuery.data.tree.entries.map((e) => (
                  <tr
                    key={e.name}
                    className="border-b border-gray-100 hover:bg-gray-50"
                  >
                    <td className="py-2 pr-4 break-all">
                      <Link
                        to="/blob/$owner/$name/$hash"
                        params={{ owner, name, hash: e.target_hash }}
                        search={{ path: e.name }}
                        className="text-blue-700 hover:underline"
                      >
                        {e.name}
                      </Link>
                    </td>
                    <td className="py-2 pr-4 text-gray-500">{e.entry_type}</td>
                    <td className="py-2 pr-4 font-mono text-xs text-gray-500">
                      {e.target_hash.slice(0, 12)}…
                    </td>
                    <td className="py-2 text-right">
                      <a
                        href={`/api/repos/${encodeURIComponent(owner)}/${encodeURIComponent(name)}/blobs/${encodeURIComponent(e.target_hash)}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-700 hover:underline text-xs"
                      >
                        下载
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}
      </CardContent>
    </Card>
  );
}

function DeleteRepoButton({
  owner,
  name,
  onDeleted,
}: {
  owner: string;
  name: string;
  onDeleted: () => void;
}) {
  const deleteRepo = useDeleteRepo(owner, name);
  const handle = async () => {
    if (!window.confirm(`确定删除 ${owner}/${name}？此操作不可撤销。`)) return;
    try {
      await deleteRepo.mutateAsync();
      onDeleted();
    } catch (err) {
      const msg = err instanceof Error ? err.message : "删除失败";
      window.alert(msg);
    }
  };
  return (
    <Button
      variant="outline"
      size="sm"
      onClick={handle}
      disabled={deleteRepo.isPending}
      className="text-red-700 hover:bg-red-50"
    >
      {deleteRepo.isPending ? "删除中…" : "Delete"}
    </Button>
  );
}

function EditRepoForm({
  owner,
  name,
  initial,
  onSaved,
  onCancel,
}: {
  owner: string;
  name: string;
  initial: { visibility: string; description: string };
  onSaved: () => void;
  onCancel: () => void;
}) {
  const updateRepo = useUpdateRepo(owner, name);
  const [visibility, setVisibility] = useState(initial.visibility);
  const [description, setDescription] = useState(initial.description);
  const [error, setError] = useState<string | null>(null);

  const handle = async () => {
    setError(null);
    try {
      await updateRepo.mutateAsync({
        visibility,
        description: description || null,
      });
      onSaved();
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存失败");
    }
  };

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="edit-visibility">visibility</Label>
        <select
          id="edit-visibility"
          className="h-9 rounded-md border border-gray-300 bg-white px-2 text-sm w-48"
          value={visibility}
          onChange={(e) => setVisibility(e.target.value)}
        >
          {VISIBILITIES.map((v) => (
            <option key={v} value={v}>
              {v}
            </option>
          ))}
        </select>
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="edit-description">description</Label>
        <Textarea
          id="edit-description"
          rows={3}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
      </div>
      {error && <div className="text-sm text-red-600">{error}</div>}
      <div className="flex gap-2 justify-end">
        <Button variant="outline" size="sm" onClick={onCancel}>
          Cancel
        </Button>
        <Button size="sm" onClick={handle} disabled={updateRepo.isPending}>
          {updateRepo.isPending ? "保存中…" : "Save"}
        </Button>
      </div>
    </div>
  );
}

interface UploadedFile {
  file: File;
  path: string;
  sha256: string | null;
  status: "pending" | "uploading" | "uploaded" | "failed";
  error?: string;
}

function IngestSection({ owner, name }: { owner: string; name: string }) {
  const router = useRouter();
  const uploadBlob = useUploadBlob(owner, name);
  const enqueueIngest = useEnqueueIngest();
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [author, setAuthor] = useState("admin");
  const [ref, setRef] = useState("main");
  const [message, setMessage] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const onFiles = (list: FileList | null) => {
    if (!list) return;
    const newOnes: UploadedFile[] = Array.from(list).map((f) => ({
      file: f,
      path: `content/${f.name}`,
      sha256: null,
      status: "pending",
    }));
    setFiles((prev) => [...prev, ...newOnes]);
  };

  const updatePath = (idx: number, path: string) => {
    setFiles((prev) =>
      prev.map((f, i) => (i === idx ? { ...f, path } : f)),
    );
  };

  const remove = (idx: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== idx));
  };

  const submit = async () => {
    setError(null);
    if (files.length === 0) {
      setError("至少选 1 个文件");
      return;
    }
    if (!author.trim()) {
      setError("author 必填");
      return;
    }
    const paths = files.map((f) => f.path);
    if (new Set(paths).size !== paths.length) {
      setError("path 不允许重复");
      return;
    }
    setBusy(true);
    try {
      // 串行上传
      const uploaded: UploadedFile[] = [];
      for (let i = 0; i < files.length; i++) {
        const f = files[i];
        if (!f) continue;
        setFiles((prev) =>
          prev.map((x, j) => (j === i ? { ...x, status: "uploading" } : x)),
        );
        try {
          const result = await uploadBlob.mutateAsync(f.file);
          const updated: UploadedFile = {
            file: f.file,
            path: f.path,
            sha256: result.sha256,
            status: "uploaded",
          };
          uploaded.push(updated);
          setFiles((prev) => prev.map((x, j) => (j === i ? updated : x)));
        } catch (err) {
          const msg = err instanceof Error ? err.message : "上传失败";
          setFiles((prev) =>
            prev.map((x, j) =>
              j === i ? { ...x, status: "failed", error: msg } : x,
            ),
          );
          throw err;
        }
      }

      const job = await enqueueIngest.mutateAsync({
        owner,
        name,
        request: {
          adapter_name: "raw-file-upload",
          adapter_version: "0.1",
          spec: {
            files: uploaded.map((u) => ({
              path: u.path,
              sha256: u.sha256 as string,
            })),
          },
          author_id: author.trim(),
          message: message || null,
          ref: ref || null,
        },
      });
      if (job) {
        router.navigate({
          to: "/jobs/$job_id",
          params: { job_id: job.id },
        });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "ingest 失败");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Ingest 文件</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col gap-3">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="ingest-files">选文件（可多选）</Label>
            <Input
              id="ingest-files"
              type="file"
              multiple
              onChange={(e) => onFiles(e.target.files)}
            />
          </div>
          {files.length > 0 && (
            <div className="flex flex-col gap-2">
              <Label>文件 → 仓库 path 映射</Label>
              <div className="flex flex-col gap-1.5 text-sm">
                {files.map((f, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <span className="text-gray-500 truncate w-40">
                      {f.file.name}
                    </span>
                    <span className="text-gray-400">→</span>
                    <Input
                      value={f.path}
                      onChange={(e) => updatePath(i, e.target.value)}
                      className="flex-1"
                    />
                    <span className="text-xs w-24 text-right">
                      {f.status === "uploaded" ? (
                        <span className="text-green-700">上传完</span>
                      ) : f.status === "uploading" ? (
                        <span className="text-blue-700">上传中</span>
                      ) : f.status === "failed" ? (
                        <span className="text-red-600">失败</span>
                      ) : (
                        <span className="text-gray-400">待上传</span>
                      )}
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => remove(i)}
                      disabled={busy}
                    >
                      ×
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="ingest-author">author_id</Label>
              <Input
                id="ingest-author"
                value={author}
                onChange={(e) => setAuthor(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="ingest-ref">ref（可选）</Label>
              <Input
                id="ingest-ref"
                value={ref}
                onChange={(e) => setRef(e.target.value)}
                placeholder="main"
              />
            </div>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="ingest-message">message（可选）</Label>
            <Input
              id="ingest-message"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
            />
          </div>
          {error && <div className="text-sm text-red-600">{error}</div>}
          <div className="flex justify-end">
            <Button onClick={submit} disabled={busy || files.length === 0}>
              {busy ? "提交中…" : "上传 + Ingest"}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// --- pipeline-ui-tab-20260518 ---

const DEMO_RECIPE_YAML = `name: demo-bronze-to-gold

nodes:
  - id: normalize
    processor: markdown-normalize@0.1
    inputs:
      - bronze/demo/raw-md@main
    config: {}
    output: silver/demo/normalized-md@auto

  - id: qa_gen
    processor: llm-qa-gen@0.1
    inputs:
      - "@normalize"
    config:
      model_id: claude-opus-4-7
      records_per_doc: 2
    output: gold/demo/sft@auto
`;

export function PipelinesSection({
  owner,
  name,
}: {
  owner: string;
  name: string;
}) {
  void owner;
  void name;
  const [yamlText, setYamlText] = useState("");
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const createRun = useCreatePipelineRun();
  const runQuery = usePipelineRun(activeRunId);

  const submit = async () => {
    setError(null);
    try {
      const res = await createRun.mutateAsync(yamlText);
      setActiveRunId(res.run_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "运行 pipeline 失败");
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Pipelines</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <Label htmlFor="pipeline-yaml">Recipe YAML</Label>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setYamlText(DEMO_RECIPE_YAML)}
              disabled={createRun.isPending}
            >
              粘贴 demo recipe
            </Button>
          </div>
          <Textarea
            id="pipeline-yaml"
            rows={12}
            value={yamlText}
            onChange={(e) => setYamlText(e.target.value)}
            placeholder="name: my-pipeline\nnodes: ..."
            className="font-mono text-xs"
          />
          {error && <div className="text-sm text-red-600">{error}</div>}
          <div className="flex justify-end">
            <Button
              onClick={submit}
              disabled={!yamlText.trim() || createRun.isPending}
            >
              {createRun.isPending ? "提交中…" : "运行 Pipeline"}
            </Button>
          </div>

          {activeRunId && (
            <div className="flex flex-col gap-2 border-t border-gray-200 pt-3 mt-2">
              <div className="flex items-center gap-2 text-sm">
                <span className="text-gray-500">Run:</span>
                <span className="font-mono text-xs">
                  {activeRunId.slice(0, 12)}…
                </span>
                {runQuery.data && (
                  <span
                    className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                      runQuery.data.status === "succeeded"
                        ? "bg-green-100 text-green-800"
                        : runQuery.data.status === "failed"
                          ? "bg-red-100 text-red-800"
                          : "bg-blue-100 text-blue-800"
                    }`}
                  >
                    {runQuery.data.status}
                  </span>
                )}
              </div>
              {runQuery.data?.error && (
                <pre className="text-xs text-red-700 bg-red-50 p-2 rounded max-h-32 overflow-auto whitespace-pre-wrap">
                  {runQuery.data.error}
                </pre>
              )}
              {runQuery.data && runQuery.data.node_runs.length > 0 && (
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-left border-b border-gray-200">
                      <th className="py-1 pr-2 font-medium text-gray-600">
                        node
                      </th>
                      <th className="py-1 pr-2 font-medium text-gray-600">
                        processor
                      </th>
                      <th className="py-1 pr-2 font-medium text-gray-600">
                        status
                      </th>
                      <th className="py-1 pr-2 font-medium text-gray-600">
                        cache
                      </th>
                      <th className="py-1 font-medium text-gray-600 font-mono">
                        output_commit
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {runQuery.data.node_runs.map((n) => (
                      <tr
                        key={n.node_id}
                        className="border-b border-gray-100 hover:bg-gray-50"
                      >
                        <td className="py-1 pr-2 font-medium">{n.node_id}</td>
                        <td className="py-1 pr-2 text-gray-700">
                          {n.processor_name}@{n.processor_version}
                        </td>
                        <td className="py-1 pr-2">
                          <span
                            className={
                              n.status === "succeeded"
                                ? "text-green-700"
                                : n.status === "failed"
                                  ? "text-red-700"
                                  : "text-blue-700"
                            }
                          >
                            {n.status}
                          </span>
                        </td>
                        <td className="py-1 pr-2 text-gray-500">
                          {n.cache_hit ? "hit" : "miss"}
                        </td>
                        <td className="py-1 font-mono text-gray-500">
                          {n.output_commit_hash
                            ? `${n.output_commit_hash.slice(0, 12)}…`
                            : "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
