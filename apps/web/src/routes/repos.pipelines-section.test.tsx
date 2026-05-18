import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mockMutateAsync = vi.fn();
const mockRunData = vi.fn();

vi.mock("../lib/api/queries", () => ({
  useCreatePipelineRun: () => ({
    mutateAsync: mockMutateAsync,
    isPending: false,
  }),
  usePipelineRun: () => ({
    data: mockRunData(),
    isLoading: false,
  }),
}));

// 静默 router 依赖（PipelinesSection 不用 router，但 $owner.$name.tsx 顶部 import 了
// createFileRoute；vi.mock 整个 queries 模块即可，组件本身不调 router hook）
function renderWithProviders(node: ReactNode) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(<QueryClientProvider client={qc}>{node}</QueryClientProvider>);
}

beforeEach(() => {
  mockMutateAsync.mockReset();
  mockRunData.mockReset();
  mockRunData.mockReturnValue(undefined);
});

describe("PipelinesSection", () => {
  it("disables run button when yaml is empty and enables when filled; click triggers mutation", async () => {
    mockMutateAsync.mockResolvedValue({ run_id: "r1", job_id: "j1" });
    const { PipelinesSection } = await import("./repos/$owner.$name");
    renderWithProviders(<PipelinesSection owner="demo" name="raw-md" />);

    const button = screen.getByRole("button", { name: /运行 Pipeline/ });
    expect(button).toBeDisabled();

    const textarea = screen.getByLabelText(/Recipe YAML/);
    fireEvent.change(textarea, {
      target: { value: "name: x\nnodes: []" },
    });
    expect(button).not.toBeDisabled();

    fireEvent.click(button);
    expect(mockMutateAsync).toHaveBeenCalledWith("name: x\nnodes: []");
  });

  it("renders node table with 2 rows when run.status=succeeded", async () => {
    mockMutateAsync.mockResolvedValue({ run_id: "r2", job_id: "j2" });
    mockRunData.mockReturnValue({
      run_id: "r2",
      recipe_name: "demo-bronze-to-gold",
      status: "succeeded",
      error: null,
      created_by: "admin",
      node_runs: [
        {
          node_id: "normalize",
          processor_name: "markdown-normalize",
          processor_version: "0.1",
          config: {},
          status: "succeeded",
          cache_hit: false,
          output_commit_hash: "a".repeat(64),
          input_commits: ["b".repeat(64)],
          cache_key: "c".repeat(64),
          error: null,
        },
        {
          node_id: "qa_gen",
          processor_name: "llm-qa-gen",
          processor_version: "0.1",
          config: {},
          status: "succeeded",
          cache_hit: true,
          output_commit_hash: "d".repeat(64),
          input_commits: ["a".repeat(64)],
          cache_key: "e".repeat(64),
          error: null,
        },
      ],
    });

    const { PipelinesSection } = await import("./repos/$owner.$name");
    renderWithProviders(<PipelinesSection owner="demo" name="raw-md" />);

    // 填入 yaml + 点 run 进入 Run 状态面板
    const textarea = screen.getByLabelText(/Recipe YAML/);
    fireEvent.change(textarea, { target: { value: "name: x" } });
    fireEvent.click(screen.getByRole("button", { name: /运行 Pipeline/ }));

    // mutateAsync 是 async，等 Promise 落地后 activeRunId set
    await screen.findByText("normalize");
    expect(screen.getByText("qa_gen")).toBeInTheDocument();
    // "succeeded" 出现 3 处（run badge + 2 个 node 状态列）
    expect(screen.getAllByText("succeeded").length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText(/markdown-normalize@0.1/)).toBeInTheDocument();
    expect(screen.getByText(/llm-qa-gen@0.1/)).toBeInTheDocument();
  });
});
