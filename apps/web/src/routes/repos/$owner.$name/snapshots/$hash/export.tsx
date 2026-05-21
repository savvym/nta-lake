/**
 * Snapshot export UI（W4-4 web-snapshot-export-ui-20260520）
 *
 * 路由：/repos/$owner/$name/snapshots/$hash/export
 * URL search: format (default "hf_datasets"), blobSha?
 *
 * folder form 多级嵌套：routes/repos/$owner.$name/snapshots/$hash/export.tsx
 * 父路由 $owner.$name.tsx 已加 <Outlet />（W4-2）
 */
import { Link, createFileRoute } from "@tanstack/react-router";
import { useRef } from "react";
import { z } from "zod";

import { useSnapshotExport } from "../../../../../lib/api/queries";

type ExportFormat = "hf_datasets" | "jsonl" | "parquet";

const searchSchema = z.object({
  format: z
    .enum(["hf_datasets", "jsonl", "parquet"] as const)
    .catch("hf_datasets")
    .default("hf_datasets"),
  blobSha: z
    .string()
    .regex(/^[0-9a-f]{64}$/)
    .optional(),
});

export const Route = createFileRoute(
  "/repos/$owner/$name/snapshots/$hash/export",
)({
  component: ExportPage,
  validateSearch: searchSchema,
});

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function ExportPage() {
  const { owner, name, hash } = Route.useParams();
  const { format: searchFormat, blobSha: searchBlobSha } = Route.useSearch();
  const navigate = Route.useNavigate();

  const exportMutation = useSnapshotExport();
  const blobShaInputRef = useRef<HTMLInputElement>(null);

  const hashShort = hash.slice(0, 12);

  const handleFormatChange = (newFormat: ExportFormat) => {
    navigate({ search: (prev) => ({ ...prev, format: newFormat }) });
  };

  const handleExport = () => {
    const blobShaValue = blobShaInputRef.current?.value?.trim() || undefined;
    exportMutation.mutate(
      {
        owner,
        name,
        hash,
        format: searchFormat as ExportFormat,
        blobSha: blobShaValue,
        split: "train",
      },
      {
        onSuccess: (result) => {
          const filename = `snapshot-${hashShort}.tar.gz`;
          triggerDownload(result.blob, filename);
        },
      },
    );
  };

  return (
    <div className="flex flex-col gap-4 p-4">
      {/* 头部 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">导出 Snapshot</h1>
          <div className="font-mono text-sm text-gray-500">
            {owner}/{name} @ {hashShort}…
          </div>
        </div>
        <Link
          to="/snapshots/$owner/$name/$hash"
          params={{ owner, name, hash }}
          className="text-blue-700 hover:underline text-sm"
        >
          ← 返回 metadata
        </Link>
      </div>

      {/* 导出表单 */}
      <div className="flex flex-col gap-4 border rounded p-4 max-w-lg">
        {/* 格式选择 */}
        <div className="flex flex-col gap-1.5">
          <label htmlFor="format-select" className="text-sm font-medium text-gray-700">
            导出格式
          </label>
          <select
            id="format-select"
            data-testid="format-select"
            className="h-9 rounded-md border border-gray-300 bg-white px-2 text-sm"
            value={searchFormat}
            onChange={(e) => handleFormatChange(e.target.value as ExportFormat)}
          >
            <option value="hf_datasets">hf_datasets（HuggingFace datasets 目录 + Arrow）</option>
            <option value="jsonl" disabled>
              jsonl（follow-up）
            </option>
            <option value="parquet" disabled>
              parquet（follow-up）
            </option>
          </select>
          {searchFormat !== "hf_datasets" && (
            <p className="text-xs text-amber-600">
              该格式尚未实现（follow-up）；请选择 hf_datasets。
            </p>
          )}
        </div>

        {/* blob_sha 输入（可选） */}
        <div className="flex flex-col gap-1.5">
          <label htmlFor="blob-sha-input" className="text-sm font-medium text-gray-700">
            blob_sha（可选，64 位 hex；留空则自动解析 .jsonl entry）
          </label>
          <input
            id="blob-sha-input"
            ref={blobShaInputRef}
            type="text"
            defaultValue={searchBlobSha ?? ""}
            placeholder={"a".repeat(64)}
            pattern="^[0-9a-f]{64}$"
            className="h-9 rounded-md border border-gray-300 px-2 text-sm font-mono"
          />
        </div>

        {/* 导出按钮 */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            data-testid="export-button"
            onClick={handleExport}
            disabled={exportMutation.isPending || searchFormat !== "hf_datasets"}
            className="px-4 py-2 bg-blue-600 text-white rounded text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {exportMutation.isPending ? "导出中…" : "导出"}
          </button>
          {exportMutation.isPending && (
            <span className="text-sm text-gray-500 animate-pulse">导出中，请稍候…</span>
          )}
        </div>

        {/* 错误显示 */}
        {exportMutation.isError && (
          <div className="text-sm text-red-600 border border-red-200 rounded p-2">
            导出失败：{exportMutation.error instanceof Error
              ? exportMutation.error.message
              : String(exportMutation.error)}
          </div>
        )}

        {/* 成功结果面板 */}
        {exportMutation.isSuccess && exportMutation.data && (
          <div
            data-testid="result-panel"
            className="flex flex-col gap-2 border border-green-200 rounded p-3 bg-green-50"
          >
            <div className="text-sm font-medium text-green-800">导出完成，浏览器下载已触发</div>
            <dl className="grid grid-cols-[8rem_1fr] gap-y-1 text-sm">
              <dt className="text-gray-500">行数</dt>
              <dd
                data-testid="row-count"
                className="font-mono text-gray-900"
              >
                {exportMutation.data.rowCount ?? "—"}
              </dd>
              <dt className="text-gray-500">blob_sha</dt>
              <dd className="font-mono text-xs text-gray-700 break-all">
                {exportMutation.data.blobSha
                  ? `${exportMutation.data.blobSha.slice(0, 12)}…`
                  : "—"}
              </dd>
              <dt className="text-gray-500">文件名</dt>
              <dd className="font-mono text-xs text-gray-700">
                snapshot-{hashShort}.tar.gz
              </dd>
            </dl>
          </div>
        )}
      </div>
    </div>
  );
}
