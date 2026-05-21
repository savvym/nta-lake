/**
 * /recipes/builder RTL 测试 (W4-3 AC-3 + AC-4)
 *
 * 模式：vi.mock("../../lib/api/queries", ...) + memory router（同 W4-2 rows.test.tsx）
 * 不 mock @dnd-kit/*（functional 仍 OK；不模拟拖拽 drag 事件）
 */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  RouterProvider,
  createMemoryHistory,
  createRouter,
} from "@tanstack/react-router";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { routeTree } from "../../routeTree.gen";

// ── 全局 mock：所有 api/queries hook（tests 不依赖 api） ────────────────────
vi.mock("../../lib/api/queries", () => ({
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
  useSnapshot: () => ({ data: null, isLoading: false, isError: false }),
  useSnapshotRows: () => ({
    data: { rows: [], total: 0, offset: 0, limit: 100, blob_sha: "" },
    isLoading: false,
    isError: false,
    error: null,
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

// mock navigator.clipboard（jsdom 默认不支持）
Object.defineProperty(navigator, "clipboard", {
  value: { writeText: vi.fn().mockResolvedValue(undefined) },
  writable: true,
});

function renderBuilderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const history = createMemoryHistory({ initialEntries: ["/recipes/builder"] });
  const router = createRouter({ routeTree, history });
  return render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router as never} />
    </QueryClientProvider>,
  );
}

describe("/recipes/builder", () => {
  it("yaml preview reflects loader and operator", async () => {
    // AC-3：选 loader + 添加 operator → yaml-preview 含对应 name 子串
    renderBuilderPage();

    // 等待页面渲染
    await waitFor(() => {
      expect(screen.getByTestId("yaml-preview")).toBeInTheDocument();
    });

    // 选 loader "html-md"（第一个 LOADER_NAME）然后点"设为 Loader"
    const loaderSelect = screen.getByTestId("loader-select") as HTMLSelectElement;
    fireEvent.change(loaderSelect, { target: { value: "html-md" } });
    // 点"设为 Loader"按钮（按钮文本）
    const setLoaderBtn = screen.getByText("设为 Loader");
    fireEvent.click(setLoaderBtn);

    // 选 operator "chunker" 然后点 Add
    const operatorSelect = screen.getByTestId("operator-select") as HTMLSelectElement;
    fireEvent.change(operatorSelect, { target: { value: "chunker" } });
    const addBtn = screen.getByTestId("operator-add");
    fireEvent.click(addBtn);

    // yaml-preview 应含 "name: html-md" 与 "name: chunker"
    await waitFor(() => {
      const yamlPre = screen.getByTestId("yaml-preview");
      expect(yamlPre.textContent).toContain("name: html-md");
      expect(yamlPre.textContent).toContain("name: chunker");
    });
  });

  it("remove operator", async () => {
    // AC-4：添加 2 个 operators，删掉其中 1 个，yaml-preview 只剩 1 个
    renderBuilderPage();

    await waitFor(() => {
      expect(screen.getByTestId("yaml-preview")).toBeInTheDocument();
    });

    const operatorSelect = screen.getByTestId("operator-select") as HTMLSelectElement;
    const addBtn = screen.getByTestId("operator-add");

    // 添加第 1 个 operator: filter
    fireEvent.change(operatorSelect, { target: { value: "filter" } });
    fireEvent.click(addBtn);

    // 添加第 2 个 operator: dedup
    fireEvent.change(operatorSelect, { target: { value: "dedup" } });
    fireEvent.click(addBtn);

    // 确认两个 operator 卡片都在
    await waitFor(() => {
      expect(screen.getByTestId("operator-card-0")).toBeInTheDocument();
      expect(screen.getByTestId("operator-card-1")).toBeInTheDocument();
    });

    // 点第 0 个 operator 的删除按钮
    const removeBtn0 = screen.getByTestId("operator-remove-0");
    fireEvent.click(removeBtn0);

    // 删除后只剩 1 个 operator（原 operator-card-1 变为 operator-card-0）
    await waitFor(() => {
      expect(screen.getByTestId("operator-card-0")).toBeInTheDocument();
      expect(screen.queryByTestId("operator-card-1")).toBeNull();
    });

    // yaml-preview 应只含 1 个 operator 名
    const yamlPre = screen.getByTestId("yaml-preview");
    const yamlText = yamlPre.textContent ?? "";
    // dedup 应在，filter 应不在
    expect(yamlText).toContain("dedup");
    expect(yamlText).not.toContain("filter");
  });

  it("yaml preview shows error inline when operator config is invalid yaml", async () => {
    // 错误状态：operator config 含非法 yaml → yaml-preview 显示 "(yaml 序列化错误：...)"
    renderBuilderPage();

    await waitFor(() => {
      expect(screen.getByTestId("yaml-preview")).toBeInTheDocument();
    });

    // 先添加一个 operator
    const operatorSelect = screen.getByTestId("operator-select") as HTMLSelectElement;
    fireEvent.change(operatorSelect, { target: { value: "score" } });
    fireEvent.click(screen.getByTestId("operator-add"));

    await waitFor(() => {
      expect(screen.getByTestId("operator-card-0")).toBeInTheDocument();
    });

    // 找到 operator-card-0 内的 textarea（config），写入非法 yaml
    const card = screen.getByTestId("operator-card-0");
    const configTextarea = card.querySelector("textarea");
    expect(configTextarea).not.toBeNull();
    fireEvent.change(configTextarea!, { target: { value: "bad: yaml: ::::" } });

    // yaml-preview 应显示错误前缀
    await waitFor(() => {
      const yamlPre = screen.getByTestId("yaml-preview");
      expect(yamlPre.textContent).toContain("yaml 序列化错误");
    });
  });
});
