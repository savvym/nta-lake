import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  RouterProvider,
  createMemoryHistory,
  createRouter,
} from "@tanstack/react-router";
import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { routeTree } from "../routeTree.gen";

const mockBlobMeta = vi.fn();

vi.mock("../lib/api/queries", () => ({
  useMe: () => ({ data: null, refetch: vi.fn() }),
  useRepo: () => ({ data: null, isLoading: false, isError: false, refetch: vi.fn() }),
  useRepos: () => ({ data: { items: [], total: 0 }, isLoading: false, isError: false, refetch: vi.fn() }),
  useRepoRef: () => ({ data: null, isLoading: false, isError: false }),
  useCommit: () => ({ data: null, isLoading: false, isError: false }),
  useUpdateRepo: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useDeleteRepo: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useEnqueueIngest: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useUploadBlob: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useCreatePipelineRun: () => ({ mutateAsync: vi.fn(), isPending: false }),
  usePipelineRun: () => ({ data: undefined, isLoading: false }),
  useBlobMeta: () => mockBlobMeta(),
}));

function renderBlob(initialUrl: string) {
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

beforeEach(() => {
  mockBlobMeta.mockReset();
  vi.restoreAllMocks();
});

describe("BlobPage rendering", () => {
  it("renders plain text preview for .txt blob within size limit", async () => {
    const sha = "a".repeat(64);
    mockBlobMeta.mockReturnValue({
      data: { sha256: sha, size: 11 },
      isLoading: false,
      isError: false,
    });
    vi.spyOn(globalThis, "fetch").mockImplementation(async () => {
      return new Response("hello world", { status: 200 });
    });

    renderBlob(`/blob/demo/files/${sha}?path=content%2Fx.txt`);

    await waitFor(() => {
      expect(screen.getByText("hello world")).toBeInTheDocument();
    });
  });

  it("renders binary fallback for unknown extension", async () => {
    const sha = "b".repeat(64);
    mockBlobMeta.mockReturnValue({
      data: { sha256: sha, size: 1024 },
      isLoading: false,
      isError: false,
    });
    const fetchSpy = vi.spyOn(globalThis, "fetch");

    renderBlob(`/blob/demo/files/${sha}?path=content%2Fblob.bin`);

    await waitFor(() => {
      expect(screen.getByText(/二进制文件/)).toBeInTheDocument();
    });
    // 二进制 fallback 不发起 fetch 文本
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("blocks preview when size > 5 MB and does not fetch", async () => {
    const sha = "c".repeat(64);
    mockBlobMeta.mockReturnValue({
      data: { sha256: sha, size: 6 * 1024 * 1024 },
      isLoading: false,
      isError: false,
    });
    const fetchSpy = vi.spyOn(globalThis, "fetch");

    renderBlob(`/blob/demo/files/${sha}?path=big.txt`);

    await waitFor(() => {
      expect(screen.getByText(/文件过大/)).toBeInTheDocument();
    });
    expect(fetchSpy).not.toHaveBeenCalled();
  });
});
