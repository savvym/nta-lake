import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  useCreatePipelineRun,
  usePipelineRun,
  type PipelineRunResponse,
  type PipelineRunCreatedResponse,
} from "./queries";

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

describe("usePipelineRun", () => {
  it("polls until status reaches succeeded", async () => {
    const responses: PipelineRunResponse[] = [
      {
        run_id: "run-1",
        recipe_name: "demo",
        status: "queued",
        error: null,
        created_by: "admin",
        node_runs: [],
      },
      {
        run_id: "run-1",
        recipe_name: "demo",
        status: "running",
        error: null,
        created_by: "admin",
        node_runs: [],
      },
      {
        run_id: "run-1",
        recipe_name: "demo",
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
        ],
      },
    ];
    let callCount = 0;
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockImplementation(async () => {
      const body = responses[Math.min(callCount, responses.length - 1)];
      callCount += 1;
      return new Response(JSON.stringify(body), { status: 200 });
    });

    const { result } = renderHook(() => usePipelineRun("run-1"), {
      wrapper: makeWrapper(),
    });

    await waitFor(
      () => {
        expect(result.current.data?.status).toBe("succeeded");
      },
      { timeout: 5000 },
    );
    expect(fetchSpy.mock.calls.length).toBeGreaterThanOrEqual(2);
  }, 10000);
});

describe("useCreatePipelineRun", () => {
  it("POSTs yaml with text/yaml content-type and returns run_id", async () => {
    const created: PipelineRunCreatedResponse = {
      run_id: "run-xyz",
      job_id: "job-xyz",
    };
    let captured: {
      url: string;
      contentType: string;
      body: string;
    } | null = null;
    vi.spyOn(globalThis, "fetch").mockImplementation(
      async (input: RequestInfo | URL, init?: RequestInit) => {
        const headers = new Headers(init?.headers);
        captured = {
          url: typeof input === "string" ? input : input.toString(),
          contentType: headers.get("Content-Type") ?? "",
          body: String(init?.body ?? ""),
        };
        return new Response(JSON.stringify(created), { status: 202 });
      },
    );

    const { result } = renderHook(() => useCreatePipelineRun(), {
      wrapper: makeWrapper(),
    });
    const out = await result.current.mutateAsync("name: x\nnodes: []");

    expect(out.run_id).toBe("run-xyz");
    expect(captured).not.toBeNull();
    expect(captured!.url).toBe("/api/pipelines/runs:from-yaml");
    expect(captured!.contentType).toBe("text/yaml");
    expect(captured!.body).toContain("name: x");
  });
});
