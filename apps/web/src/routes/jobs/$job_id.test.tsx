import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  RouterProvider,
  createMemoryHistory,
  createRouter,
} from "@tanstack/react-router";
import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { routeTree } from "../../routeTree.gen";

const FAKE_JOB_ID = "abc-123";

let jobState: "queued" | "running" | "succeeded" | "failed" = "queued";

vi.mock("../../lib/api/queries", () => ({
  useMe: () => ({ data: null, refetch: vi.fn() }),
  useRepos: () => ({ data: { items: [], total: 0 }, isLoading: false, isError: false, refetch: vi.fn() }),
  useRepo: () => ({ data: null, isLoading: false, isError: false, refetch: vi.fn() }),
  useJob: () => {
    if (jobState === "succeeded") {
      return {
        data: {
          id: FAKE_JOB_ID,
          type: "ingest",
          status: "succeeded",
          payload: {
            owner: "demo",
            name: "r1",
            request: { adapter_name: "raw-file-upload", adapter_version: "0.1" },
          },
          result: { commit_hash: "a".repeat(64), deduplicated: false },
          error: null,
          created_at: "2026-05-17T00:00:00Z",
          started_at: "2026-05-17T00:00:01Z",
          completed_at: "2026-05-17T00:00:02Z",
        },
        isLoading: false,
        isError: false,
        refetch: vi.fn(),
      };
    }
    return {
      data: {
        id: FAKE_JOB_ID,
        type: "ingest",
        status: "queued",
        payload: { owner: "demo", name: "r1", request: { adapter_name: "raw-file-upload", adapter_version: "0.1" } },
        result: null,
        error: null,
        created_at: "2026-05-17T00:00:00Z",
        started_at: null,
        completed_at: null,
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    };
  },
  useCommit: () => ({ data: null, isLoading: false, isError: false, refetch: vi.fn() }),
}));

function renderJob() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const router = createRouter({
    routeTree,
    history: createMemoryHistory({ initialEntries: [`/jobs/${FAKE_JOB_ID}`] }),
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router as never} />
    </QueryClientProvider>,
  );
}

describe("/jobs/$job_id", () => {
  it("queued status shows polling hint", async () => {
    jobState = "queued";
    renderJob();
    await waitFor(() => {
      expect(screen.getByText(/queued/)).toBeInTheDocument();
      expect(screen.getByText(/自动每秒刷新/)).toBeInTheDocument();
    });
  });

  it("succeeded status shows commit_hash link", async () => {
    jobState = "succeeded";
    renderJob();
    await waitFor(() => {
      expect(screen.getByText(/succeeded/)).toBeInTheDocument();
      // commit_hash 64 hex 显示
      expect(screen.getByText("a".repeat(64))).toBeInTheDocument();
    });
  });
});
