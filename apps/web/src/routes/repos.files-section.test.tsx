import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  RouterProvider,
  createMemoryHistory,
  createRouter,
} from "@tanstack/react-router";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { routeTree } from "../routeTree.gen";

const FAKE_COMMIT_HASH = "c".repeat(64);
const SHA_A = "a".repeat(64);
const SHA_B = "b".repeat(64);
const SHA_PAPER = "d".repeat(64);
const SHA_IMAGES_TREE = "e".repeat(64);

// 可被各 test 覆盖的 mock 返回；模块级 mock 必须用引用穿透
const mockSubtreeState = {
  data: null as unknown,
  isLoading: false,
  isError: false,
  error: null as unknown,
};

vi.mock("../lib/api/queries", () => ({
  useMe: () => ({
    data: {
      user_id: "1",
      username: "admin",
      email: null,
      role: "admin",
      is_active: true,
    },
    refetch: vi.fn(),
  }),
  useRepos: () => ({
    data: { items: [], total: 0 },
    isLoading: false,
    isError: false,
    refetch: vi.fn(),
  }),
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
      tree: { hash: "t".repeat(64), entries: [] },
      deduplicated: false,
    },
    isLoading: false,
    isError: false,
    refetch: vi.fn(),
  }),
  useSubtreeByPath: () => mockSubtreeState,
  useDeleteRepo: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useUpdateRepo: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useUploadBlob: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useEnqueueIngest: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useCreatePipelineRun: () => ({ mutateAsync: vi.fn(), isPending: false }),
  usePipelineRun: () => ({ data: undefined, isLoading: false }),
  useBlobMeta: () => ({ data: undefined, isLoading: false, isError: false }),
}));

function renderDetail(initialUrl = "/repos/demo/test") {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const history = createMemoryHistory({ initialEntries: [initialUrl] });
  const router = createRouter({ routeTree, history });
  const view = render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router as never} />
    </QueryClientProvider>,
  );
  return { ...view, router, history };
}

beforeEach(() => {
  mockSubtreeState.data = null;
  mockSubtreeState.isLoading = false;
  mockSubtreeState.isError = false;
  mockSubtreeState.error = null;
});

describe("repo detail Files section", () => {
  it("legacy 扁平 commit：渲染扁平 entry list，无 folder icon，下载链可用", async () => {
    // 模拟 legacy 扁平 commit：所有 entries 都是 type=blob，name 含 /
    mockSubtreeState.data = {
      hash: "t".repeat(64),
      entries: [
        { name: "content/a.md", mode: 33188, entry_type: "blob", target_hash: SHA_A },
        { name: "content/b.md", mode: 33188, entry_type: "blob", target_hash: SHA_B },
      ],
    };
    renderDetail();
    await waitFor(() => {
      expect(screen.getByText("main")).toBeInTheDocument();
      expect(screen.getByText("2 entries")).toBeInTheDocument();
      expect(screen.getByText("content/a.md")).toBeInTheDocument();
      expect(screen.getByText("content/b.md")).toBeInTheDocument();
      const links = screen.getAllByText("下载");
      expect(links.length).toBe(2);
    });
    // legacy 提示
    expect(
      screen.getByText(/legacy 扁平 commit/),
    ).toBeInTheDocument();
  });

  it("嵌套 commit：根级渲染 folder icon + blob 混合", async () => {
    mockSubtreeState.data = {
      hash: "t".repeat(64),
      entries: [
        {
          name: "images",
          mode: 0o040000,
          entry_type: "tree",
          target_hash: SHA_IMAGES_TREE,
        },
        {
          name: "paper.md",
          mode: 33188,
          entry_type: "blob",
          target_hash: SHA_PAPER,
        },
      ],
    };
    renderDetail();
    await waitFor(() => {
      // folder 行
      expect(screen.getByText(/📁\s+images\//)).toBeInTheDocument();
      // blob 行
      expect(screen.getByText("paper.md")).toBeInTheDocument();
      expect(screen.getByText("2 entries")).toBeInTheDocument();
    });
    // 根级无面包屑 "返回上一级"
    expect(screen.queryByText(/返回上一级/)).not.toBeInTheDocument();
  });

  it("点 folder：URL ?path 更新", async () => {
    mockSubtreeState.data = {
      hash: "t".repeat(64),
      entries: [
        {
          name: "images",
          mode: 0o040000,
          entry_type: "tree",
          target_hash: SHA_IMAGES_TREE,
        },
      ],
    };
    const { router } = renderDetail();
    await waitFor(() => {
      expect(screen.getByText(/📁\s+images\//)).toBeInTheDocument();
    });
    const folderRow = screen.getByLabelText(/进入子目录 images/);
    fireEvent.click(folderRow);
    await waitFor(() => {
      const search = router.state.location.search as { path?: string };
      expect(search.path).toBe("images");
    });
  });

  it("面包屑：path 非空时显示路径段 + 返回上一级；点段回退", async () => {
    mockSubtreeState.data = {
      hash: "t".repeat(64),
      entries: [
        { name: "x.txt", mode: 33188, entry_type: "blob", target_hash: SHA_A },
      ],
    };
    const { router } = renderDetail("/repos/demo/test?path=images%2Fsub");
    await waitFor(() => {
      // 面包屑包含 images / sub
      expect(screen.getByText("images")).toBeInTheDocument();
      expect(screen.getByText("sub")).toBeInTheDocument();
      // 返回上一级按钮存在
      expect(screen.getByText(/返回上一级/)).toBeInTheDocument();
    });
    // 点 "images" 段（中间，可点）
    fireEvent.click(screen.getByText("images"));
    await waitFor(() => {
      const search = router.state.location.search as { path?: string };
      expect(search.path).toBe("images");
    });
  });

  it("path 不存在：渲染错误 message + 返根目录按钮", async () => {
    mockSubtreeState.data = null;
    mockSubtreeState.isError = true;
    mockSubtreeState.error = new Error("path 段 nope 在当前层不存在");
    renderDetail("/repos/demo/test?path=nope");
    await waitFor(() => {
      expect(screen.getByText(/加载失败/)).toBeInTheDocument();
      expect(screen.getByText(/返回根目录/)).toBeInTheDocument();
    });
  });
});
