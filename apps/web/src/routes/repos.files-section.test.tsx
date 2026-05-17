import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  RouterProvider,
  createMemoryHistory,
  createRouter,
} from "@tanstack/react-router";
import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { routeTree } from "../routeTree.gen";

const FAKE_COMMIT_HASH = "c".repeat(64);
const SHA_A = "a".repeat(64);
const SHA_B = "b".repeat(64);

vi.mock("../lib/api/queries", () => ({
  useMe: () => ({
    data: { user_id: "1", username: "admin", email: null, role: "admin", is_active: true },
    refetch: vi.fn(),
  }),
  useRepos: () => ({ data: { items: [], total: 0 }, isLoading: false, isError: false, refetch: vi.fn() }),
  useRepo: () => ({
    data: {
      id: "r1",
      owner: "demo",
      name: "test",
      layer: "bronze",
      subtype: "pdf",
      visibility: "public",
      description: null,
      created_at: "2026-05-17T00:00:00Z",
      updated_at: "2026-05-17T00:00:00Z",
    },
    isLoading: false,
    isError: false,
    refetch: vi.fn(),
  }),
  useRepoRef: () => ({
    data: { name: "main", commit_hash: FAKE_COMMIT_HASH },
    isLoading: false,
    isError: false,
  }),
  useCommit: () => ({
    data: {
      hash: FAKE_COMMIT_HASH,
      repo_id: "r1",
      tree_hash: "t".repeat(64),
      parents: [],
      author_id: "admin",
      created_at: "2026-05-17T00:00:00Z",
      message: "init",
      lineage: null,
      tree: {
        hash: "t".repeat(64),
        entries: [
          { name: "content/a.md", mode: 33188, entry_type: "blob", target_hash: SHA_A },
          { name: "content/b.md", mode: 33188, entry_type: "blob", target_hash: SHA_B },
        ],
      },
      deduplicated: false,
    },
    isLoading: false,
    isError: false,
    refetch: vi.fn(),
  }),
  useDeleteRepo: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useUpdateRepo: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useUploadBlob: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useEnqueueIngest: () => ({ mutateAsync: vi.fn(), isPending: false }),
}));

function renderDetail() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const router = createRouter({
    routeTree,
    history: createMemoryHistory({ initialEntries: ["/repos/demo/test"] }),
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router as never} />
    </QueryClientProvider>,
  );
}

describe("repo detail Files section", () => {
  it("renders main badge + file count + entries with download links", async () => {
    renderDetail();
    await waitFor(() => {
      // main 徽章
      expect(screen.getByText("main")).toBeInTheDocument();
      // 文件计数
      expect(screen.getByText("2 files")).toBeInTheDocument();
      // 两个 entry 的 path
      expect(screen.getByText("content/a.md")).toBeInTheDocument();
      expect(screen.getByText("content/b.md")).toBeInTheDocument();
      // 下载链 href 含 blob sha
      const links = screen.getAllByText("下载");
      expect(links.length).toBe(2);
      const hrefs = links.map(
        (l) => (l as HTMLAnchorElement).getAttribute("href") ?? "",
      );
      expect(hrefs.some((h) => h.includes(SHA_A))).toBe(true);
      expect(hrefs.some((h) => h.includes(SHA_B))).toBe(true);
    });
  });
});
