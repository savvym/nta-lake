# request-analysis Reference: AC Kind Lint

本文件保存 AC 分层规约的完整背景和豁免清单。主 `SKILL.md` 只保留 stage 1 / stage 2 必读摘要。

## 背景

`pipeline-orchestrator-mvp-20260518` stage 9 首次真跑端到端 demo 暴露 3 个真 bug：demo recipe 字段名误用、fixture 撞 hash、`pipeline_cache` FK 缺 CASCADE。直接根因是大量 AC 只用 grep / `test -f` / import 检查，`self_check` 全 PASS 不能证明业务路径跑通。

## kind 字段

`spec.md` 验收标准表必须有 `kind` 列：

- `static`：源码骨架检查，如 grep、`test -f`、parse、dry-import。不真跑业务路径。
- `behavioral`：真跑代码并断言行为。

硬约束：每个非豁免 change 至少 1 条 `kind: behavioral` AC。

## behavioral 判定

任一层级即可：

| 层级 | 形态 | 例子 |
|---|---|---|
| L1 | 真起服务 curl smoke | `curl -X POST http://localhost:8080/repos ...` |
| L2 | ASGITransport in-process roundtrip | `httpx.AsyncClient(transport=ASGITransport(app=app)).post(...)` |
| L3 | 真跑纯逻辑 / fixture | `load_recipe(yaml_text)` 或 `bash scripts/lint/test_*.sh` |

不算 behavioral：

- `uv run python -c "import dataplat_api.foo"`
- `grep "@router.post" routers/foo.py`
- `test -f tests/test_foo.py`

## lint 双条件

`scripts/_self_check.sh::run_ac_kind_lint` 对未豁免 spec 执行：

```bash
awk '/^## 验收标准/{p=1;next} p && /^## /{exit} p' spec.md \
  | grep -qE '^\|[^|]*\|[[:space:]]*kind[[:space:]]*\|'
awk '/^## 验收标准/{p=1;next} p && /^## /{exit} p' spec.md \
  | grep -qE '^\|[[:space:]]*AC-[0-9]+[a-z]?[[:space:]]*\|[[:space:]]*(\*\*)?behavioral(\*\*)?[[:space:]]*\|'
```

第二条必须锚定 AC 行的 kind 单元格；不接受裸 `grep -q behavioral`。

## 自声明豁免

纯文档 / 纯 harness / 纯 wiki / 纯 scripts 变更可在 `spec.md` frontmatter 加：

```yaml
ac_kind_lint: exempt
ac_kind_lint_exempt_reason: |
  纯 harness 变更（仅改 .harness/* + scripts/*）；
  通过 reviewer 跑 git diff --stat origin/main..HEAD 验证。
```

### 豁免判定

stage 2 reviewer 必跑：

```bash
git diff --stat origin/main..HEAD
```

合法路径：

- `.harness/*`
- `wiki/*`
- `scripts/*`
- `*.md`

任一业务代码路径出现，`ac_kind_lint: exempt` 必须打回。

## grandfather 豁免清单

永久豁免：

- `harness-bootstrap-20260516`
- `harness-reviewer-agent-separation-20260518`

暂豁免：

- `bootstrap-monorepo-20260516`
- `core-domain-model-20260516`
- `cas-storage-20260517`
- `auth-scaffold-20260517`
- `repo-api-mvp-20260517`
- `commit-api-mvp-20260517`
- `rq-worker-skeleton-20260517`
- `processor-framework-20260517`
- `adapter-framework-20260517`
- `llm-gateway-mvp-20260517`
- `adapter-firecrawl-20260517`
- `llm-qa-gen-20260518`
- `web-mvp-pages-20260517`
- `web-write-flows-20260517`
- `repo-files-tab-20260517`
- `sdk-cli-mvp-20260518`
- `pipeline-orchestrator-mvp-20260518`

这些 ID 只为历史兼容；未来新 change 默认不豁免。

## 混合 AC 拆分

错误：

```markdown
| AC-N | mixed | POST /repos 返回 201 + 路由文件含 @router.post | curl + grep | 201 + grep 命中 |
```

正确：

```markdown
| AC-Na | static | 路由文件含 @router.post(/repos) | `test -f routers/repos.py && grep -q "@router.post" routers/repos.py` | grep 命中 |
| AC-Nb | behavioral | POST /repos 返回 201 + repo_id | `uv run pytest -q apps/api/tests/test_repos.py::test_create_201` | pytest passed |
```
