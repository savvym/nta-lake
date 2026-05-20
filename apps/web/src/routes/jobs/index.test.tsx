import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  RouterProvider,
  createMemoryHistory,
  createRouter,
} from "@tanstack/react-router";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { routeTree } from "../../routeTree.gen";

// spec web-jobs-list-page-20260520 AC-7：vitest 覆盖 admin / 非 admin / 过滤 / 分页

const meAdmin = {
  user_id: "u1",
  username: "alice",
  email: null,
  role: "admin",
  is_active: true,
};
const meUser = { ...meAdmin, role: "user", username: "bob" };

const mockJobs = [
  {
    id: "11111111-1111-1111-1111-111111111111",
    type: "ingest",
    status: "succeeded",
    payload: { owner: "demo", name: "x" },
    result: null,
    error: null,
    created_at: "2026-05-20T10:00:00Z",
    started_at: "2026-05-20T10:00:01Z",
    completed_at: "2026-05-20T10:00:05Z",
  },
  {
    id: "22222222-2222-2222-2222-222222222222",
    type: "process",
    status: "running",
    payload: { runner: "mineru" },
    result: null,
    error: null,
    created_at: "2026-05-20T09:00:00Z",
    started_at: null,
    completed_at: null,
  },
];

let currentMe = meAdmin;
let lastFilters: { status?: string; type?: string; limit: number; offset: number } = {
  limit: 50,
  offset: 0,
};

vi.mock("../../lib/api/queries", () => ({
  useMe: () => ({ data: currentMe, refetch: vi.fn() }),
  useJobs: (filters: typeof lastFilters, _opts?: { enabled?: boolean }) => {
    lastFilters = filters;
    const filtered = mockJobs.filter(
      (j) =>
        (!filters.status || j.status === filters.status) &&
        (!filters.type || j.type === filters.type),
    );
    return {
      data: {
        items: filtered.slice(filters.offset, filters.offset + filters.limit),
        total: filtered.length,
        limit: filters.limit,
        offset: filters.offset,
      },
      isLoading: false,
      isError: false,
      error: null,
    };
  },
}));

function renderAt(url: string) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const router = createRouter({
    routeTree,
    history: createMemoryHistory({ initialEntries: [url] }),
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router as never} />
    </QueryClientProvider>,
  );
}

describe("/jobs list page", () => {
  beforeEach(() => {
    currentMe = meAdmin;
    lastFilters = { limit: 50, offset: 0 };
  });

  it("admin sees jobs table with status badges", async () => {
    renderAt("/jobs");
    await waitFor(() => {
      // 表格行：通过 job id 前 8 位（jobs.id.slice(0,8)）定位
      expect(screen.getByText("11111111")).toBeInTheDocument();
      expect(screen.getByText("22222222")).toBeInTheDocument();
      // status 文本同时出现在 filter <option> 与 row 内 badge，断言 ≥ 1
      expect(screen.getAllByText("succeeded").length).toBeGreaterThan(0);
      expect(screen.getAllByText("running").length).toBeGreaterThan(0);
    });
  });

  it("non-admin sees 403-equivalent message", async () => {
    currentMe = meUser;
    renderAt("/jobs");
    await waitFor(() => {
      expect(screen.getByText(/仅 admin 可见/)).toBeInTheDocument();
    });
  });

  it("status filter narrows visible rows and updates useJobs args", async () => {
    renderAt("/jobs?status=running");
    await waitFor(() => {
      // mockJobs 里 status=running 只有 22222222 这一条；11111111 (succeeded) 被过滤掉
      expect(screen.getByText("22222222")).toBeInTheDocument();
      expect(screen.queryByText("11111111")).not.toBeInTheDocument();
      expect(lastFilters.status).toBe("running");
    });
  });

  it("pagination next/prev affects useJobs offset", async () => {
    renderAt("/jobs?limit=1&offset=0");
    await waitFor(() => {
      expect(lastFilters.offset).toBe(0);
      expect(lastFilters.limit).toBe(1);
    });
    fireEvent.click(screen.getByText(/下一页/));
    await waitFor(() => {
      expect(lastFilters.offset).toBe(1);
    });
    fireEvent.click(screen.getByText(/上一页/));
    await waitFor(() => {
      expect(lastFilters.offset).toBe(0);
    });
  });

  it("type filter narrows visible rows and updates useJobs args", async () => {
    renderAt("/jobs?type=ingest");
    await waitFor(() => {
      // mockJobs 里 type=ingest 只有 11111111；22222222 (process) 被过滤掉
      expect(screen.getByText("11111111")).toBeInTheDocument();
      expect(screen.queryByText("22222222")).not.toBeInTheDocument();
      expect(lastFilters.type).toBe("ingest");
    });
  });

  it("changing page size resets offset to 0", async () => {
    renderAt("/jobs?limit=25&offset=5");
    await waitFor(() => {
      expect(lastFilters.offset).toBe(5);
    });
    const sel = screen.getByLabelText(/page size/) as HTMLSelectElement;
    fireEvent.change(sel, { target: { value: "100" } });
    await waitFor(() => {
      expect(lastFilters.limit).toBe(100);
      expect(lastFilters.offset).toBe(0);
    });
  });
});
