import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  RouterProvider,
  createMemoryHistory,
  createRouter,
} from "@tanstack/react-router";
import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { routeTree } from "../routeTree.gen";

// spec W4-7 AC-4：vitest 覆盖 admin 3 行 / 非 admin 403 message

const meAdmin = {
  user_id: "u1",
  username: "alice",
  email: null,
  role: "admin",
  is_active: true,
};
const meUser = { ...meAdmin, role: "user", username: "bob" };

const mockOperators = [
  {
    operator_name: "chunker",
    runs: 5,
    rows_in: 10,
    rows_out: 20,
    errors: 0,
    duration_ms_total: 50.0,
    duration_ms_avg: 10.0,
  },
  {
    operator_name: "filter",
    runs: 3,
    rows_in: 6,
    rows_out: 5,
    errors: 1,
    duration_ms_total: 30.0,
    duration_ms_avg: 10.0,
  },
  {
    operator_name: "snapshot_tag",
    runs: 2,
    rows_in: 5,
    rows_out: 5,
    errors: 0,
    duration_ms_total: 10.0,
    duration_ms_avg: 5.0,
  },
];

let currentMe = meAdmin;

vi.mock("../lib/api/queries", () => ({
  useMe: () => ({ data: currentMe, refetch: vi.fn() }),
  useMetrics: (_opts?: { enabled?: boolean }) => ({
    data: {
      operators: mockOperators,
      collected_at: "2026-05-21T10:00:00+00:00",
    },
    isLoading: false,
    isError: false,
    error: null,
  }),
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

describe("/observability page", () => {
  beforeEach(() => {
    currentMe = meAdmin;
  });

  it("admin sees operators table with 3 rows", async () => {
    renderAt("/observability");
    await waitFor(() => {
      // 3 operator 行
      expect(screen.getByText("chunker")).toBeInTheDocument();
      expect(screen.getByText("filter")).toBeInTheDocument();
      expect(screen.getByText("snapshot_tag")).toBeInTheDocument();
      // 表头存在
      expect(screen.getByText("operator")).toBeInTheDocument();
      expect(screen.getByText("runs")).toBeInTheDocument();
      expect(screen.getByText("rows_in")).toBeInTheDocument();
      expect(screen.getByText("rows_out")).toBeInTheDocument();
      expect(screen.getByText("errors")).toBeInTheDocument();
      expect(screen.getByText("avg duration (ms)")).toBeInTheDocument();
    });
  });

  it("non-admin sees 需要 admin 权限 message", async () => {
    currentMe = meUser;
    renderAt("/observability");
    await waitFor(() => {
      expect(screen.getByText("需要 admin 权限")).toBeInTheDocument();
    });
  });
});
