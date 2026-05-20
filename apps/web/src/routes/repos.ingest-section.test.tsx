/**
 * IngestSection onFiles 默认 path 行为单测
 * （spec web-ingest-path-default-20260520 AC-3a）
 *
 * 验证：拖文件 / 选文件后默认 path 是 filename，不再加 content/ 前缀。
 */
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
      name: "ingest-test",
      layer: "bronze",
      subtype: "raw-md",
      visibility: "private",
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

function renderIngest(initialUrl: string) {
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

describe("IngestSection default path", () => {
  it("default path equals filename (no content/ prefix)", async () => {
    renderIngest("/repos/demo/ingest-test?tab=ingest&path=");

    await waitFor(() => {
      expect(screen.getByLabelText(/选文件/)).toBeInTheDocument();
    });

    const fileInput = screen.getByLabelText(/选文件/) as HTMLInputElement;
    const file = new File(["%PDF-1.4 fake"], "a.pdf", {
      type: "application/pdf",
    });
    Object.defineProperty(fileInput, "files", { value: [file] });
    fireEvent.change(fileInput);

    const pathInput = await screen.findByDisplayValue("a.pdf");
    expect(pathInput).toBeInTheDocument();
    expect(screen.queryByDisplayValue("content/a.pdf")).not.toBeInTheDocument();
  });

  it("user edited path is preserved (not overwritten)", async () => {
    renderIngest("/repos/demo/ingest-test?tab=ingest&path=");

    const fileInput = (await screen.findByLabelText(
      /选文件/,
    )) as HTMLInputElement;
    const file = new File(["%PDF-1.4 fake"], "b.pdf", {
      type: "application/pdf",
    });
    Object.defineProperty(fileInput, "files", { value: [file] });
    fireEvent.change(fileInput);

    const pathInput = (await screen.findByDisplayValue(
      "b.pdf",
    )) as HTMLInputElement;
    fireEvent.change(pathInput, { target: { value: "papers/2026/b.pdf" } });
    expect(
      screen.getByDisplayValue("papers/2026/b.pdf"),
    ).toBeInTheDocument();
  });
});
