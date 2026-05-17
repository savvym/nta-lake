import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider, createMemoryHistory, createRouter } from "@tanstack/react-router";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { routeTree } from "../routeTree.gen";

vi.mock("../lib/api/queries", () => ({
  useMe: () => ({ data: null, refetch: vi.fn() }),
  useRepos: () => ({ data: { items: [], total: 0 }, isLoading: false, isError: false, refetch: vi.fn() }),
  useRepo: () => ({ data: null, isLoading: false, isError: false, refetch: vi.fn() }),
}));

function renderLogin() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const router = createRouter({
    routeTree,
    history: createMemoryHistory({ initialEntries: ["/login"] }),
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router as never} />
    </QueryClientProvider>,
  );
}

describe("login page", () => {
  it("renders username + password fields and submit button", async () => {
    renderLogin();
    await waitFor(() => {
      expect(screen.getByLabelText("用户名")).toBeInTheDocument();
      expect(screen.getByLabelText("密码")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /^登录/ })).toBeInTheDocument();
    });
  });

  it("shows validation error when submitting empty form", async () => {
    renderLogin();
    await waitFor(() =>
      expect(screen.getByRole("button", { name: /^登录/ })).toBeInTheDocument(),
    );
    fireEvent.click(screen.getByRole("button", { name: /^登录/ }));
    await waitFor(() => {
      const errs = screen.queryAllByText(/必填/);
      expect(errs.length).toBeGreaterThan(0);
    });
  });
});
