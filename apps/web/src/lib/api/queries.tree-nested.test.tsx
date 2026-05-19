/**
 * useSubtreeByPath queryFn 单测（stage 6 reviewer v1 MUST FIX-2）。
 *
 * mock fetchJson 在 client.ts 层；renderHook + QueryClient 让 queryFn 真跑。
 * 覆盖：
 *   a. null-guard（root fetch 返 null → throw）
 *   b. segment 不存在 → throw 含 segment 名
 *   c. happy path（多段 nested）
 *   d. segment 不是 tree 是 blob → throw（不下钻进 blob hash）
 */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import * as client from "./client";
import { useSubtreeByPath } from "./queries";

const COMMIT_HASH = "a".repeat(64);
const ROOT_TREE_HASH = "b".repeat(64);
const IMAGES_TREE_HASH = "c".repeat(64);
const FILE_HASH = "d".repeat(64);

const fetchJsonSpy = vi.spyOn(client, "fetchJson");

afterEach(() => {
  fetchJsonSpy.mockReset();
});

beforeEach(() => {
  fetchJsonSpy.mockReset();
});

function wrapper(qc: QueryClient) {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
  };
}

describe("useSubtreeByPath queryFn", () => {
  it("happy path: 多段 nested → 串行 fetch 到 leaf 层", async () => {
    fetchJsonSpy.mockImplementation(async (url: string) => {
      if (url.includes(`/tree/${COMMIT_HASH}`)) {
        return {
          hash: ROOT_TREE_HASH,
          entries: [
            {
              name: "images",
              mode: 0o040000,
              entry_type: "tree",
              target_hash: IMAGES_TREE_HASH,
            },
          ],
        };
      }
      if (url.includes(`/trees/${IMAGES_TREE_HASH}`)) {
        return {
          hash: IMAGES_TREE_HASH,
          entries: [
            { name: "a.jpg", mode: 33188, entry_type: "blob", target_hash: FILE_HASH },
          ],
        };
      }
      return null;
    });

    const qc = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const { result } = renderHook(
      () => useSubtreeByPath("demo", "r", COMMIT_HASH, "images"),
      { wrapper: wrapper(qc) },
    );
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.hash).toBe(IMAGES_TREE_HASH);
    expect(result.current.data?.entries[0].name).toBe("a.jpg");
  });

  it("null-guard: root fetch 返 null → throw", async () => {
    fetchJsonSpy.mockResolvedValue(null);

    const qc = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const { result } = renderHook(
      () => useSubtreeByPath("demo", "r", COMMIT_HASH, ""),
      { wrapper: wrapper(qc) },
    );
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(String(result.current.error)).toMatch(/tree not found/);
  });

  it("segment 不存在 → throw 含 segment 名 + entries 列表", async () => {
    fetchJsonSpy.mockResolvedValue({
      hash: ROOT_TREE_HASH,
      entries: [
        { name: "paper.md", mode: 33188, entry_type: "blob", target_hash: FILE_HASH },
      ],
    });

    const qc = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const { result } = renderHook(
      () => useSubtreeByPath("demo", "r", COMMIT_HASH, "nope"),
      { wrapper: wrapper(qc) },
    );
    await waitFor(() => expect(result.current.isError).toBe(true));
    const msg = String(result.current.error);
    expect(msg).toMatch(/nope/);
    expect(msg).toMatch(/paper\.md/);
  });

  it("segment 是 blob 而非 tree → throw（不下钻进 blob hash）", async () => {
    fetchJsonSpy.mockResolvedValue({
      hash: ROOT_TREE_HASH,
      entries: [
        // images 名相同但 type=blob → 不应当 subtree 用
        { name: "images", mode: 33188, entry_type: "blob", target_hash: FILE_HASH },
      ],
    });

    const qc = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const { result } = renderHook(
      () => useSubtreeByPath("demo", "r", COMMIT_HASH, "images"),
      { wrapper: wrapper(qc) },
    );
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(String(result.current.error)).toMatch(/不是目录|images/);
  });

  it("path 含 // 或前后空段：filter Boolean 后等价 path=有效段", async () => {
    fetchJsonSpy.mockImplementation(async (url: string) => {
      if (url.includes(`/tree/${COMMIT_HASH}`)) {
        return {
          hash: ROOT_TREE_HASH,
          entries: [
            {
              name: "images",
              mode: 0o040000,
              entry_type: "tree",
              target_hash: IMAGES_TREE_HASH,
            },
          ],
        };
      }
      if (url.includes(`/trees/${IMAGES_TREE_HASH}`)) {
        return { hash: IMAGES_TREE_HASH, entries: [] };
      }
      return null;
    });

    const qc = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const { result } = renderHook(
      // 多余的 /  应被 filter 掉
      () => useSubtreeByPath("demo", "r", COMMIT_HASH, "//images//"),
      { wrapper: wrapper(qc) },
    );
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.hash).toBe(IMAGES_TREE_HASH);
  });
});
