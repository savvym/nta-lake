import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  RouterProvider,
  createMemoryHistory,
  createRouter,
} from "@tanstack/react-router";
import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { routeTree } from "../../routeTree.gen";

const FAKE_HASH = "f".repeat(64);
const FAKE_TARGET = "1".repeat(64);

vi.mock("../../lib/api/queries", () => ({
  useMe: () => ({ data: null, refetch: vi.fn() }),
  useRepos: () => ({ data: { items: [], total: 0 }, isLoading: false, isError: false, refetch: vi.fn() }),
  useRepo: () => ({ data: null, isLoading: false, isError: false, refetch: vi.fn() }),
  useJob: () => ({ data: null, isLoading: false, isError: false, refetch: vi.fn() }),
  useSnapshot: () => ({
    data: {
      hash: FAKE_HASH,
      repo_id: "r1",
      tree_hash: "t".repeat(64),
      parent: null,
      author_id: "admin",
      created_at: "2026-05-17T00:00:00Z",
      message: "init",
      lineage: null,
      tree: {
        hash: "t".repeat(64),
        entries: [
          { name: "content/a.md", mode: 33188, entry_type: "blob", target_hash: FAKE_TARGET },
        ],
      },
      deduplicated: false,
    },
    isLoading: false,
    isError: false,
    refetch: vi.fn(),
  }),
}));

function renderSnapshot() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const router = createRouter({
    routeTree,
    history: createMemoryHistory({
      initialEntries: [`/snapshots/demo/r1/${FAKE_HASH}`],
    }),
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router as never} />
    </QueryClientProvider>,
  );
}

describe("/snapshots/$owner/$name/$hash", () => {
  it("renders metadata + tree entries with download link", async () => {
    renderSnapshot();
    await waitFor(() => {
      expect(screen.getByText("content/a.md")).toBeInTheDocument();
      const links = screen.getAllByText("下载");
      expect(links.length).toBeGreaterThan(0);
      // 下载链 href 含 blob sha256
      expect(
        (links[0] as HTMLAnchorElement).getAttribute("href"),
      ).toContain(FAKE_TARGET);
    });
  });
});
