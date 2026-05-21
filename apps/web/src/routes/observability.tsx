import { createFileRoute } from "@tanstack/react-router";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { useMe, useMetrics } from "../lib/api/queries";

export const Route = createFileRoute("/observability")({
  component: ObservabilityPage,
});

function ObservabilityPage() {
  const { data: me } = useMe();
  const isAdmin = me?.role === "admin";
  const metricsQuery = useMetrics({ enabled: isAdmin });

  if (!me) {
    return (
      <Card>
        <CardContent className="py-6">
          <div className="text-gray-500">未登录。</div>
        </CardContent>
      </Card>
    );
  }

  if (!isAdmin) {
    return (
      <Card>
        <CardContent className="py-6">
          <div className="text-red-600">需要 admin 权限</div>
        </CardContent>
      </Card>
    );
  }

  const operators = metricsQuery.data?.operators ?? [];
  const collectedAt = metricsQuery.data?.collected_at ?? null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-3">
          <span>Observability</span>
          <span className="text-xs text-gray-400 font-normal">每 5s 自动刷新</span>
        </CardTitle>
        {collectedAt && (
          <p className="text-xs text-gray-500 mt-1">
            采集时间：{new Date(collectedAt).toLocaleString()} （进程启动以来）
          </p>
        )}
      </CardHeader>
      <CardContent>
        {metricsQuery.isLoading ? (
          <div className="text-gray-500">加载中…</div>
        ) : metricsQuery.isError ? (
          <div className="text-red-600">
            加载失败：{String(metricsQuery.error)}
          </div>
        ) : operators.length === 0 ? (
          <div className="text-gray-500">暂无 operator 运行记录。</div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left border-b border-gray-200">
                <th className="py-2 pr-4 font-medium text-gray-600">operator</th>
                <th className="py-2 pr-4 font-medium text-gray-600">runs</th>
                <th className="py-2 pr-4 font-medium text-gray-600">rows_in</th>
                <th className="py-2 pr-4 font-medium text-gray-600">rows_out</th>
                <th className="py-2 pr-4 font-medium text-gray-600">errors</th>
                <th className="py-2 pr-4 font-medium text-gray-600">avg duration (ms)</th>
              </tr>
            </thead>
            <tbody>
              {operators.map((op) => (
                <tr
                  key={op.operator_name}
                  className="border-b border-gray-100 hover:bg-gray-50"
                >
                  <td className="py-2 pr-4 font-mono text-xs">{op.operator_name}</td>
                  <td className="py-2 pr-4 text-gray-700">{op.runs}</td>
                  <td className="py-2 pr-4 text-gray-700">{op.rows_in}</td>
                  <td className="py-2 pr-4 text-gray-700">{op.rows_out}</td>
                  <td className="py-2 pr-4">
                    {op.errors > 0 ? (
                      <span className="text-red-600 font-medium">{op.errors}</span>
                    ) : (
                      <span className="text-gray-500">{op.errors}</span>
                    )}
                  </td>
                  <td className="py-2 pr-4 text-gray-700">
                    {op.duration_ms_avg.toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </CardContent>
    </Card>
  );
}
