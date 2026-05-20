import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { z } from "zod";

import { Button } from "../components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { useBlobMeta, useSubtreeByPath } from "../lib/api/queries";

export const Route = createFileRoute("/blob/$owner/$name/$hash")({
  component: BlobPage,
  validateSearch: (search: Record<string, unknown>) =>
    z
      .object({
        path: z.string().catch("").default(""),
        commit: z.string().optional(),
      })
      .parse(search),
});

const MAX_PREVIEW_SIZE = 5 * 1024 * 1024;

const TEXT_EXTS = new Set([
  ".md",
  ".txt",
  ".json",
  ".jsonl",
  ".yaml",
  ".yml",
  ".csv",
  ".tsv",
  ".py",
  ".ts",
  ".tsx",
  ".js",
  ".jsx",
  ".sh",
  ".toml",
  ".ini",
  ".conf",
  ".rst",
  ".html",
  ".css",
  ".scss",
  ".xml",
  ".sql",
]);
const IMAGE_EXTS = new Set([
  ".png",
  ".jpg",
  ".jpeg",
  ".gif",
  ".svg",
  ".webp",
  ".ico",
]);

type Kind = "text" | "markdown" | "image" | "binary";

function detectKind(path: string): Kind {
  const idx = path.lastIndexOf(".");
  if (idx < 0) return "binary";
  const ext = path.slice(idx).toLowerCase();
  if (ext === ".md") return "markdown";
  if (TEXT_EXTS.has(ext)) return "text";
  if (IMAGE_EXTS.has(ext)) return "image";
  return "binary";
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function blobDownloadHref(owner: string, name: string, hash: string): string {
  return `/api/repos/${encodeURIComponent(owner)}/${encodeURIComponent(name)}/blobs/${encodeURIComponent(hash)}`;
}

// --- web-blob-md-image-resolver-20260520: 路径解析 helpers ---

export function isAbsoluteUrl(src: string): boolean {
  return (
    src.startsWith("http://") ||
    src.startsWith("https://") ||
    src.startsWith("data:")
  );
}

// 解析 dir 和 rel：处理 "." / ".." / 空段，返合并后的仓内 path
export function resolveRelative(dir: string, rel: string): string {
  const segs = [
    ...(dir ? dir.split("/") : []),
    ...rel.split("/"),
  ];
  const out: string[] = [];
  for (const seg of segs) {
    if (seg === "" || seg === ".") continue;
    if (seg === "..") {
      out.pop();
      continue;
    }
    out.push(seg);
  }
  return out.join("/");
}

// resolveImagePath：返 null 表示"不重写"（绝对 URL）；string 表示要查 tree 的仓内全路径
export function resolveImagePath(
  mdPath: string,
  src: string,
): string | null {
  if (isAbsoluteUrl(src)) return null;
  if (src.startsWith("/")) return resolveRelative("", src.slice(1));
  const dir = mdPath.includes("/")
    ? mdPath.slice(0, mdPath.lastIndexOf("/"))
    : "";
  return resolveRelative(dir, src);
}

function splitDirAndBasename(fullPath: string): [string, string] {
  const idx = fullPath.lastIndexOf("/");
  if (idx < 0) return ["", fullPath];
  return [fullPath.slice(0, idx), fullPath.slice(idx + 1)];
}

const SHA256_RE = /^[0-9a-f]{64}$/;

function CustomImage({
  src,
  alt,
  owner,
  name,
  commit,
  mdPath,
}: {
  src?: string;
  alt?: string;
  owner: string;
  name: string;
  commit?: string;
  mdPath: string;
}) {
  const resolved =
    typeof src === "string" ? resolveImagePath(mdPath, src) : null;
  const shouldQuery =
    !!src &&
    resolved !== null &&
    !!commit &&
    SHA256_RE.test(commit);
  const [dir, base] = shouldQuery
    ? splitDirAndBasename(resolved as string)
    : ["", ""];
  // hooks rules: 无条件调用；shouldQuery=false 时 commit 传 "" 让 enabled=false
  const subtreeQuery = useSubtreeByPath(
    owner,
    name,
    shouldQuery ? (commit as string) : "",
    dir,
  );

  if (!src) return null;
  // 绝对 URL → 透传
  if (resolved === null) {
    return <img src={src} alt={alt ?? ""} />;
  }
  // commit 缺 → 透传 + 小字提示
  if (!commit || !SHA256_RE.test(commit)) {
    return (
      <span>
        <img src={src} alt={alt ?? ""} />
        <span className="text-xs text-gray-400 ml-1">
          (no commit ctx, src 不解析)
        </span>
      </span>
    );
  }
  if (subtreeQuery.isLoading) {
    return (
      <span className="text-xs text-gray-400">(loading image: {src})</span>
    );
  }
  if (subtreeQuery.isError || !subtreeQuery.data) {
    return (
      <span>
        <img src={src} alt={alt ?? ""} />
        <span className="text-xs text-orange-600 ml-1">(目录加载失败)</span>
      </span>
    );
  }
  const entry = subtreeQuery.data.entries.find(
    (e) => e.name === base && e.entry_type === "blob",
  );
  if (!entry) {
    return (
      <span>
        <img src={src} alt={alt ?? ""} />
        <span className="text-xs text-orange-600 ml-1">
          (找不到 {resolved})
        </span>
      </span>
    );
  }
  return (
    <img
      src={`/api/repos/${encodeURIComponent(owner)}/${encodeURIComponent(name)}/blobs/${encodeURIComponent(entry.target_hash)}`}
      alt={alt ?? ""}
    />
  );
}

function BlobPage() {
  const { owner, name, hash } = Route.useParams();
  const { path, commit } = Route.useSearch();
  const displayPath = path || "(unknown path)";
  const metaQuery = useBlobMeta(owner, name, hash);

  return (
    <div className="flex flex-col gap-4">
      <Breadcrumbs owner={owner} name={name} path={displayPath} />

      <BlobInfoCard
        sha={hash}
        size={metaQuery.data?.size ?? null}
        loading={metaQuery.isLoading}
        error={metaQuery.isError}
      />

      <BlobBody
        owner={owner}
        name={name}
        hash={hash}
        path={path}
        commit={commit}
        size={metaQuery.data?.size ?? null}
        loading={metaQuery.isLoading}
        error={metaQuery.isError}
      />
    </div>
  );
}

function Breadcrumbs({
  owner,
  name,
  path,
}: {
  owner: string;
  name: string;
  path: string;
}) {
  return (
    <div className="flex items-center gap-2 text-sm">
      <Link
        to="/repos/$owner/$name"
        params={{ owner, name }}
        search={{ tab: "files", path: "" }}
        className="text-blue-700 hover:underline"
      >
        {owner}/{name}
      </Link>
      <span className="text-gray-400">/</span>
      <Link
        to="/repos/$owner/$name"
        params={{ owner, name }}
        search={{ tab: "files", path: "" }}
        className="text-blue-700 hover:underline"
      >
        Files
      </Link>
      <span className="text-gray-400">/</span>
      <span className="text-gray-900 break-all">{path}</span>
    </div>
  );
}

function BlobInfoCard({
  sha,
  size,
  loading,
  error,
}: {
  sha: string;
  size: number | null;
  loading: boolean;
  error: boolean;
}) {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(sha);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  };
  return (
    <Card>
      <CardHeader>
        <CardTitle>File</CardTitle>
      </CardHeader>
      <CardContent>
        <dl className="grid grid-cols-[6rem_1fr] gap-y-2 gap-x-4 text-sm">
          <dt className="text-gray-500">sha256</dt>
          <dd className="font-mono text-xs break-all flex items-center gap-2">
            <span>{sha}</span>
            <Button variant="outline" size="sm" onClick={copy}>
              {copied ? "已复制" : "复制"}
            </Button>
          </dd>
          <dt className="text-gray-500">size</dt>
          <dd>
            {loading
              ? "加载中…"
              : error
                ? <span className="text-red-600">加载失败</span>
                : size === null
                  ? "—"
                  : formatSize(size)}
          </dd>
          <dt className="text-gray-500">ref</dt>
          <dd className="text-gray-400">—</dd>
        </dl>
      </CardContent>
    </Card>
  );
}

function BlobBody({
  owner,
  name,
  hash,
  path,
  commit,
  size,
  loading,
  error,
}: {
  owner: string;
  name: string;
  hash: string;
  path: string;
  commit?: string;
  size: number | null;
  loading: boolean;
  error: boolean;
}) {
  if (loading) return <div className="text-gray-500">加载中…</div>;
  if (error)
    return <div className="text-red-600">加载文件元信息失败</div>;
  if (size === null) return null;

  if (size > MAX_PREVIEW_SIZE) {
    return (
      <Card>
        <CardContent className="flex flex-col items-start gap-3 py-4">
          <div className="text-gray-700">
            文件过大（{formatSize(size)} &gt; 5 MB），请下载查看
          </div>
          <a
            href={blobDownloadHref(owner, name, hash)}
            target="_blank"
            rel="noopener noreferrer"
          >
            <Button variant="outline" size="sm">
              下载原始文件
            </Button>
          </a>
        </CardContent>
      </Card>
    );
  }

  const kind = detectKind(path);

  if (kind === "image") {
    return (
      <Card>
        <CardContent>
          <img
            src={blobDownloadHref(owner, name, hash)}
            alt={path || hash}
            className="max-w-full"
          />
        </CardContent>
      </Card>
    );
  }

  if (kind === "binary") {
    return (
      <Card>
        <CardContent className="flex flex-col items-start gap-3 py-4">
          <div className="text-gray-700">二进制文件，无法预览。</div>
          <div className="text-xs text-gray-500 font-mono break-all">
            size: {formatSize(size)} · sha256: {hash.slice(0, 12)}…
          </div>
          <a
            href={blobDownloadHref(owner, name, hash)}
            target="_blank"
            rel="noopener noreferrer"
          >
            <Button variant="outline" size="sm">
              下载原始文件
            </Button>
          </a>
        </CardContent>
      </Card>
    );
  }

  // text / markdown
  return (
    <TextOrMarkdownBody
      owner={owner}
      name={name}
      hash={hash}
      kind={kind}
      path={path}
      commit={commit}
    />
  );
}

function TextOrMarkdownBody({
  owner,
  name,
  hash,
  kind,
  path,
  commit,
}: {
  owner: string;
  name: string;
  hash: string;
  kind: "text" | "markdown";
  path: string;
  commit?: string;
}) {
  const [text, setText] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [mode, setMode] = useState<"source" | "rendered">("source");

  useEffect(() => {
    let aborted = false;
    setText(null);
    setErr(null);
    (async () => {
      try {
        const resp = await fetch(blobDownloadHref(owner, name, hash));
        if (!resp.ok) {
          throw new Error(`HTTP ${resp.status}`);
        }
        const body = await resp.text();
        if (!aborted) setText(body);
      } catch (e) {
        if (!aborted)
          setErr(e instanceof Error ? e.message : "fetch failed");
      }
    })();
    return () => {
      aborted = true;
    };
  }, [owner, name, hash]);

  if (err) return <div className="text-red-600">加载失败：{err}</div>;
  if (text === null) return <div className="text-gray-500">加载中…</div>;

  if (kind === "markdown") {
    return (
      <Card>
        <CardContent className="flex flex-col gap-3 py-4">
          <div className="flex gap-2 self-end">
            <Button
              variant={mode === "source" ? "default" : "outline"}
              size="sm"
              onClick={() => setMode("source")}
            >
              Source
            </Button>
            <Button
              variant={mode === "rendered" ? "default" : "outline"}
              size="sm"
              onClick={() => setMode("rendered")}
            >
              Rendered
            </Button>
          </div>
          {mode === "source" ? (
            <pre className="bg-gray-50 p-3 rounded text-xs overflow-auto">
              <code className="font-mono whitespace-pre-wrap break-all">
                {text}
              </code>
            </pre>
          ) : (
            <div className="prose prose-sm max-w-none">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  img: ({ src, alt }) => (
                    <CustomImage
                      src={typeof src === "string" ? src : undefined}
                      alt={typeof alt === "string" ? alt : undefined}
                      owner={owner}
                      name={name}
                      commit={commit}
                      mdPath={path}
                    />
                  ),
                }}
              >
                {text}
              </ReactMarkdown>
            </div>
          )}
        </CardContent>
      </Card>
    );
  }

  // plain text
  return (
    <Card>
      <CardContent className="py-4">
        <pre className="bg-gray-50 p-3 rounded text-xs overflow-auto">
          <code className="font-mono whitespace-pre-wrap break-all">
            {text}
          </code>
        </pre>
      </CardContent>
    </Card>
  );
}
