/**
 * PDF → Silver Row UI v2 route 测试（W4-1 web-pdf-mineru-ui-v2-20260520 AC-4）
 *
 * 模式：vi.mock("../lib/api/queries", ...) + memory router（同 repos.tabs.test.tsx）
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

const MOCK_ROWS = [
  {
    text: "row text one",
    images: [],
    source_ref: { blob_sha: "x".repeat(64), path: "page1.pdf" },
    stats: { char_count: 12 },
    lineage_ops: [],
  },
  {
    text: "row text two",
    images: [],
    source_ref: { blob_sha: "y".repeat(64), path: "page2.pdf" },
    stats: { char_count: 12 },
    lineage_ops: [],
  },
  {
    text: "row text three",
    images: [],
    source_ref: { blob_sha: "z".repeat(64), path: "page3.pdf" },
    stats: { char_count: 14 },
    lineage_ops: [],
  },
];

vi.mock("../../../lib/api/queries", () => ({
  // 新 hook
  useSnapshotRows: () => ({
    data: {
      rows: MOCK_ROWS,
      total: 3,
      offset: 0,
      limit: 50,
      blob_sha: "b".repeat(64),
    },
    isLoading: false,
    isError: false,
    error: null,
    refetch: vi.fn(),
  }),
  // 现有 hooks（其他路由所需）
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
      layer: "silver",
      subtype: "text-corpus",
      visibility: "public",
      description: null,
      created_at: "2026-05-20T00:00:00Z",
      updated_at: "2026-05-20T00:00:00Z",
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
  useRepoRef: () => ({ data: null, isLoading: false, isError: false }),
  useSnapshot: () => ({ data: null, isLoading: false, isError: false }),
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

function renderPdfMineruPage(initialUrl: string) {
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

describe("/repos/$owner/$name/pdf-mineru", () => {
  it("renders 3 rows table from useSnapshotRows", async () => {
    renderPdfMineruPage(
      `/repos/demo/files/pdf-mineru?snapshot=${FAKE_HASH}`,
    );

    await waitFor(() => {
      // 表格应含至少 3 行内容
      expect(screen.getByText("row text one")).toBeInTheDocument();
      expect(screen.getByText("row text two")).toBeInTheDocument();
      expect(screen.getByText("row text three")).toBeInTheDocument();
    });
  });

  it("clicking detail button expands row JSON", async () => {
    renderPdfMineruPage(
      `/repos/demo/files/pdf-mineru?snapshot=${FAKE_HASH}`,
    );

    // 等待表格渲染
    await waitFor(() => {
      expect(screen.getByText("row text one")).toBeInTheDocument();
    });

    // 点第 1 个 [详情] 按钮（idx=0）
    const detailButtons = screen.getAllByText("[详情]");
    expect(detailButtons.length).toBeGreaterThanOrEqual(1);
    fireEvent.click(detailButtons[0]!);

    // 等待详情 pre 出现
    const detailEl = await screen.findByTestId("row-detail-0");
    expect(detailEl).toBeInTheDocument();
    expect(detailEl.textContent).toContain("source_ref");
  });
});
