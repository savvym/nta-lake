import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  RouterProvider,
  createMemoryHistory,
  createRouter,
} from "@tanstack/react-router";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { routeTree } from "../routeTree.gen";

vi.mock("../lib/api/queries", async () => {
  const actual = await vi.importActual<typeof import("../lib/api/queries")>(
    "../lib/api/queries",
  );
  return {
    ...actual,
    useMe: () => ({
      data: { user_id: "1", username: "admin", email: null, role: "admin", is_active: true },
      refetch: vi.fn(),
    }),
    useRepos: () => ({
      data: { items: [], total: 0 },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    }),
    useRepo: () => ({ data: null, isLoading: false, isError: false, refetch: vi.fn() }),
    useCreateRepo: () => ({ mutateAsync: vi.fn(), isPending: false }),
  };
});

function renderNew() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const router = createRouter({
    routeTree,
    history: createMemoryHistory({ initialEntries: ["/repos/new"] }),
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router as never} />
    </QueryClientProvider>,
  );
}

describe("/repos/new", () => {
  it("renders form fields owner/name/layer/subtype/visibility", async () => {
    renderNew();
    await waitFor(() => {
      expect(screen.getByLabelText("owner")).toBeInTheDocument();
      expect(screen.getByLabelText("name")).toBeInTheDocument();
      expect(screen.getByLabelText("layer")).toBeInTheDocument();
      expect(screen.getByLabelText("subtype")).toBeInTheDocument();
      expect(screen.getByLabelText("visibility")).toBeInTheDocument();
    });
  });

  it("shows owner/name required errors when submitting empty", async () => {
    renderNew();
    await waitFor(() =>
      expect(screen.getByRole("button", { name: /创建/ })).toBeInTheDocument(),
    );
    fireEvent.click(screen.getByRole("button", { name: /创建/ }));
    await waitFor(() => {
      const errs = screen.queryAllByText(/必填/);
      expect(errs.length).toBeGreaterThan(0);
    });
  });
});
