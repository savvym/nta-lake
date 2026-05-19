import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  RouterProvider,
  createMemoryHistory,
  createRouter,
} from "@tanstack/react-router";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { routeTree } from "../routeTree.gen";

vi.mock("../lib/api/queries", () => ({
  useMe: () => ({
    data: {
      user_id: "u-admin",
      username: "admin",
      email: null,
      role: "admin",
      is_active: true,
    },
    refetch: vi.fn(),
  }),
  useRepo: () => ({
    data: {
      id: "r-1",
      owner: "demo",
      name: "files",
      layer: "bronze",
      subtype: "raw-md",
      visibility: "private",
      description: null,
      created_at: "2026-05-18T10:00:00Z",
      updated_at: "2026-05-18T10:00:00Z",
    },
    isLoading: false,
    isError: false,
    refetch: vi.fn(),
  }),
  useRepos: () => ({
    data: { items: [], total: 0 },
    isLoading: false,
    isError: false,
    refetch: vi.fn(),
  }),
  useRepoRef: () => ({
    data: null,
    isLoading: false,
    isError: false,
  }),
  useCommit: () => ({
    data: null,
    isLoading: false,
    isError: false,
  }),
  useSubtreeByPath: () => ({
    data: null,
    isLoading: false,
    isError: false,
    error: null,
  }),
  useUpdateRepo: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useDeleteRepo: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useEnqueueIngest: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useUploadBlob: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useCreatePipelineRun: () => ({ mutateAsync: vi.fn(), isPending: false }),
  usePipelineRun: () => ({ data: undefined, isLoading: false }),
  useBlobMeta: () => ({ data: undefined, isLoading: false, isError: false }),
}));

function renderRepoDetail(initialUrl: string) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const history = createMemoryHistory({ initialEntries: [initialUrl] });
  const router = createRouter({
    routeTree,
    history,
  });
  const view = render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router as never} />
    </QueryClientProvider>,
  );
  return { ...view, router, history };
}

describe("RepoDetailPage Tabs URL state", () => {
  it("clicking Pipelines tab updates URL to ?tab=pipelines", async () => {
    const { router } = renderRepoDetail("/repos/demo/files?tab=files");

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /demo\/files/ })).toBeInTheDocument();
    });

    const pipelinesTab = await screen.findByRole("tab", { name: "Pipelines" });
    fireEvent.click(pipelinesTab);

    await waitFor(() => {
      const search = router.state.location.search as { tab?: string };
      expect(search.tab).toBe("pipelines");
    });
  });
});
