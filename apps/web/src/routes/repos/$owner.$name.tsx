import { createFileRoute, Link } from "@tanstack/react-router";

import { Button } from "../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { useRepo } from "../../lib/api/queries";

export const Route = createFileRoute("/repos/$owner/$name")({ component: RepoDetailPage });

function RepoDetailPage() {
  const { owner, name } = Route.useParams();
  const { data: repo, isLoading, isError, refetch } = useRepo(owner, name);

  if (isLoading) return <div className="text-gray-500">加载中…</div>;
  if (isError) {
    return (
      <div className="flex flex-col items-start gap-2">
        <div className="text-red-600">加载失败</div>
        <Button variant="outline" size="sm" onClick={() => refetch()}>重试</Button>
      </div>
    );
  }
  if (!repo) {
    return (
      <div className="flex flex-col items-start gap-2">
        <div className="text-gray-700">Repository {owner}/{name} 不存在或无权访问。</div>
        <Link to="/repos"><Button variant="outline" size="sm">回列表</Button></Link>
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
    { label: "created_at", value: new Date(repo.created_at).toLocaleString() },
    { label: "updated_at", value: new Date(repo.updated_at).toLocaleString() },
  ];

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">{repo.owner}/{repo.name}</h1>
        <Link to="/repos"><Button variant="outline" size="sm">回列表</Button></Link>
      </div>
      <Card>
        <CardHeader><CardTitle>Metadata</CardTitle></CardHeader>
        <CardContent>
          <dl className="grid grid-cols-[8rem_1fr] gap-y-2 gap-x-4 text-sm">
            {fields.map((f) => (
              <div key={f.label} className="contents">
                <dt className="text-gray-500">{f.label}</dt>
                <dd className="text-gray-900 break-words">{f.value}</dd>
              </div>
            ))}
          </dl>
        </CardContent>
      </Card>
    </div>
  );
}
