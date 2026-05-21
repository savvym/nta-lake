/**
 * recipe-v2-builder.ts pure 函数单测 (W4-3 AC-2)
 *
 * DEV-1 修订：AC-2 示例中的 "pdf_mineru" loader 与 "normalize_unicode" operator
 * 在 packages/core LoaderRegistry / OperatorRegistry 均未注册；
 * 实际注册名为 "html-md"（loader）与 "chunker"（operator）。
 * 本测试改用实际注册名；design.md AC-2 描述中的举例名称仅作 illustrative。
 */
import yaml from "js-yaml";
import { describe, expect, it } from "vitest";

import { buildRecipeYaml } from "./recipe-v2-builder";

describe("buildRecipeYaml", () => {
  it("serializes minimal recipe", () => {
    // AC-2：传入 loader + 1 个 operator，返回 yaml 字符串含必要字段
    // DEV-1：用实际注册名 "html-md" + "chunker" 替代 "pdf_mineru" + "normalize_unicode"
    const state = {
      name: "r",
      loader: {
        name: "html-md",
        configYaml: "",
        inputYaml: "blob_sha: abc",
      },
      operators: [
        { id: "1", name: "chunker", configYaml: "", configObject: {} },
      ],
    };

    const result = buildRecipeYaml(state);
    const parsed = yaml.load(result) as Record<string, unknown>;

    expect(parsed["name"]).toBe("r");
    expect(parsed["version"]).toBe(2);

    const loader = parsed["loader"] as Record<string, unknown>;
    expect(loader["name"]).toBe("html-md");

    const input = loader["input"] as Record<string, unknown>;
    expect(input["blob_sha"]).toBe("abc");

    const operators = parsed["operators"] as Array<Record<string, unknown>>;
    expect(operators[0]!["name"]).toBe("chunker");
  });

  it("treats empty config yaml as empty object", () => {
    const state = {
      name: "test-recipe",
      loader: {
        name: "docx",
        configYaml: "",
        inputYaml: "   ",
      },
      operators: [
        { id: "op1", name: "filter", configYaml: "", configObject: {} },
        { id: "op2", name: "dedup", configYaml: "   ", configObject: {} },
      ],
    };

    const result = buildRecipeYaml(state);
    const parsed = yaml.load(result) as Record<string, unknown>;

    const loader = parsed["loader"] as Record<string, unknown>;
    expect(loader["config"]).toEqual({});
    expect(loader["input"]).toEqual({});

    const operators = parsed["operators"] as Array<Record<string, unknown>>;
    expect(operators[0]!["config"]).toEqual({});
    expect(operators[1]!["config"]).toEqual({});
  });

  it("throws on invalid yaml in operator config", () => {
    const state = {
      name: "bad-recipe",
      loader: null,
      operators: [
        { id: "op1", name: "score", configYaml: "invalid: yaml: ::::", configObject: {} },
      ],
    };

    expect(() => buildRecipeYaml(state)).toThrow();
  });
});
