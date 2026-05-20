import { createFileRoute, Link } from "@tanstack/react-router";

import { Button } from "../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { useJob } from "../../lib/api/queries";

export const Route = createFileRoute("/jobs/$job_id")({ component: JobPage });

const STATUS_COLORS: Record<string, string> = {
  queued: "bg-gray-100 text-gray-800",
  running: "bg-blue-100 text-blue-800",
  succeeded: "bg-green-100 text-green-800",
  failed: "bg-red-100 text-red-800",
};

function JobPage() {
  const { job_id } = Route.useParams();
  const { data, isLoading, isError, refetch } = useJob(job_id);

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
  if (!data) {
    return (
      <div className="flex flex-col items-start gap-2">
        <div className="text-gray-700">Job {job_id} 不存在或无权访问。</div>
      </div>
    );
  }

  const payload = data.payload as {
    owner?: string;
    name?: string;
    request?: { adapter_name?: string; adapter_version?: string };
  };
  const commitHash =
    (data.result?.commit_hash as string | undefined) ?? null;
  const dedup =
    (data.result?.deduplicated as boolean | undefined) ?? null;

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-semibold">Job</h1>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span className="truncate font-mono text-sm">{data.id}</span>
            <span
              className={`text-xs px-2 py-0.5 rounded-full ${STATUS_COLORS[data.status] ?? "bg-gray-100 text-gray-700"}`}
            >
              {data.status}
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-[8rem_1fr] gap-y-2 gap-x-4 text-sm">
            <dt className="text-gray-500">type</dt>
            <dd>{data.type}</dd>
            <dt className="text-gray-500">repo</dt>
            <dd>
              {payload.owner && payload.name ? (
                <Link
                  to="/repos/$owner/$name"
                  params={{ owner: payload.owner, name: payload.name }}
                  search={{ tab: "files", path: "" }}
                  className="text-blue-700 hover:underline"
                >
                  {payload.owner}/{payload.name}
                </Link>
              ) : (
                "—"
              )}
            </dd>
            <dt className="text-gray-500">adapter</dt>
            <dd>
              {payload.request?.adapter_name}@{payload.request?.adapter_version}
            </dd>
            <dt className="text-gray-500">created_at</dt>
            <dd>{new Date(data.created_at).toLocaleString()}</dd>
            <dt className="text-gray-500">started_at</dt>
            <dd>
              {data.started_at
                ? new Date(data.started_at).toLocaleString()
                : "—"}
            </dd>
            <dt className="text-gray-500">completed_at</dt>
            <dd>
              {data.completed_at
                ? new Date(data.completed_at).toLocaleString()
                : "—"}
            </dd>
          </dl>

          {data.status === "succeeded" && commitHash && payload.owner && payload.name && (
            <div className="mt-4 flex flex-col gap-2 border-t border-gray-200 pt-4">
              <div className="text-sm text-gray-500">commit_hash</div>
              <Link
                to="/commits/$owner/$name/$hash"
                params={{
                  owner: payload.owner,
                  name: payload.name,
                  hash: commitHash,
                }}
                className="font-mono text-sm text-blue-700 hover:underline break-all"
              >
                {commitHash}
              </Link>
              <div className="text-xs text-gray-500">
                deduplicated: {dedup === true ? "true (复用既有 commit)" : "false (新建)"}
              </div>
            </div>
          )}

          {data.status === "failed" && data.error && (
            <div className="mt-4 border-t border-red-200 pt-4">
              <div className="text-sm text-red-600 font-medium">error</div>
              <pre className="text-xs text-red-700 bg-red-50 p-2 rounded mt-1 whitespace-pre-wrap break-words">
                {data.error}
              </pre>
            </div>
          )}

          {(data.status === "queued" || data.status === "running") && (
            <div className="mt-4 text-xs text-gray-500">
              自动每秒刷新…
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
