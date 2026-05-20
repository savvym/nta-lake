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
const mockSubtreeByPath = vi.fn();

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
  useSubtreeByPath: () => mockSubtreeByPath(),
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
  mockSubtreeByPath.mockReset();
  mockSubtreeByPath.mockReturnValue({
    data: null,
    isLoading: false,
    isError: false,
    error: null,
  });
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

  // --- web-blob-md-image-resolver-20260520 新增用例 ---

  it("md image with relative path + commit → 重写 src 为 /api/.../blobs/<sha>", async () => {
    const mdSha = "d".repeat(64);
    const imgSha = "e".repeat(64);
    const commit = "f".repeat(64);
    mockBlobMeta.mockReturnValue({
      data: { sha256: mdSha, size: 30 },
      isLoading: false,
      isError: false,
    });
    mockSubtreeByPath.mockReturnValue({
      data: {
        hash: "1".repeat(64),
        entries: [
          {
            name: "a.jpg",
            mode: 33188,
            entry_type: "blob",
            target_hash: imgSha,
          },
        ],
      },
      isLoading: false,
      isError: false,
      error: null,
    });
    vi.spyOn(globalThis, "fetch").mockImplementation(async () => {
      return new Response("# hi\n\n![alt](images/a.jpg)\n", { status: 200 });
    });

    renderBlob(`/blob/demo/r/${mdSha}?path=paper.md&commit=${commit}`);

    // 切换到 Rendered
    await waitFor(() => {
      expect(screen.getByText("Rendered")).toBeInTheDocument();
    });
    screen.getByText("Rendered").click();

    await waitFor(() => {
      const img = document.querySelector("img") as HTMLImageElement;
      expect(img).not.toBeNull();
      expect(img.src).toContain(`/api/repos/demo/r/blobs/${imgSha}`);
    });
  });

  it("md image with absolute URL → 透传，不重写", async () => {
    const mdSha = "d".repeat(64);
    const commit = "f".repeat(64);
    mockBlobMeta.mockReturnValue({
      data: { sha256: mdSha, size: 30 },
      isLoading: false,
      isError: false,
    });
    vi.spyOn(globalThis, "fetch").mockImplementation(async () => {
      return new Response("![](https://example.com/x.png)\n", { status: 200 });
    });

    renderBlob(`/blob/demo/r/${mdSha}?path=paper.md&commit=${commit}`);

    await waitFor(() => {
      expect(screen.getByText("Rendered")).toBeInTheDocument();
    });
    screen.getByText("Rendered").click();

    await waitFor(() => {
      const img = document.querySelector("img") as HTMLImageElement;
      expect(img).not.toBeNull();
      expect(img.src).toBe("https://example.com/x.png");
    });
  });

  it("md image but no commit param → 透传原 src + 提示", async () => {
    const mdSha = "d".repeat(64);
    mockBlobMeta.mockReturnValue({
      data: { sha256: mdSha, size: 30 },
      isLoading: false,
      isError: false,
    });
    vi.spyOn(globalThis, "fetch").mockImplementation(async () => {
      return new Response("![](images/a.jpg)\n", { status: 200 });
    });

    renderBlob(`/blob/demo/r/${mdSha}?path=paper.md`);

    await waitFor(() => {
      expect(screen.getByText("Rendered")).toBeInTheDocument();
    });
    screen.getByText("Rendered").click();

    await waitFor(() => {
      const img = document.querySelector("img") as HTMLImageElement;
      expect(img).not.toBeNull();
      expect(img.src).toContain("images/a.jpg");
      expect(
        screen.getByText(/no commit ctx, src 不解析/),
      ).toBeInTheDocument();
    });
  });

  it("md image while subtree isLoading → 显占位文字", async () => {
    const mdSha = "d".repeat(64);
    const commit = "f".repeat(64);
    mockBlobMeta.mockReturnValue({
      data: { sha256: mdSha, size: 30 },
      isLoading: false,
      isError: false,
    });
    mockSubtreeByPath.mockReturnValue({
      data: null,
      isLoading: true,
      isError: false,
      error: null,
    });
    vi.spyOn(globalThis, "fetch").mockImplementation(async () => {
      return new Response("![](images/a.jpg)\n", { status: 200 });
    });

    renderBlob(`/blob/demo/r/${mdSha}?path=paper.md&commit=${commit}`);
    await waitFor(() => {
      expect(screen.getByText("Rendered")).toBeInTheDocument();
    });
    screen.getByText("Rendered").click();
    await waitFor(() => {
      expect(screen.getByText(/loading image/)).toBeInTheDocument();
    });
  });

  it("md image but entry not found in tree → 透传 + 提示", async () => {
    const mdSha = "d".repeat(64);
    const commit = "f".repeat(64);
    mockBlobMeta.mockReturnValue({
      data: { sha256: mdSha, size: 30 },
      isLoading: false,
      isError: false,
    });
    mockSubtreeByPath.mockReturnValue({
      data: { hash: "1".repeat(64), entries: [] }, // 空 tree → 找不到
      isLoading: false,
      isError: false,
      error: null,
    });
    vi.spyOn(globalThis, "fetch").mockImplementation(async () => {
      return new Response("![](images/missing.jpg)\n", { status: 200 });
    });

    renderBlob(`/blob/demo/r/${mdSha}?path=paper.md&commit=${commit}`);
    await waitFor(() => {
      expect(screen.getByText("Rendered")).toBeInTheDocument();
    });
    screen.getByText("Rendered").click();
    await waitFor(() => {
      expect(screen.getByText(/找不到.*images\/missing\.jpg/)).toBeInTheDocument();
    });
  });
});

// --- web-blob-md-image-resolver-20260520: helper 单测 ---

describe("path resolution helpers", () => {
  it("resolveImagePath: 绝对 URL → null", async () => {
    const { resolveImagePath } = await import("./blob.$owner.$name.$hash");
    expect(resolveImagePath("paper.md", "https://x.com/a.png")).toBeNull();
    expect(resolveImagePath("paper.md", "data:image/png;base64,xx")).toBeNull();
  });

  it("resolveImagePath: leading / → 仓根绝对路径", async () => {
    const { resolveImagePath } = await import("./blob.$owner.$name.$hash");
    expect(resolveImagePath("paper.md", "/images/a.jpg")).toBe("images/a.jpg");
  });

  it("resolveImagePath: 相对路径 + mdPath dirname 拼接", async () => {
    const { resolveImagePath } = await import("./blob.$owner.$name.$hash");
    expect(resolveImagePath("paper.md", "images/a.jpg")).toBe("images/a.jpg");
    expect(resolveImagePath("papers/2026/a.md", "images/b.jpg")).toBe(
      "papers/2026/images/b.jpg",
    );
    expect(resolveImagePath("papers/2026/a.md", "../shared/c.jpg")).toBe(
      "papers/shared/c.jpg",
    );
  });
});
