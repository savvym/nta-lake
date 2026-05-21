/**
 * OperatorConfigForm — 根据 operator config_schema 渲染结构化表单（web-recipe-structured-config-20260521）
 *
 * 支持的 JSON Schema 类型：
 *   string + enum → <select>
 *   string        → <input type="text">
 *   integer       → <input type="number" step="1">
 *   number        → <input type="number" step="any">
 *   boolean       → <input type="checkbox">
 *   其他 / object / array → fallback 到整个表单用 YAML textarea
 *
 * 若 schema 为 undefined / 无 properties / type 非 object → fallback textarea
 * 若 schema 有效但 properties 为空 → 显示"（无可配置参数）"
 */

interface PropDef {
  type?: string;
  enum?: unknown[];
  [key: string]: unknown;
}

interface SchemaLike {
  type?: string;
  properties?: Record<string, PropDef>;
  required?: string[];
  [key: string]: unknown;
}

export interface OperatorConfigFormProps {
  /** operator 的 config_schema（JSON-schema like dict）*/
  schema: Record<string, unknown> | undefined;
  /** 结构化表单当前值 */
  value: Record<string, unknown>;
  onChange: (next: Record<string, unknown>) => void;
  /** fallback YAML textarea 的文本 */
  fallbackYaml: string;
  onFallbackYamlChange: (yaml: string) => void;
  testIdPrefix?: string;
}

function _shouldFallback(schema: Record<string, unknown> | undefined): boolean {
  if (!schema) return true;
  if (schema.type !== "object") return true;
  // no properties key at all → also treated as fallback (schema not recognized)
  if (!("properties" in schema)) return true;
  return false;
}

function _hasUnsupportedProp(properties: Record<string, PropDef>): boolean {
  for (const prop of Object.values(properties)) {
    const t = prop.type;
    if (
      t !== "string" &&
      t !== "integer" &&
      t !== "number" &&
      t !== "boolean"
    ) {
      // unsupported type → entire form falls back
      return true;
    }
  }
  return false;
}

export function OperatorConfigForm({
  schema,
  value,
  onChange,
  fallbackYaml,
  onFallbackYamlChange,
  testIdPrefix = "op-cfg",
}: OperatorConfigFormProps) {
  const s = schema as SchemaLike | undefined;

  // ── Determine render mode ─────────────────────────────────────────────────
  if (_shouldFallback(s)) {
    return <FallbackYamlTextarea value={fallbackYaml} onChange={onFallbackYamlChange} />;
  }

  const properties = (s!.properties ?? {}) as Record<string, PropDef>;
  const required: string[] = (s!.required ?? []) as string[];

  // unsupported prop type → fallback entire form
  if (_hasUnsupportedProp(properties)) {
    return <FallbackYamlTextarea value={fallbackYaml} onChange={onFallbackYamlChange} />;
  }

  const propEntries = Object.entries(properties);

  // empty properties → placeholder
  if (propEntries.length === 0) {
    return (
      <div className="text-xs text-gray-400 italic py-1">（无可配置参数）</div>
    );
  }

  // ── Structured form ───────────────────────────────────────────────────────
  function handleChange(key: string, newVal: unknown) {
    onChange({ ...value, [key]: newVal });
  }

  return (
    <div className="flex flex-col gap-2">
      {propEntries.map(([propName, propDef]) => {
        const isRequired = required.includes(propName);
        const currentVal = value[propName];

        return (
          <div key={propName} className="flex flex-col gap-0.5">
            <label className="text-xs text-gray-500">
              {propName}
              {isRequired && (
                <span className="text-red-500 ml-0.5">*</span>
              )}
            </label>
            {renderInput(propName, propDef, currentVal, handleChange, testIdPrefix)}
          </div>
        );
      })}
    </div>
  );
}

function renderInput(
  propName: string,
  propDef: PropDef,
  currentVal: unknown,
  handleChange: (key: string, val: unknown) => void,
  testIdPrefix: string,
) {
  const testId = `${testIdPrefix}-${propName}`;
  const t = propDef.type;

  if (t === "string" && Array.isArray(propDef.enum)) {
    const enumVals = propDef.enum as string[];
    const strVal = typeof currentVal === "string" ? currentVal : (enumVals[0] ?? "");
    return (
      <select
        data-testid={testId}
        value={strVal}
        onChange={(e) => handleChange(propName, e.target.value)}
        className="border border-gray-200 rounded px-1.5 py-1 text-xs bg-white"
      >
        {enumVals.map((opt) => (
          <option key={opt} value={opt}>
            {opt}
          </option>
        ))}
      </select>
    );
  }

  if (t === "string") {
    return (
      <input
        type="text"
        data-testid={testId}
        value={typeof currentVal === "string" ? currentVal : ""}
        onChange={(e) => handleChange(propName, e.target.value)}
        className="border border-gray-200 rounded px-1.5 py-1 text-xs"
      />
    );
  }

  if (t === "integer") {
    return (
      <input
        type="number"
        step={1}
        data-testid={testId}
        value={typeof currentVal === "number" ? currentVal : ""}
        onChange={(e) =>
          handleChange(propName, e.target.value === "" ? "" : Number(e.target.value))
        }
        className="border border-gray-200 rounded px-1.5 py-1 text-xs"
      />
    );
  }

  if (t === "number") {
    return (
      <input
        type="number"
        step="any"
        data-testid={testId}
        value={typeof currentVal === "number" ? currentVal : ""}
        onChange={(e) =>
          handleChange(propName, e.target.value === "" ? "" : Number(e.target.value))
        }
        className="border border-gray-200 rounded px-1.5 py-1 text-xs"
      />
    );
  }

  if (t === "boolean") {
    return (
      <input
        type="checkbox"
        data-testid={testId}
        checked={typeof currentVal === "boolean" ? currentVal : false}
        onChange={(e) => handleChange(propName, e.target.checked)}
        className="mt-0.5"
      />
    );
  }

  // unreachable after _hasUnsupportedProp check, but TypeScript needs it
  return null;
}

function FallbackYamlTextarea({
  value,
  onChange,
}: {
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="flex flex-col gap-0.5">
      <label className="text-xs text-gray-500">config (yaml, fallback)</label>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="font-mono text-xs border border-gray-200 rounded p-1.5 w-full min-h-[60px] resize-y"
        placeholder="key: value"
        spellCheck={false}
      />
    </div>
  );
}
