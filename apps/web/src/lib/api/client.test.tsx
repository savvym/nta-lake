/**
 * fetchJson 双路径单元测试（spec web-mvp-pages AC-5 + AC-11 c1/c2）：
 * - 默认 401 → /api/auth/refresh 成功 → 重试原请求成功
 * - allowAnon: true 401 → 直接返 null（不调 refresh）
 */
import { afterEach, describe, expect, it, vi } from "vitest";

import { fetchJson } from "./client";

const originalFetch = globalThis.fetch;

afterEach(() => {
  globalThis.fetch = originalFetch;
  vi.clearAllMocks();
});

describe("fetchJson 401 处理", () => {
  it("默认 401 → refresh 成功 → 重试原请求成功", async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    globalThis.fetch = vi.fn(async (input: RequestInfo, init?: RequestInit) => {
      const url = typeof input === "string" ? input : input.toString();
      calls.push({ url, init });
      if (url === "/api/repos" && calls.filter((c) => c.url === "/api/repos").length === 1) {
        return new Response(null, { status: 401 });
      }
      if (url === "/api/auth/refresh") {
        return new Response(null, { status: 200 });
      }
      if (url === "/api/repos") {
        return new Response(JSON.stringify({ items: [], total: 0 }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      return new Response(null, { status: 500 });
    }) as never;

    const result = await fetchJson<{ total: number }>("/api/repos");
    expect(result).toEqual({ items: [], total: 0 });
    const urls = calls.map((c) => c.url);
    expect(urls).toContain("/api/auth/refresh");
    expect(urls.filter((u) => u === "/api/repos").length).toBe(2);
  });

  it("allowAnon=true 401 → 返 null，不调 refresh", async () => {
    const calls: string[] = [];
    globalThis.fetch = vi.fn(async (input: RequestInfo) => {
      const url = typeof input === "string" ? input : input.toString();
      calls.push(url);
      return new Response(null, { status: 401 });
    }) as never;

    const result = await fetchJson("/api/auth/me", undefined, { allowAnon: true });
    expect(result).toBeNull();
    expect(calls).toEqual(["/api/auth/me"]);
    expect(calls.some((u) => u.includes("/auth/refresh"))).toBe(false);
  });
});
