/**
 * Snapshot export UI 测试（W4-4 web-snapshot-export-ui-20260520 AC-4）
 *
 * vi.mock useSnapshotExport
 * - "renders format select with default hf_datasets"
 * - "triggers export and shows result panel"（AC-4）
 */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  RouterProvider,
  createMemoryHistory,
  createRouter,
} from "@tanstack/react-router";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { routeTree } from "../../../../../routeTree.gen";

// jsdom 不支持 URL.createObjectURL / revokeObjectURL，mock 掉避免 unhandled error
if (!URL.createObjectURL) {
  URL.createObjectURL = vi.fn(() => "blob:mock-url");
}
if (!URL.revokeObjectURL) {
  URL.revokeObjectURL = vi.fn();
}

const FAKE_HASH = "a".repeat(64);
const FAKE_BLOB_SHA = "b".repeat(64);

vi.mock("../../../../../lib/api/queries", () => ({
  useSnapshotExport: vi.fn(),
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
      id: "repo-1",
      owner: "demo",
      name: "myrepo",
      layer: "silver",
      subtype: "jsonl",
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
  useSnapshotRows: () => ({
    data: undefined,
    isLoading: false,
    isError: false,
    error: null,
    refetch: vi.fn(),
  }),
}));

function renderExportPage(initialUrl: string) {
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

describe("/repos/$owner/$name/snapshots/$hash/export", () => {
  it("renders format select with default hf_datasets", async () => {
    const { useSnapshotExport } = await import(
      "../../../../../lib/api/queries"
    );
    (useSnapshotExport as ReturnType<typeof vi.fn>).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
      isError: false,
      isSuccess: false,
      data: undefined,
      error: null,
    });

    renderExportPage(
      `/repos/demo/myrepo/snapshots/${FAKE_HASH}/export`,
    );

    // format-select 应渲染
    await waitFor(() => {
      expect(screen.getByTestId("format-select")).toBeInTheDocument();
    });

    // 默认值应为 hf_datasets
    const select = screen.getByTestId("format-select") as HTMLSelectElement;
    expect(select.value).toBe("hf_datasets");

    // 导出按钮应渲染
    expect(screen.getByTestId("export-button")).toBeInTheDocument();

    // result-panel 不应出现（尚未导出）
    expect(screen.queryByTestId("result-panel")).toBeNull();
  });

  it("triggers export and shows result panel", async () => {
    const mockMutate = vi.fn((
      _args: unknown,
      options?: { onSuccess?: (result: unknown) => void },
    ) => {
      // 同步模拟 onSuccess 回调
      options?.onSuccess?.({
        blob: new Blob(["mock-tar-gz-content"], { type: "application/gzip" }),
        rowCount: "2",
        blobSha: FAKE_BLOB_SHA,
      });
    });

    const { useSnapshotExport } = await import(
      "../../../../../lib/api/queries"
    );
    (useSnapshotExport as ReturnType<typeof vi.fn>).mockReturnValue({
      mutate: mockMutate,
      isPending: false,
      isError: false,
      isSuccess: true,
      data: {
        blob: new Blob(["mock-tar-gz-content"], { type: "application/gzip" }),
        rowCount: "2",
        blobSha: FAKE_BLOB_SHA,
      },
      error: null,
    });

    renderExportPage(
      `/repos/demo/myrepo/snapshots/${FAKE_HASH}/export`,
    );

    // 等待导出按钮渲染
    await waitFor(() => {
      expect(screen.getByTestId("export-button")).toBeInTheDocument();
    });

    // 点击导出按钮
    fireEvent.click(screen.getByTestId("export-button"));

    // mutation.mutate 应被调用
    expect(mockMutate).toHaveBeenCalled();

    // result-panel 应出现（因为 isSuccess=true + data 存在）
    await waitFor(() => {
      expect(screen.getByTestId("result-panel")).toBeInTheDocument();
    });

    // row-count 应显示 "2"
    expect(screen.getByTestId("row-count")).toHaveTextContent("2");
  });
});
