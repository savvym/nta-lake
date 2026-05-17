import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider, createMemoryHistory, createRouter } from "@tanstack/react-router";
import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { routeTree } from "../routeTree.gen";

vi.mock("../lib/api/queries", () => ({
  useMe: () => ({ data: null, refetch: vi.fn() }),
  useRepos: () => ({
    data: {
      items: [
        {
          id: "1",
          owner: "cn-lit",
          name: "honglou",
          layer: "bronze",
          subtype: "book",
          visibility: "public",
          description: "古典文学",
          created_at: "2026-05-17T10:00:00Z",
          updated_at: "2026-05-17T10:00:00Z",
        },
        {
          id: "2",
          owner: "demo",
          name: "qa-sft",
          layer: "gold",
          subtype: "sft",
          visibility: "internal",
          description: null,
          created_at: "2026-05-17T11:00:00Z",
          updated_at: "2026-05-17T11:00:00Z",
        },
      ],
      total: 2,
    },
    isLoading: false,
    isError: false,
    refetch: vi.fn(),
  }),
  useRepo: () => ({ data: null, isLoading: false, isError: false, refetch: vi.fn() }),
}));

function renderRepos() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const router = createRouter({
    routeTree,
    history: createMemoryHistory({ initialEntries: ["/repos"] }),
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router as never} />
    </QueryClientProvider>,
  );
}

describe("/repos list page", () => {
  it("renders repo cards with owner/name and layer badges", async () => {
    renderRepos();
    await waitFor(() => {
      expect(screen.getByText(/cn-lit\/honglou/)).toBeInTheDocument();
      expect(screen.getByText(/demo\/qa-sft/)).toBeInTheDocument();
      expect(screen.getByText("bronze")).toBeInTheDocument();
      expect(screen.getByText("gold")).toBeInTheDocument();
      expect(screen.getByText(/public/)).toBeInTheDocument();
      expect(screen.getByText(/internal/)).toBeInTheDocument();
    });
  });
});
