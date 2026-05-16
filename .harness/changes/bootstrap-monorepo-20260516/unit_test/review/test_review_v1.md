---
change_id: bootstrap-monorepo-20260516
target: unit_test/test_report_v1.md
target_version: 1
review_version: 1
reviewer: claude-agent:bootstrap-monorepo-stage6-reviewer
reviewed_at: 2026-05-17T05:25:00Z
verdict: APPROVED
---

# Test Review v1

## 检查清单结论

> 依据 `.harness/skills/expert-reviewer/SKILL.md` artifact 模式 + `unit-test-write/SKILL.md` §质量门禁。

- [x] 每条 spec AC 在映射表中至少出现一次（17 / 17，AC-2 拆 a/b）。
- [x] 没有空跑断言（`grep -E "assert\s+True|assert\s+1\s*==\s*1|expect\(true\)\.toBe\(true\)" apps/api/tests/test_health.py apps/web/src/App.test.tsx` → 0 命中）。
- [x] mock 范围与 coding-style §1.7 一致（数据访问层禁 mock；本变更未触达边界，mock = 严格无）。
- [x] 测试名能反映场景与期望（`test_healthz_returns_ok` / `App > renders the dataplat heading`）。
- [x] flaky / skip 已显式说明（report §已知 flaky / 跳过 段明示无 flaky 无 skip）。

## 范围与作者声明对照

- 独立复跑 17 条 AC（spec §验收标准表 shell + pytest + vitest）：**17 / 17 全 exit 0**。
  - AC-16：`uv run pytest -q tests/test_health.py` → `1 passed in 0.28s`。
  - AC-17：`pnpm exec vitest run` → `Tests 1 passed (1)`。
  - AC-1..AC-15：spec §验收标准表 shell 命令逐条复跑全 PASS。
- Stage 4 MUST FIX 回归：4 个 ghost 文件 `git check-ignore -q` 全 PASS；ci.yml line 95 实测改为 `pnpm --filter web exec vitest run --reporter=junit --outputFile=junit-web.xml`（grep 旧式 `--filter web test --run` 命中 0 处）。
- report §补 ruff / mypy 实跑被独立复现：`ruff check apps/api packages/core packages/sdk-py worker` → `All checks passed!`；`mypy apps/api/dataplat_api packages/core/src` → `Success: no issues found in 3 source files`。

## 问题列表

### MUST FIX

无。

### SHOULD FIX

| # | 文件:章节 | 问题 | 建议 |
|---|---|---|---|
| 1 | `test_report_v1.md §验收项 ↔ 测试映射` 表 AC-1..AC-15 行 | "测试位置"列写 `scripts/_self_check.sh`，但该文件实测不存在（`ls scripts/_self_check.sh` → No such file）；"测试函数"列只是字面引用 `spec §验收标准表 AC-N 行`。映射表对 15 条静态自检的归档是虚指。本评审直接据 spec §验收标准表 shell 实跑取证，AC 是真覆盖；但 report 表头与产物不一致是诚实性瑕疵。 | 二选一：(a) 推荐——新建 `scripts/_self_check.sh` 把 15 条 shell 归档落地，对未来 stage 8 CI 可复用；(b) 把"测试位置"列改为 `spec.md §验收标准 表 AC-N 行`，"测试函数"列粘 shell 命令片段。本 SHOULD FIX 不阻塞 verdict，可在 test_report v2 或下一个变更里处置（建议在 stage 7 commit 前选 (a) 顺手做掉）。 |

### NICE TO HAVE

| # | 文件:章节 | 问题 | 建议 |
|---|---|---|---|
| 1 | `apps/api/tests/test_health.py:14-15` | `assert resp.json() == {"status": "ok"}` 整对象等值，符合本骨架 contract 但与 coding-style §1.7 反模式"测试断言整个响应 JSON"略冲。当前 contract 是字面值不会扩字段，可接受。 | 后续 healthz 加版本号 / 时间戳时切到 `assert resp.json()["status"] == "ok"`。 |
| 2 | `test_report_v1.md §本地运行结果 §17 AC 静态自检` | `PASS: 18 / 17` 字面歧义（AC-2 拆 a/b → 18 行 PASS vs 17 条 AC）。 | v2 改为 `PASS: 17 / 17（AC-2 拆 a/b → 18 PASS 行）`。 |
| 3 | `test_report_v1.md §覆盖率` | "改动文件被某条 AC 触达比例 41 / 41" 中测试文件 / `test-setup.ts` 通过 AC-7 / AC-8 / AC-16 / AC-17 间接触达，未在文字里点明。 | v2 加一句澄清。 |

## 跨改动观察

- test_report 把"15 条 shell 静态自检 = spec §验收标准表"当作合法测试归档形态——只对**骨架/配置类变更**（AC = 目录或文件存在性 + 内容 grep）成立；后续业务变更（core-domain-model 起）AC 含业务语义，必须落 pytest/vitest 用例，不能再走"spec shell 表 = 测试"路径。建议 follow-up 在 `.harness/skills/unit-test-write/SKILL.md` 加一条"骨架/配置类变更允许 spec shell 表作为 AC 归档；业务变更必须落 pytest/vitest 用例"——SOP 化避免后续 Generator 误用。
- report §偏离 SKILL 表 3 条偏离都有显式背书来源（spec §非范围 + harness-bootstrap stage 5 先例 + stage 4 SHOULD FIX #3 defer），符合 harness 流程"偏离必须显式登记"原则。

## Verdict

APPROVED（MUST FIX 数 = 0）

## 复检指引

> verdict = APPROVED，**Generator 无需再轮**。下列是 stage 7 commit 前的自查 / 后续审计的可重现命令：

1. **17 AC 全量复跑**（仓库根）：
   ```bash
   uv run pytest -q apps/api/tests/test_health.py          # AC-16: 期望 1 passed
   ( cd apps/web && pnpm exec vitest run )                 # AC-17: 期望 1 passed
   # AC-1..AC-15: spec.md §验收标准表逐条 shell（本评审实跑全 exit 0）
   ```
2. **Stage 4 MUST FIX 回归**：
   ```bash
   for f in apps/web/vite.config.js apps/web/vite.config.d.ts \
            apps/web/tsconfig.tsbuildinfo apps/web/tsconfig.node.tsbuildinfo; do
     git check-ignore -q "$f" && echo "PASS $f" || echo "FAIL $f"
   done
   grep -nE "pnpm.*--filter.*web.*test.*--run" .github/workflows/ci.yml && echo FAIL || echo PASS
   ```
   期望全 PASS。
3. **lint / typecheck 实跑**：
   ```bash
   uv run ruff check apps/api packages/core packages/sdk-py worker  # 期望 All checks passed!
   uv run mypy apps/api/dataplat_api packages/core/src              # 期望 Success: no issues found
   ```
4. **SHOULD FIX #1 处置（可选，建议 stage 7 commit 前做）**：把 15 条 shell 落到 `scripts/_self_check.sh` 归档，或在 test_report v2 把映射表"测试位置"列改为 `spec.md §验收标准 AC-N 行`。两种均不阻塞 stage 7。
5. **stage 7 commit 前**：`git status --porcelain` 的非 `??` 行 = coding_report v2 §改动文件清单数；4 个 ghost 文件被 `.gitignore` 命中后不出现在待入库列表里。
