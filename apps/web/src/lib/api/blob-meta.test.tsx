import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useBlobMeta, type BlobMetaResponse } from "./queries";

function makeWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("useBlobMeta", () => {
  it("fetches /meta endpoint and returns sha256 + size", async () => {
    const sha = "a".repeat(64);
    const body: BlobMetaResponse = { sha256: sha, size: 1234 };
    let capturedUrl = "";
    vi.spyOn(globalThis, "fetch").mockImplementation(
      async (input: RequestInfo | URL) => {
        capturedUrl = typeof input === "string" ? input : input.toString();
        return new Response(JSON.stringify(body), { status: 200 });
      },
    );

    const { result } = renderHook(() => useBlobMeta("owner1", "repo1", sha), {
      wrapper: makeWrapper(),
    });

    await waitFor(() => {
      expect(result.current.data?.size).toBe(1234);
    });
    expect(result.current.data?.sha256).toBe(sha);
    expect(capturedUrl).toBe(`/api/repos/owner1/repo1/blobs/${sha}/meta`);
  });
});
