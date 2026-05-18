import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState, type ReactNode } from "react";

import { Button } from "../components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { useBlobMeta } from "../lib/api/queries";

export const Route = createFileRoute("/blob/$owner/$name/$hash")({
  component: BlobPage,
  validateSearch: (search: Record<string, unknown>): { path: string } => ({
    path: typeof search.path === "string" ? search.path : "",
  }),
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

function BlobPage() {
  const { owner, name, hash } = Route.useParams();
  const { path } = Route.useSearch();
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
        search={{ tab: "files" }}
        className="text-blue-700 hover:underline"
      >
        {owner}/{name}
      </Link>
      <span className="text-gray-400">/</span>
      <Link
        to="/repos/$owner/$name"
        params={{ owner, name }}
        search={{ tab: "files" }}
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
  size,
  loading,
  error,
}: {
  owner: string;
  name: string;
  hash: string;
  path: string;
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
    />
  );
}

function TextOrMarkdownBody({
  owner,
  name,
  hash,
  kind,
}: {
  owner: string;
  name: string;
  hash: string;
  kind: "text" | "markdown";
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
            <div className="prose prose-sm max-w-none flex flex-col gap-2">
              {renderMinimalMarkdown(text)}
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

// renderMinimalMarkdown：4 类语法，fenced 优先级最高
//   (i) heading: ^#{1-6} <text>
//   (ii) list: 连续 ^- / ^* 行 → <ul><li>
//   (iii) fenced code: ``` ... ``` （未闭合按"剩余全是 code"）
//   (iv) paragraph: 其余非空行段
// fenced 内行不触发 heading/list/paragraph 识别。
// 不支持 inline emphasis / link / image / table / blockquote。
export function renderMinimalMarkdown(src: string): ReactNode[] {
  const lines = src.split("\n");
  const out: ReactNode[] = [];
  let i = 0;
  let key = 0;

  while (i < lines.length) {
    const line = lines[i] ?? "";

    // fenced code （优先级最高）
    if (line.startsWith("```")) {
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !(lines[i] ?? "").startsWith("```")) {
        codeLines.push(lines[i] ?? "");
        i++;
      }
      // 跳过闭合 ```（如果有）
      if (i < lines.length) i++;
      out.push(
        <pre
          key={`code-${key++}`}
          className="bg-gray-50 p-3 rounded text-xs overflow-auto"
        >
          <code className="font-mono whitespace-pre-wrap break-all">
            {codeLines.join("\n")}
          </code>
        </pre>,
      );
      continue;
    }

    // heading
    const headingMatch = /^(#{1,6})\s+(.+)$/.exec(line);
    if (headingMatch) {
      const level = headingMatch[1]!.length;
      const text = headingMatch[2]!;
      const sizeCls =
        level === 1
          ? "text-2xl font-bold"
          : level === 2
            ? "text-xl font-semibold"
            : level === 3
              ? "text-lg font-semibold"
              : "text-base font-semibold";
      out.push(
        <div key={`h-${key++}`} className={sizeCls}>
          {text}
        </div>,
      );
      i++;
      continue;
    }

    // unordered list（连续 ^- / ^* ）
    if (/^[-*]\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^[-*]\s+/.test(lines[i] ?? "")) {
        items.push((lines[i] ?? "").replace(/^[-*]\s+/, ""));
        i++;
      }
      out.push(
        <ul key={`ul-${key++}`} className="list-disc pl-6">
          {items.map((it, idx) => (
            <li key={idx}>{it}</li>
          ))}
        </ul>,
      );
      continue;
    }

    // skip blank
    if (line.trim() === "") {
      i++;
      continue;
    }

    // paragraph
    out.push(
      <p key={`p-${key++}`} className="text-sm">
        {line}
      </p>,
    );
    i++;
  }

  return out;
}
