/**
 * dataplat HTTP API client wrapper（spec web-mvp-pages AC-5）。
 *
 * 401 处理两路径：
 * - 默认：尝试 POST /api/auth/refresh → 成功重试一次原请求 / 失败 throw UnauthorizedError
 * - opts.allowAnon=true：直接返 null，不走 refresh（useMe 用之，匿名 nav 不弹 login）
 */

export class UnauthorizedError extends Error {
  constructor(message = "Unauthorized") {
    super(message);
    this.name = "UnauthorizedError";
  }
}

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly body?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export interface FetchOptions {
  /** 401 时返 null 而非走 refresh + throw。匿名查询用（useMe）。 */
  allowAnon?: boolean;
}

async function _rawFetch(url: string, init?: RequestInit): Promise<Response> {
  return fetch(url, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
}

async function _tryRefresh(): Promise<boolean> {
  try {
    const resp = await _rawFetch("/api/auth/refresh", { method: "POST" });
    return resp.ok;
  } catch {
    return false;
  }
}

export async function fetchJson<T>(
  url: string,
  init?: RequestInit,
  opts?: FetchOptions,
): Promise<T | null> {
  const resp = await _rawFetch(url, init);

  if (resp.status === 401) {
    if (opts?.allowAnon) {
      return null;
    }
    const refreshed = await _tryRefresh();
    if (refreshed) {
      const retry = await _rawFetch(url, init);
      if (retry.status === 401) {
        throw new UnauthorizedError();
      }
      if (!retry.ok) {
        throw new ApiError(retry.status, await retry.text());
      }
      return (await retry.json()) as T;
    }
    throw new UnauthorizedError();
  }

  if (resp.status === 404) {
    return null;
  }

  if (!resp.ok) {
    const body = await resp.text();
    throw new ApiError(resp.status, body, body);
  }

  if (resp.status === 204) {
    return null;
  }
  return (await resp.json()) as T;
}
