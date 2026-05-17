/** Router smoke test：mock useMe / useRepos / useRepo，验证 layout + 重定向。 */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider, createMemoryHistory, createRouter } from "@tanstack/react-router";
import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { routeTree } from "./routeTree.gen";

vi.mock("./lib/api/queries", () => ({
  useMe: () => ({ data: null, refetch: vi.fn() }),
  useRepos: () => ({
    data: { items: [], total: 0 },
    isLoading: false,
    isError: false,
    refetch: vi.fn(),
  }),
  useRepo: () => ({ data: null, isLoading: false, isError: false, refetch: vi.fn() }),
}));

function renderAt(path: string) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const router = createRouter({
    routeTree,
    history: createMemoryHistory({ initialEntries: [path] }),
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router as never} />
    </QueryClientProvider>,
  );
}

afterEach(() => vi.clearAllMocks());

describe("App router smoke", () => {
  it("/ redirects to /repos and shows empty state", async () => {
    renderAt("/");
    await waitFor(() => {
      expect(screen.getByText(/暂无 repository/)).toBeInTheDocument();
    });
  });

  it("root layout shows dataplat brand and login link when anonymous", async () => {
    renderAt("/repos");
    await waitFor(() => {
      expect(screen.getByText("dataplat")).toBeInTheDocument();
      expect(screen.getByText("login")).toBeInTheDocument();
    });
  });
});
