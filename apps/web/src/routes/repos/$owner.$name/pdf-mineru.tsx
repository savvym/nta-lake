/**
 * PDF → Silver Row UI v2 (W4-1 web-pdf-mineru-ui-v2-20260520)
 *
 * 路由：/repos/$owner/$name/pdf-mineru
 * URL search: snapshot?, offset(default 0), limit(default 50), blobSha?
 */
import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { z } from "zod";

import { useSnapshotRows } from "../../../lib/api/queries";

const searchSchema = z.object({
  snapshot: z.string().optional(),
  offset: z.coerce.number().int().min(0).catch(0).default(0),
  limit: z.coerce.number().int().min(1).max(500).catch(50).default(50),
  blobSha: z.string().optional(),
});

export const Route = createFileRoute("/repos/$owner/$name/pdf-mineru")({
  component: PdfMineruPage,
  validateSearch: (search: Record<string, unknown>) => searchSchema.parse(search),
});

const SNAPSHOT_HEX_PATTERN = /^[0-9a-f]{64}$/;

function PdfMineruPage() {
  const { owner, name } = Route.useParams();
  const search = Route.useSearch();
  const navigate = Route.useNavigate();

  const snapshotHash = search.snapshot ?? "";
  const isValidHash = SNAPSHOT_HEX_PATTERN.test(snapshotHash);

  const rowsQuery = useSnapshotRows(
    owner,
    name,
    snapshotHash,
    {
      offset: search.offset,
      limit: search.limit,
      blobSha: search.blobSha,
    },
  );

  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);

  const goToPage = (newOffset: number) => {
    navigate({
      search: { ...search, offset: Math.max(0, newOffset) },
    });
    setExpandedIdx(null);
  };

  return (
    <div className="flex flex-col gap-4 p-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">PDF → Silver Row（v2）</h1>
        <a
          href={`/repos/${encodeURIComponent(owner)}/${encodeURIComponent(name)}`}
          className="text-blue-700 hover:underline text-sm"
        >
          ← 返回 {owner}/{name}
        </a>
      </div>

      {/* 区 1：上传区（占位，真跑由后续 e2e 验） */}
      <div className="border rounded p-3 text-gray-500 text-sm">
        上传区（接 useUploadBlob + useEnqueueIngest；当前 W4-1 仅占位，UI 真跑由后续 e2e 验）
      </div>

      {/* 区 2：流水线区（占位） */}
      <div className="border rounded p-3 text-gray-500 text-sm">
        流水线区（接 useCreatePipelineRun + usePipelineRun）
      </div>

      {/* 区 3：行展示区 */}
      <div className="border rounded p-3">
        <h2 className="text-lg font-medium mb-3">Silver Row 展示</h2>

        {!isValidHash ? (
          <div className="text-gray-500 text-sm">
            请提供 ?snapshot=&lt;hash&gt; URL 参数以加载 silver row
          </div>
        ) : rowsQuery.isLoading ? (
          <div className="text-gray-500 text-sm">加载行中…</div>
        ) : rowsQuery.isError ? (
          <div className="flex flex-col gap-2">
            <div className="text-red-600 text-sm">
              加载失败：{String(rowsQuery.error)}
            </div>
            <button
              type="button"
              onClick={() => rowsQuery.refetch()}
              className="text-blue-700 hover:underline text-sm w-fit"
            >
              重试
            </button>
          </div>
        ) : rowsQuery.data ? (
          <>
            <div className="text-xs text-gray-500 mb-2">
              共 {rowsQuery.data.total} 行，当前 {search.offset + 1}–
              {Math.min(search.offset + search.limit, rowsQuery.data.total)}
            </div>
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="py-2 pr-3 text-left font-medium text-gray-600 w-10">#</th>
                  <th className="py-2 pr-3 text-left font-medium text-gray-600">text（截断 200）</th>
                  <th className="py-2 text-left font-medium text-gray-600 w-16">操作</th>
                </tr>
              </thead>
              <tbody>
                {rowsQuery.data.rows.map((row, idx) => {
                  const absoluteIdx = search.offset + idx;
                  const truncated =
                    row.text.length > 200
                      ? row.text.slice(0, 200) + "…"
                      : row.text;
                  return (
                    <tr
                      key={absoluteIdx}
                      className="border-b border-gray-100 hover:bg-gray-50"
                    >
                      <td className="py-2 pr-3 text-gray-400 text-xs">
                        {absoluteIdx + 1}
                      </td>
                      <td className="py-2 pr-3 break-all">{truncated}</td>
                      <td className="py-2">
                        <button
                          type="button"
                          onClick={() =>
                            setExpandedIdx(expandedIdx === idx ? null : idx)
                          }
                          className="text-blue-700 hover:underline text-xs"
                        >
                          [详情]
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>

            {/* 展开详情 */}
            {expandedIdx !== null && rowsQuery.data.rows[expandedIdx] && (
              <pre
                data-testid={`row-detail-${expandedIdx}`}
                className="mt-3 p-3 bg-gray-50 rounded text-xs overflow-auto max-h-64 whitespace-pre-wrap"
              >
                {JSON.stringify(rowsQuery.data.rows[expandedIdx], null, 2)}
              </pre>
            )}

            {/* 翻页 */}
            <div className="flex gap-2 mt-3">
              <button
                type="button"
                disabled={search.offset === 0}
                onClick={() => goToPage(search.offset - search.limit)}
                className="px-3 py-1 text-sm border rounded disabled:opacity-40 hover:bg-gray-50"
              >
                上一页
              </button>
              <button
                type="button"
                disabled={
                  search.offset + search.limit >= rowsQuery.data.total
                }
                onClick={() => goToPage(search.offset + search.limit)}
                className="px-3 py-1 text-sm border rounded disabled:opacity-40 hover:bg-gray-50"
              >
                下一页
              </button>
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
}
