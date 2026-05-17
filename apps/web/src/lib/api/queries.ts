import { useQuery } from "@tanstack/react-query";

import { fetchJson } from "./client";

export interface MeResponse {
  user_id: string;
  username: string;
  email: string | null;
  role: string;
  is_active: boolean;
}

export interface RepoListItem {
  id: string;
  owner: string;
  name: string;
  layer: string;
  subtype: string;
  visibility: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface RepoListResponse {
  items: RepoListItem[];
  total: number;
}

export function useMe() {
  return useQuery({
    queryKey: ["me"],
    queryFn: () =>
      fetchJson<MeResponse>("/api/auth/me", undefined, { allowAnon: true }),
    staleTime: 30_000,
  });
}

export function useRepos() {
  return useQuery({
    queryKey: ["repos"],
    queryFn: () => fetchJson<RepoListResponse>("/api/repos?limit=200"),
  });
}

export function useRepo(owner: string, name: string) {
  return useQuery({
    queryKey: ["repo", owner, name],
    queryFn: () =>
      fetchJson<RepoListItem>(
        `/api/repos/${encodeURIComponent(owner)}/${encodeURIComponent(name)}`,
      ),
  });
}
