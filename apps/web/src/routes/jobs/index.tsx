import { createFileRoute, Link } from "@tanstack/react-router";
import { useQueryClient } from "@tanstack/react-query";
import { z } from "zod";

import { Button } from "../../components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import { Label } from "../../components/ui/label";
import { useJobs, useMe } from "../../lib/api/queries";

const searchSchema = z.object({
  status: z.string().catch("").default(""),
  type: z.string().catch("").default(""),
  limit: z.coerce.number().int().positive().max(200).catch(50).default(50),
  offset: z.coerce.number().int().nonnegative().catch(0).default(0),
});

export const Route = createFileRoute("/jobs/")({
  component: JobsListPage,
  validateSearch: (search: Record<string, unknown>) => searchSchema.parse(search),
});

const STATUS_OPTIONS = ["", "queued", "running", "succeeded", "failed"] as const;
const TYPE_OPTIONS = ["", "ingest", "process", "pipeline"] as const;
const LIMIT_OPTIONS = [25, 50, 100] as const;

function JobsListPage() {
  // 所有 hooks 必须在 early return 之前调用（React Rules of Hooks）：
  // useMe 首屏 me=undefined → early return；下次 me 解析 → 多调用 useJobs，会触发
  // "Rendered more hooks than during the previous render"。统一拉到顶。
  const { data: me } = useMe();
  const search = Route.useSearch();
  const navigate = Route.useNavigate();
  const qc = useQueryClient();
  const isAdmin = me?.role === "admin";
  const jobsQuery = useJobs(
    {
      status: search.status || undefined,
      type: search.type || undefined,
      limit: search.limit,
      offset: search.offset,
    },
    { enabled: isAdmin },
  );

  const setSearch = (patch: Partial<typeof search>) => {
    navigate({ search: { ...search, ...patch } });
  };

  if (!me) {
    return (
      <Card>
        <CardContent className="py-6">
          <div className="text-gray-500">未登录。</div>
          <Link to="/login" className="text-blue-700 hover:underline">
            去登录
          </Link>
        </CardContent>
      </Card>
    );
  }
  if (!isAdmin) {
    return (
      <Card>
        <CardContent className="py-6">
          <div className="text-red-600 mb-2">仅 admin 可见 Jobs 列表。</div>
          <Link to="/" className="text-blue-700 hover:underline">
            返回首页
          </Link>
        </CardContent>
      </Card>
    );
  }

  const items = jobsQuery.data?.items ?? [];
  const total = jobsQuery.data?.total ?? 0;
  const pageStart = search.offset + 1;
  const pageEnd = search.offset + items.length;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-3">
          <span>Jobs</span>
          {jobsQuery.data && (
            <span className="text-sm text-gray-500 font-normal">
              {pageStart}-{pageEnd} of {total}
            </span>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={() => qc.invalidateQueries({ queryKey: ["jobs"] })}
          >
            ↻ Refresh
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap items-end gap-4 mb-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="filter-status">status</Label>
            <select
              id="filter-status"
              value={search.status}
              onChange={(e) => setSearch({ status: e.target.value, offset: 0 })}
              className="border border-gray-300 rounded px-2 py-1 text-sm"
            >
              {STATUS_OPTIONS.map((s) => (
                <option key={s || "all"} value={s}>
                  {s || "(all)"}
                </option>
              ))}
            </select>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="filter-type">type</Label>
            <select
              id="filter-type"
              value={search.type}
              onChange={(e) => setSearch({ type: e.target.value, offset: 0 })}
              className="border border-gray-300 rounded px-2 py-1 text-sm"
            >
              {TYPE_OPTIONS.map((t) => (
                <option key={t || "all"} value={t}>
                  {t || "(all)"}
                </option>
              ))}
            </select>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="filter-limit">page size</Label>
            <select
              id="filter-limit"
              value={search.limit}
              onChange={(e) =>
                setSearch({ limit: Number(e.target.value), offset: 0 })
              }
              className="border border-gray-300 rounded px-2 py-1 text-sm"
            >
              {LIMIT_OPTIONS.map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </div>
        </div>

        {jobsQuery.isLoading ? (
          <div className="text-gray-500">加载中…</div>
        ) : jobsQuery.isError ? (
          <div className="text-red-600">
            加载失败：{String(jobsQuery.error)}
          </div>
        ) : items.length === 0 ? (
          <div className="text-gray-500">无 jobs</div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left border-b border-gray-200">
                <th className="py-2 pr-4 font-medium text-gray-600">created</th>
                <th className="py-2 pr-4 font-medium text-gray-600">id</th>
                <th className="py-2 pr-4 font-medium text-gray-600">type</th>
                <th className="py-2 pr-4 font-medium text-gray-600">status</th>
                <th className="py-2 pr-4 font-medium text-gray-600">payload</th>
                <th className="py-2 pr-4 font-medium text-gray-600">duration</th>
              </tr>
            </thead>
            <tbody>
              {items.map((j) => (
                <tr
                  key={j.id}
                  className="border-b border-gray-100 hover:bg-gray-50"
                >
                  <td className="py-2 pr-4 text-gray-500 whitespace-nowrap">
                    {formatRelativeTime(j.created_at)}
                  </td>
                  <td className="py-2 pr-4 font-mono text-xs">
                    <Link
                      to="/jobs/$job_id"
                      params={{ job_id: j.id }}
                      className="text-blue-700 hover:underline"
                    >
                      {j.id.slice(0, 8)}
                    </Link>
                  </td>
                  <td className="py-2 pr-4 text-gray-700">{j.type}</td>
                  <td className="py-2 pr-4">
                    <StatusBadge status={j.status} />
                  </td>
                  <td className="py-2 pr-4 text-gray-500 text-xs truncate max-w-xs">
                    {summarizePayload(j.payload)}
                  </td>
                  <td className="py-2 pr-4 text-gray-500 text-xs whitespace-nowrap">
                    {formatDuration(j.started_at, j.completed_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        <div className="mt-4 flex items-center justify-between text-sm">
          <Button
            variant="outline"
            size="sm"
            disabled={search.offset === 0}
            onClick={() =>
              setSearch({
                offset: Math.max(0, search.offset - search.limit),
              })
            }
          >
            ← 上一页
          </Button>
          <span className="text-gray-500">
            {pageStart}-{pageEnd} of {total}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={pageEnd >= total}
            onClick={() => setSearch({ offset: search.offset + search.limit })}
          >
            下一页 →
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function StatusBadge({ status }: { status: string }) {
  const cls =
    status === "succeeded"
      ? "bg-green-100 text-green-800"
      : status === "failed"
        ? "bg-red-100 text-red-800"
        : status === "running"
          ? "bg-blue-100 text-blue-800"
          : "bg-gray-100 text-gray-700";
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full ${cls}`}>{status}</span>
  );
}

function formatRelativeTime(iso: string): string {
  const t = new Date(iso).getTime();
  const diff = Date.now() - t;
  const sec = Math.floor(diff / 1000);
  if (sec < 60) return `${sec}s ago`;
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min}m ago`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h ago`;
  return new Date(iso).toLocaleDateString();
}

function formatDuration(
  startedAt: string | null,
  completedAt: string | null,
): string {
  if (!startedAt) return "—";
  const end = completedAt ? new Date(completedAt).getTime() : Date.now();
  const sec = Math.floor((end - new Date(startedAt).getTime()) / 1000);
  if (sec < 60) return `${sec}s`;
  return `${Math.floor(sec / 60)}m ${sec % 60}s`;
}

function summarizePayload(payload: Record<string, unknown>): string {
  if (!payload) return "";
  const owner = (payload.owner ?? payload.source_owner) as string | undefined;
  const name = (payload.name ?? payload.source_name) as string | undefined;
  if (owner && name) return `${owner}/${name}`;
  const keys = Object.keys(payload).slice(0, 3).join(", ");
  return keys ? `{${keys}…}` : "{}";
}
