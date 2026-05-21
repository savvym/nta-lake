/**
 * Recipe v2 builder：yaml 序列化 pure 函数 + loader/operator 名称常量 (W4-3)
 *
 * LOADER_NAMES 来自 packages/core/src/dataplat_core/loaders/__init__.py 注册列表
 * OPERATOR_NAMES（硬编码）已删除，由 useOperatorsQuery 运行时拉取替代（web-recipe-structured-config-20260521）。
 *
 * 注意：pdf_mineru / markdown loader 尚未在 LoaderRegistry 注册（W1-4 只做了
 * MinerU adapter，实际 LoaderRegistry 仅含 html-md / docx / pptx / jsonl）。
 * 如 W3-x 新增 loader，同步更新此处。
 */

import yaml from "js-yaml";

// 与 packages/core/src/dataplat_core/loaders/__init__.py 注册列表对齐
export const LOADER_NAMES = [
  "html-md",
  "docx",
  "pptx",
  "jsonl",
] as const;

export type LoaderName = (typeof LOADER_NAMES)[number];

export type BuilderState = {
  name: string;
  loader: { name: string; configYaml: string; inputYaml: string } | null;
  operators: Array<{
    id: string;
    name: string;
    configYaml: string;
    configObject: Record<string, unknown>;
  }>;
};

/**
 * 把 BuilderState 序列化为 Recipe v2 yaml 字符串。
 *
 * - config / input 字段：传入 yaml string，本函数先 yaml.load 成 obj 再嵌入
 * - 空 yaml / 纯空白 → 视为 {}
 * - yaml.load 失败 → throw Error（caller 在 UI 层 catch 并显示 inline 错误）
 */
export function buildRecipeYaml(state: BuilderState): string {
  const parseYamlField = (s: string): Record<string, unknown> => {
    const trimmed = s.trim();
    if (!trimmed) return {};
    const parsed = yaml.load(trimmed);
    if (parsed === undefined || parsed === null) return {};
    if (typeof parsed !== "object" || Array.isArray(parsed)) {
      throw new Error("yaml 必须解析为 object（mapping）");
    }
    return parsed as Record<string, unknown>;
  };

  const recipe: Record<string, unknown> = {
    name: state.name,
    version: 2,
  };

  if (state.loader) {
    recipe.loader = {
      name: state.loader.name,
      config: parseYamlField(state.loader.configYaml),
      input: parseYamlField(state.loader.inputYaml),
    };
  }

  recipe.operators = state.operators.map((op) => ({
    name: op.name,
    // 优先用 configObject（结构化输入），否则 parse configYaml（fallback 路径）
    config:
      Object.keys(op.configObject).length > 0
        ? op.configObject
        : parseYamlField(op.configYaml),
  }));

  return yaml.dump(recipe, { lineWidth: -1, noRefs: true });
}
