/**
 * 通用 silver/gold row 预览路由测试 (W4-2 web-row-preview-20260520 AC-3 + AC-4)
 *
 * 模式：vi.mock("../../../lib/api/queries", ...) + vi.mock("@tanstack/react-virtual", ...)
 *       + memory router（同 W4-1 pdf-mineru.test.tsx）
 */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  RouterProvider,
  createMemoryHistory,
  createRouter,
} from "@tanstack/react-router";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { routeTree } from "../../../routeTree.gen";

const FAKE_HASH = "a".repeat(64);
const FAKE_BLOB_SHA = "b".repeat(64);

const MOCK_ROWS = [
  {
    text: "silver row alpha text content here",
    images: [],
    source_ref: { blob_sha: "x".repeat(64), path: "doc1.pdf" },
    stats: { char_count: 34 },
    lineage_ops: [{ op: "pdf-extract", version: "3.1.0" }],
  },
  {
    text: "silver row beta text content here",
    images: [],
    source_ref: { blob_sha: "y".repeat(64), path: "doc2.pdf" },
    stats: { char_count: 33 },
    lineage_ops: [],
  },
  {
    text: "silver row gamma text content here",
    images: [],
    source_ref: { blob_sha: "z".repeat(64), path: "doc3.pdf" },
    stats: { char_count: 34 },
    lineage_ops: [],
  },
];

vi.mock("../../../lib/api/queries", () => ({
  useSnapshotRows: vi.fn(),
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
    data: null,
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
  useRepoRef: () => ({ data: null, isLoading: false, isError: false }),
  useSnapshot: () => ({
    data: {
      hash: FAKE_HASH,
      repo_id: "r1",
      tree_hash: "t".repeat(64),
      parent: null,
      author_id: "admin",
      created_at: "2026-05-20T00:00:00Z",
      message: "test snapshot",
      lineage: null,
      tree: {
        hash: "t".repeat(64),
        entries: [
          {
            name: "content/rows.jsonl",
            mode: 33188,
            entry_type: "blob",
            target_hash: FAKE_BLOB_SHA,
          },
        ],
      },
      deduplicated: false,
    },
    isLoading: false,
    isError: false,
    refetch: vi.fn(),
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

vi.mock("@tanstack/react-virtual", () => ({
  useVirtualizer: vi.fn((opts: { count: number }) => ({
    getVirtualItems: () =>
      Array.from({ length: opts.count }, (_, i) => ({
        key: i,
        index: i,
        start: i * 48,
        size: 48,
      })),
    getTotalSize: () => opts.count * 48,
  })),
}));

function renderRowsPage(initialUrl: string) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const history = createMemoryHistory({ initialEntries: [initialUrl] });
  const router = createRouter({ routeTree, history });
  return render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router as never} />
    </QueryClientProvider>,
  );
}

describe("/snapshots/$owner/$name/$hash/rows", () => {
  it("renders virtualized rows and expands row detail on click", async () => {
    const { useSnapshotRows } = await import("../../../lib/api/queries");
    (useSnapshotRows as ReturnType<typeof vi.fn>).mockReturnValue({
      data: {
        rows: MOCK_ROWS,
        total: 3,
        offset: 0,
        limit: 100,
        blob_sha: FAKE_BLOB_SHA,
      },
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });

    renderRowsPage(
      `/snapshots/demo/myrepo/${FAKE_HASH}/rows?blobSha=${FAKE_BLOB_SHA}`,
    );

    // 等待 3 个虚拟行渲染
    await waitFor(() => {
      expect(screen.getByTestId("row-0")).toBeInTheDocument();
      expect(screen.getByTestId("row-1")).toBeInTheDocument();
      expect(screen.getByTestId("row-2")).toBeInTheDocument();
    });

    // row-0 应含截断后的 text
    expect(screen.getByTestId("row-0").textContent).toContain(
      "silver row alpha",
    );

    // 点击 row-0 的 [详情] 按钮
    const detailButtons = screen.getAllByText("[详情]");
    expect(detailButtons.length).toBeGreaterThanOrEqual(1);
    fireEvent.click(detailButtons[0]!);

    // row-detail-0 应出现，含 source_ref / stats / lineage_ops
    const detailEl = await screen.findByTestId("row-detail-0");
    expect(detailEl).toBeInTheDocument();
    expect(detailEl.textContent).toContain("source_ref");
    expect(detailEl.textContent).toContain("lineage_ops");
    expect(detailEl.textContent).toContain("doc1.pdf");
  });

  it("empty snapshot shows placeholder and no virtual container", async () => {
    const { useSnapshotRows } = await import("../../../lib/api/queries");
    (useSnapshotRows as ReturnType<typeof vi.fn>).mockReturnValue({
      data: {
        rows: [],
        total: 0,
        offset: 0,
        limit: 100,
        blob_sha: "",
      },
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });

    renderRowsPage(`/snapshots/demo/myrepo/${FAKE_HASH}/rows`);

    // 等待占位文字出现
    await waitFor(() => {
      expect(
        screen.getByText(/无 silver\/gold 行可预览/),
      ).toBeInTheDocument();
    });

    // 虚拟化容器不应渲染
    expect(screen.queryByTestId("rows-virtual-container")).toBeNull();
  });

  it("shows error state with retry button", async () => {
    const { useSnapshotRows } = await import("../../../lib/api/queries");
    (useSnapshotRows as ReturnType<typeof vi.fn>).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      error: new Error("422: no .jsonl entry found"),
      refetch: vi.fn(),
    });

    renderRowsPage(`/snapshots/demo/myrepo/${FAKE_HASH}/rows`);

    await waitFor(() => {
      expect(screen.getByText(/加载失败/)).toBeInTheDocument();
    });

    // 重试按钮应存在
    expect(screen.getByRole("button", { name: /重试/ })).toBeInTheDocument();
  });
});
