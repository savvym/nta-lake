import { createFileRoute, Link } from "@tanstack/react-router";

import { Button } from "../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { useMe, useRepos } from "../../lib/api/queries";

export const Route = createFileRoute("/repos/")({ component: ReposListPage });

const LAYER_COLORS: Record<string, string> = {
  bronze: "bg-amber-100 text-amber-800",
  silver: "bg-slate-100 text-slate-800",
  gold: "bg-yellow-100 text-yellow-800",
};

function ReposListPage() {
  const { data: me } = useMe();
  const { data, isLoading, isError, refetch } = useRepos();
  const isAdmin = me?.role === "admin";

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Repositories</h1>
        {isAdmin && (
          <Link to="/repos/new">
            <Button>+ New Repository</Button>
          </Link>
        )}
      </div>
      {isLoading ? (
        <div className="text-gray-500">加载中…</div>
      ) : isError || !data ? (
        <div className="flex flex-col items-start gap-2">
          <div className="text-red-600">加载失败</div>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            重试
          </Button>
        </div>
      ) : data.items.length === 0 ? (
        <div className="text-gray-500">暂无 repository</div>
      ) : (
        <div className="grid gap-3 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
          {data.items.map((r) => (
            <Link
              key={r.id}
              to="/repos/$owner/$name"
              params={{ owner: r.owner, name: r.name }}
              search={{ tab: "files", path: "" }}
              className="block"
            >
              <Card className="hover:shadow-md transition-shadow">
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span className="truncate">
                      {r.owner}/{r.name}
                    </span>
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full ${LAYER_COLORS[r.layer] ?? "bg-gray-100 text-gray-700"}`}
                    >
                      {r.layer}
                    </span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-xs text-gray-500 flex gap-2">
                    <span>{r.subtype}</span>
                    <span>·</span>
                    <span>{r.visibility}</span>
                    <span>·</span>
                    <span>{new Date(r.created_at).toLocaleDateString()}</span>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
