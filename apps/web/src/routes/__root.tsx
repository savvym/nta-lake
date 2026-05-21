import { createRootRoute, Link, Outlet, useRouter } from "@tanstack/react-router";

import { Button } from "../components/ui/button";
import { fetchJson } from "../lib/api/client";
import { useMe } from "../lib/api/queries";

export const Route = createRootRoute({ component: RootLayout });

function RootLayout() {
  const { data: me, refetch } = useMe();
  const router = useRouter();

  const handleLogout = async () => {
    try {
      await fetchJson("/api/auth/logout", { method: "POST" });
    } catch {
      // 即便后端 logout 失败也清前端态
    }
    await refetch();
    router.navigate({ to: "/login" });
  };

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto max-w-6xl px-4 py-3 flex items-center justify-between">
          <Link to="/" className="font-semibold text-lg text-gray-900">
            dataplat
          </Link>
          <div className="flex items-center gap-3">
            {me ? (
              <>
                <Link
                  to="/repos"
                  className="text-sm text-gray-700 hover:underline"
                >
                  Repos
                </Link>
                {me.role === "admin" && (
                  <Link
                    to="/repos/new"
                    className="text-sm text-gray-700 hover:underline"
                  >
                    New Repo
                  </Link>
                )}
                {me.role === "admin" && (
                  <>
                    <Link
                      to="/jobs"
                      search={{ status: "", type: "", limit: 50, offset: 0 }}
                      className="text-sm text-gray-700 hover:underline"
                    >
                      Jobs
                    </Link>
                    <Link
                      to="/observability"
                      className="text-sm text-gray-700 hover:underline"
                    >
                      Observability
                    </Link>
                  </>
                )}
                <Link
                  to="/recipes/builder"
                  search={{}}
                  className="text-sm text-gray-700 hover:underline"
                >
                  Recipes Builder
                </Link>
                <span className="text-sm text-gray-600">{me.username}</span>
                <Button variant="outline" size="sm" onClick={handleLogout}>
                  logout
                </Button>
              </>
            ) : (
              <Link to="/login" className="text-sm text-gray-700 hover:underline">
                login
              </Link>
            )}
          </div>
        </div>
      </header>
      <main className="flex-1 mx-auto max-w-6xl w-full px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}
