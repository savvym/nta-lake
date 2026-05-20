/**
 * 通用 silver/gold row 预览路由 (W4-2 web-row-preview-20260520)
 *
 * 路由：/snapshots/$owner/$name/$hash/rows
 * URL search: offset(default 0), limit(default 100), blobSha?(64-hex)
 */
import { createFileRoute, Link } from "@tanstack/react-router";
import { useRef, useState } from "react";
import { useVirtualizer } from "@tanstack/react-virtual";
import { z } from "zod";

import { Button } from "../../../components/ui/button";
import { useSnapshotRows } from "../../../lib/api/queries";

const searchSchema = z.object({
  offset: z.coerce.number().int().min(0).optional().default(0),
  limit: z.coerce.number().int().min(1).max(500).optional().default(100),
  blobSha: z.string().regex(/^[0-9a-f]{64}$/).optional(),
});

export const Route = createFileRoute("/snapshots/$owner/$name/$hash/rows")({
  component: RowsPage,
  validateSearch: searchSchema,
});

function RowsPage() {
  const { owner, name, hash } = Route.useParams();
  const { offset, limit, blobSha } = Route.useSearch();
  const navigate = Route.useNavigate();

  const { data, isLoading, isError, error, refetch } = useSnapshotRows(
    owner,
    name,
    hash,
    { offset, limit, blobSha },
  );

  const [expanded, setExpanded] = useState<Set<number>>(new Set());

  const parentRef = useRef<HTMLDivElement>(null);

  const rowVirtualizer = useVirtualizer({
    count: data?.rows.length ?? 0,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 48,
    overscan: 10,
  });

  const hashShort = hash.slice(0, 12);

  if (isLoading) {
    return (
      <div className="flex flex-col gap-4 p-4">
        <div className="text-gray-500">加载中…</div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex flex-col gap-4 p-4">
        <div className="flex items-center gap-2 text-sm">
          <Link
            to="/snapshots/$owner/$name/$hash"
            params={{ owner, name, hash }}
            className="text-blue-700 hover:underline"
          >
            ← 返回 metadata
          </Link>
          <span className="text-gray-400">|</span>
          <span className="font-mono text-gray-500">{owner}/{name}@{hashShort}…</span>
        </div>
        <div className="flex flex-col items-start gap-2">
          <div className="text-red-600 text-sm">
            加载失败：{String(error)}
          </div>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            重试
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4 p-4">
      {/* 头部 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Row 预览</h1>
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

      {!data || data.rows.length === 0 ? (
        <div className="text-gray-500 text-sm py-6 text-center border rounded">
          该 snapshot 无 silver/gold 行可预览
        </div>
      ) : (
        <>
          {/* Metadata 行 */}
          <div className="text-xs text-gray-500 font-mono">
            total={data.total} offset={data.offset} limit={data.limit}{" "}
            blob_sha={data.blob_sha.slice(0, 12)}…
          </div>

          {/* 虚拟化容器 */}
          <div
            ref={parentRef}
            data-testid="rows-virtual-container"
            className="h-[600px] overflow-auto border border-gray-200 rounded"
          >
            <div
              style={{
                height: rowVirtualizer.getTotalSize(),
                position: "relative",
              }}
            >
              {rowVirtualizer.getVirtualItems().map((vi) => {
                const row = data.rows[vi.index];
                const isExpanded = expanded.has(vi.index);
                const truncated =
                  row && row.text.length > 200
                    ? row.text.slice(0, 200) + "…"
                    : (row?.text ?? "");

                return (
                  <div
                    key={vi.key}
                    data-testid={`row-${vi.index}`}
                    style={{
                      position: "absolute",
                      top: vi.start,
                      left: 0,
                      width: "100%",
                    }}
                    className="border-b border-gray-100 px-3 py-2"
                  >
                    <div className="flex items-start gap-3">
                      <span className="text-gray-400 text-xs w-10 shrink-0 pt-0.5">
                        {offset + vi.index + 1}
                      </span>
                      <span className="text-sm break-all flex-1">{truncated}</span>
                      <button
                        type="button"
                        onClick={() => {
                          setExpanded((prev) => {
                            const next = new Set(prev);
                            if (next.has(vi.index)) {
                              next.delete(vi.index);
                            } else {
                              next.add(vi.index);
                            }
                            return next;
                          });
                        }}
                        className="text-blue-700 hover:underline text-xs shrink-0"
                      >
                        [详情]
                      </button>
                    </div>
                    {isExpanded && row && (
                      <pre
                        data-testid={`row-detail-${vi.index}`}
                        className="text-xs bg-gray-50 p-2 rounded max-h-64 overflow-auto mt-1"
                      >
                        {JSON.stringify(row, null, 2)}
                      </pre>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* 分页 */}
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={offset === 0}
              onClick={() =>
                navigate({
                  search: (prev) => ({
                    ...prev,
                    offset: Math.max(0, offset - limit),
                  }),
                })
              }
            >
              上一页
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={offset + limit >= data.total}
              onClick={() =>
                navigate({
                  search: (prev) => ({ ...prev, offset: offset + limit }),
                })
              }
            >
              下一页
            </Button>
          </div>
        </>
      )}
    </div>
  );
}
