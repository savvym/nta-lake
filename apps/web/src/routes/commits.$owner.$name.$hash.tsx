import { createFileRoute, Link } from "@tanstack/react-router";

import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { useCommit } from "../lib/api/queries";

export const Route = createFileRoute("/commits/$owner/$name/$hash")({
  component: CommitPage,
});

function CommitPage() {
  const { owner, name, hash } = Route.useParams();
  const { data, isLoading, isError, refetch } = useCommit(owner, name, hash);

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
        <div className="text-gray-700">
          Commit {hash} 在 {owner}/{name} 不存在或无权访问。
        </div>
        <Link to="/repos/$owner/$name" params={{ owner, name }} search={{ tab: "files", path: "" }}>
          <Button variant="outline" size="sm">
            回 repo
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Commit</h1>
          <div className="font-mono text-sm text-gray-500 break-all">
            {data.hash}
          </div>
        </div>
        <Link to="/repos/$owner/$name" params={{ owner, name }} search={{ tab: "files", path: "" }}>
          <Button variant="outline" size="sm">
            回 {owner}/{name}
          </Button>
        </Link>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Metadata</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-[8rem_1fr] gap-y-2 gap-x-4 text-sm">
            <dt className="text-gray-500">author</dt>
            <dd>{data.author_id}</dd>
            <dt className="text-gray-500">message</dt>
            <dd>{data.message ?? "—"}</dd>
            <dt className="text-gray-500">created_at</dt>
            <dd>{new Date(data.created_at).toLocaleString()}</dd>
            <dt className="text-gray-500">tree_hash</dt>
            <dd className="font-mono text-xs break-all">{data.tree_hash}</dd>
            <dt className="text-gray-500">parents</dt>
            <dd>
              {data.parents.length === 0 ? (
                <span className="text-gray-400">（root commit）</span>
              ) : (
                <ul className="flex flex-col gap-1">
                  {data.parents.map((p) => (
                    <li key={p}>
                      <Link
                        to="/commits/$owner/$name/$hash"
                        params={{ owner, name, hash: p }}
                        className="font-mono text-xs text-blue-700 hover:underline break-all"
                      >
                        {p}
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </dd>
            <dt className="text-gray-500">lineage</dt>
            <dd>
              {data.lineage ? (
                <pre className="text-xs bg-gray-50 p-2 rounded overflow-auto">
                  {JSON.stringify(data.lineage, null, 2)}
                </pre>
              ) : (
                <span className="text-gray-400">—</span>
              )}
            </dd>
          </dl>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>
            Tree entries ({data.tree.entries.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {data.tree.entries.length === 0 ? (
            <div className="text-gray-500 text-sm">empty tree</div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left border-b border-gray-200">
                  <th className="py-2 pr-4">path</th>
                  <th className="py-2 pr-4">type</th>
                  <th className="py-2 pr-4 font-mono">sha256</th>
                  <th className="py-2">操作</th>
                </tr>
              </thead>
              <tbody>
                {data.tree.entries.map((e) => (
                  <tr key={e.name} className="border-b border-gray-100">
                    <td className="py-2 pr-4">{e.name}</td>
                    <td className="py-2 pr-4 text-gray-500">{e.entry_type}</td>
                    <td className="py-2 pr-4 font-mono text-xs text-gray-500">
                      {e.target_hash.slice(0, 12)}…
                    </td>
                    <td className="py-2">
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
          )}
        </CardContent>
      </Card>
    </div>
  );
}
