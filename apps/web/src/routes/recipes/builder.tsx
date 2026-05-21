/**
 * Recipe v2 Chain Builder UI (W4-3 web-operator-chain-builder-20260520)
 *
 * 路由：/recipes/builder
 * 三栏布局：Palette（左）| Chain（中）| YAML Preview（右）
 *
 * LOADER_NAMES / OPERATOR_NAMES 来自 lib/recipe-v2-builder.ts（与 packages/core 注册对齐）
 * 拖拽排序：@dnd-kit/sortable（垂直可拖序列表；tests 不模拟拖拽事件）
 * yaml 序列化：buildRecipeYaml（js-yaml stringify）
 */
import {
  DndContext,
  closestCenter,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  SortableContext,
  arrayMove,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { createFileRoute } from "@tanstack/react-router";
import yaml from "js-yaml";
import { GripVertical, X } from "lucide-react";
import { useState } from "react";
import { z } from "zod";

import { Button } from "../../components/ui/button";
import {
  LOADER_NAMES,
  OPERATOR_NAMES,
  type BuilderState,
  buildRecipeYaml,
} from "../../lib/recipe-v2-builder";

// zod search schema（可选；用于通过 URL 预填）
const searchSchema = z.object({
  loader: z.string().optional(),
  recipe_name: z.string().optional(),
});

export const Route = createFileRoute("/recipes/builder")({
  component: BuilderPage,
  validateSearch: searchSchema,
});

// ────────────────────────────────────────────────────────────────────────────
// SortableOperatorCard 组件
// ────────────────────────────────────────────────────────────────────────────

interface SortableOperatorCardProps {
  op: { id: string; name: string; configYaml: string };
  idx: number;
  onRemove: (id: string) => void;
  onConfigChange: (id: string, yaml: string) => void;
}

function SortableOperatorCard({
  op,
  idx,
  onRemove,
  onConfigChange,
}: SortableOperatorCardProps) {
  const { attributes, listeners, setNodeRef, transform, transition } =
    useSortable({ id: op.id });

  const style: React.CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition: transition ?? undefined,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      data-testid={`operator-card-${idx}`}
      className="border border-gray-200 rounded p-3 bg-white flex flex-col gap-2"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button
            type="button"
            {...attributes}
            {...listeners}
            className="cursor-grab text-gray-400 hover:text-gray-600"
            aria-label="拖拽排序"
          >
            <GripVertical size={16} />
          </button>
          <span className="font-mono text-sm font-medium">{op.name}</span>
        </div>
        <button
          type="button"
          data-testid={`operator-remove-${idx}`}
          onClick={() => onRemove(op.id)}
          className="text-gray-400 hover:text-red-500"
          aria-label={`删除 ${op.name}`}
        >
          <X size={16} />
        </button>
      </div>
      <div className="flex flex-col gap-1">
        <label className="text-xs text-gray-500">config (yaml)</label>
        <textarea
          value={op.configYaml}
          onChange={(e) => onConfigChange(op.id, e.target.value)}
          className="font-mono text-xs border border-gray-200 rounded p-1.5 w-full min-h-[60px] resize-y"
          placeholder="key: value"
          spellCheck={false}
        />
      </div>
    </div>
  );
}

// ────────────────────────────────────────────────────────────────────────────
// BuilderPage 主组件
// ────────────────────────────────────────────────────────────────────────────

function BuilderPage() {
  const { loader: presetLoader, recipe_name: presetName } = Route.useSearch();

  const [state, setState] = useState<BuilderState>({
    name: presetName ?? "my-recipe",
    loader: presetLoader
      ? { name: presetLoader, configYaml: "", inputYaml: "" }
      : null,
    operators: [],
  });

  const [selectedLoader, setSelectedLoader] = useState<string>(
    LOADER_NAMES[0],
  );
  const [selectedOperator, setSelectedOperator] = useState<string>(
    OPERATOR_NAMES[0],
  );
  const [validateResult, setValidateResult] = useState<string | null>(null);
  const [copyDone, setCopyDone] = useState(false);

  // ── 序列化 yaml ───────────────────────────────────────────────────────────

  let yamlText = "";
  let yamlError: string | null = null;
  try {
    yamlText = buildRecipeYaml(state);
  } catch (err) {
    yamlError = `(yaml 序列化错误：${String(err instanceof Error ? err.message : err)})`;
  }

  const displayYaml = yamlError ?? yamlText;

  // ── Palette 操作 ──────────────────────────────────────────────────────────

  function selectLoader() {
    setState((prev) => ({
      ...prev,
      loader: { name: selectedLoader, configYaml: "", inputYaml: "" },
    }));
  }

  function addOperator() {
    const id = `op-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
    setState((prev) => ({
      ...prev,
      operators: [
        ...prev.operators,
        { id, name: selectedOperator, configYaml: "" },
      ],
    }));
  }

  // ── Chain 操作 ────────────────────────────────────────────────────────────

  function removeOperator(opId: string) {
    setState((prev) => ({
      ...prev,
      operators: prev.operators.filter((o) => o.id !== opId),
    }));
  }

  function updateOperatorConfig(opId: string, configYaml: string) {
    setState((prev) => ({
      ...prev,
      operators: prev.operators.map((o) =>
        o.id === opId ? { ...o, configYaml } : o,
      ),
    }));
  }

  function updateLoaderField(
    field: "configYaml" | "inputYaml",
    value: string,
  ) {
    setState((prev) =>
      prev.loader ? { ...prev, loader: { ...prev.loader, [field]: value } } : prev,
    );
  }

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    setState((prev) => {
      const oldIdx = prev.operators.findIndex((o) => o.id === active.id);
      const newIdx = prev.operators.findIndex((o) => o.id === over.id);
      if (oldIdx === -1 || newIdx === -1) return prev;
      return { ...prev, operators: arrayMove(prev.operators, oldIdx, newIdx) };
    });
  }

  // ── 右栏操作 ──────────────────────────────────────────────────────────────

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(displayYaml);
      setCopyDone(true);
      setTimeout(() => setCopyDone(false), 1500);
    } catch {
      /* jsdom / insecure context ignore */
    }
  }

  function handleDownload() {
    if (!state.name.trim()) return;
    const blob = new Blob([displayYaml], { type: "text/yaml" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${state.name.trim()}.yaml`;
    a.click();
    URL.revokeObjectURL(url);
  }

  function handleValidate() {
    try {
      // 仅 yaml 语法校验，不做 schema 校验
      yaml.load(displayYaml);
      setValidateResult("✓ yaml 语法合法");
    } catch (err) {
      setValidateResult(`✗ ${String(err instanceof Error ? err.message : err)}`);
    }
  }

  // ────────────────────────────────────────────────────────────────────────
  // Render
  // ────────────────────────────────────────────────────────────────────────

  return (
    <div className="flex flex-row h-screen overflow-hidden">
      {/* ── 左栏：Palette ──────────────────────────────────────────── */}
      <aside className="w-60 shrink-0 flex flex-col gap-4 p-4 border-r border-gray-200 overflow-y-auto bg-gray-50">
        <h2 className="font-semibold text-sm text-gray-700">Palette</h2>

        {/* Loader section */}
        <div className="flex flex-col gap-2">
          <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
            Loader
          </span>
          <select
            data-testid="loader-select"
            value={selectedLoader}
            onChange={(e) => setSelectedLoader(e.target.value)}
            className="border border-gray-300 rounded text-sm px-2 py-1 bg-white"
          >
            {LOADER_NAMES.map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
          <Button
            size="sm"
            variant="outline"
            onClick={selectLoader}
            className="w-full text-xs"
          >
            设为 Loader
          </Button>
        </div>

        {/* Operator section */}
        <div className="flex flex-col gap-2">
          <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
            Operator
          </span>
          <select
            data-testid="operator-select"
            value={selectedOperator}
            onChange={(e) => setSelectedOperator(e.target.value)}
            className="border border-gray-300 rounded text-sm px-2 py-1 bg-white"
          >
            {OPERATOR_NAMES.map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
          <Button
            size="sm"
            onClick={addOperator}
            data-testid="operator-add"
            className="w-full text-xs"
          >
            + Add Operator
          </Button>
        </div>
      </aside>

      {/* ── 中栏：Chain ────────────────────────────────────────────── */}
      <main className="flex flex-col flex-1 gap-4 p-4 overflow-y-auto min-w-0">
        <h2 className="font-semibold text-sm text-gray-700">Chain</h2>

        {/* Recipe name */}
        <div className="flex flex-col gap-1">
          <label className="text-xs text-gray-500">Recipe 名称</label>
          <input
            type="text"
            required
            minLength={1}
            value={state.name}
            onChange={(e) =>
              setState((prev) => ({ ...prev, name: e.target.value }))
            }
            className="border border-gray-300 rounded px-2 py-1 text-sm font-mono w-full"
            placeholder="my-recipe"
          />
        </div>

        {/* Loader card */}
        <div className="border border-dashed border-gray-300 rounded p-3 flex flex-col gap-2">
          <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
            Loader
          </span>
          {state.loader ? (
            <>
              <div className="flex items-center justify-between">
                <span className="font-mono text-sm font-medium">
                  {state.loader.name}
                </span>
                <button
                  type="button"
                  onClick={() =>
                    setState((prev) => ({ ...prev, loader: null }))
                  }
                  className="text-gray-400 hover:text-red-500"
                  aria-label="移除 Loader"
                >
                  <X size={16} />
                </button>
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-xs text-gray-500">config (yaml)</label>
                <textarea
                  value={state.loader.configYaml}
                  onChange={(e) => updateLoaderField("configYaml", e.target.value)}
                  className="font-mono text-xs border border-gray-200 rounded p-1.5 w-full min-h-[60px] resize-y"
                  placeholder="key: value"
                  spellCheck={false}
                />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-xs text-gray-500">input (yaml)</label>
                <textarea
                  value={state.loader.inputYaml}
                  onChange={(e) => updateLoaderField("inputYaml", e.target.value)}
                  className="font-mono text-xs border border-gray-200 rounded p-1.5 w-full min-h-[60px] resize-y"
                  placeholder="blob_sha: ..."
                  spellCheck={false}
                />
              </div>
            </>
          ) : (
            <span className="text-gray-400 text-sm italic">未选 Loader</span>
          )}
        </div>

        {/* Operator list */}
        <div className="flex flex-col gap-2">
          <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
            Operators ({state.operators.length})
          </span>

          {state.operators.length === 0 ? (
            <div className="text-gray-400 text-sm italic py-2 text-center border border-dashed border-gray-200 rounded">
              暂无 Operator（从左侧 Palette 添加）
            </div>
          ) : (
            <DndContext
              collisionDetection={closestCenter}
              onDragEnd={handleDragEnd}
            >
              <SortableContext
                items={state.operators.map((o) => o.id)}
                strategy={verticalListSortingStrategy}
              >
                <div className="flex flex-col gap-2">
                  {state.operators.map((op, idx) => (
                    <SortableOperatorCard
                      key={op.id}
                      op={op}
                      idx={idx}
                      onRemove={removeOperator}
                      onConfigChange={updateOperatorConfig}
                    />
                  ))}
                </div>
              </SortableContext>
            </DndContext>
          )}
        </div>
      </main>

      {/* ── 右栏：YAML Preview ─────────────────────────────────────── */}
      <aside className="w-90 shrink-0 flex flex-col gap-3 p-4 border-l border-gray-200 overflow-y-auto bg-gray-50">
        <h2 className="font-semibold text-sm text-gray-700">YAML Preview</h2>

        <div className="flex gap-2 flex-wrap">
          <Button
            size="sm"
            variant="outline"
            onClick={handleCopy}
            className="text-xs"
          >
            {copyDone ? "已复制！" : "复制"}
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={handleDownload}
            disabled={!state.name.trim()}
            className="text-xs"
          >
            下载
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={handleValidate}
            className="text-xs"
          >
            校验
          </Button>
        </div>

        {validateResult && (
          <div
            className={`text-xs rounded p-2 ${
              validateResult.startsWith("✓")
                ? "bg-green-50 text-green-700"
                : "bg-red-50 text-red-600"
            }`}
          >
            {validateResult}
          </div>
        )}

        <pre
          data-testid="yaml-preview"
          className="flex-1 font-mono text-xs bg-white border border-gray-200 rounded p-3 overflow-auto whitespace-pre-wrap break-all"
        >
          {displayYaml}
        </pre>
      </aside>
    </div>
  );
}
