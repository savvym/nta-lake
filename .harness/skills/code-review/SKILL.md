---
name: code-review
description: 对代码实现做独立评审，覆盖正确性、风格、架构、风险
applicable_stage: 阶段 4（编码评审）
inputs:
  - 改动的代码 diff（功能分支 vs main）
  - coding/coding_report_v{latest}.md
  - request_analysis/spec.md
  - .harness/rules/coding-style.md
  - .harness/rules/engineering-structure.md
outputs:
  - coding/review/code_review_v{N}.md
---

# code-review Skill

> 评审者必须独立于 coding 阶段的执行者。

## 进入条件

- 阶段 3 Quality Gate 通过；coding_report 已生成。
- 评审者**未参与**本次编码。

## 输入

1. `git diff main...HEAD` 的完整 diff。
2. coding_report：作为"作者声明"对照。
3. spec：验收标准的来源。
4. rules：风格与结构约束。

## 步骤

### 1. 范围审查

- 改动文件清单 = coding_report 声明的清单？不一致 → MUST FIX。
- 改动是否都在 spec 的范围内？发现 scope creep → MUST FIX，要求拆 change。
- 所属目录是否符合 `engineering-structure.md`？错位 → MUST FIX。

### 2. 正确性审查

逐文件读 diff，关注：

- 边界条件：空集合、None、超大输入。
- 并发：异步代码是否有 race、忘记 await。
- 错误路径：异常是否被吞掉、状态是否在异常时正确回滚。
- 数据一致性：DB 事务边界、CAS blob 引用计数（dataplat 特有）。
- 安全：用户输入校验、SQL 注入、路径穿越、权限检查。

### 3. 架构审查

- 是否绕过项目分层（router 直接写 SQL、plugin 直接 import provider SDK 等）。
- 是否引入了未经 ADR 同意的新顶层目录 / 新基础依赖。
- 是否破坏了已有抽象的不变量（如 SourceAdapter/Processor 协议）。

### 4. 风格审查

按 `coding-style.md` 章节逐项核对：

- 类型完整性、async 一致性、命名、注释（少而精）、错误处理、日志、测试组织。
- LLM 调用是否走 Gateway，模板放对位置。
- TS 用 `@dataplat/api-types`，未手写后端响应类型。

### 5. 性能与可观测性

- N+1 查询？大对象一次性 read？
- 列表接口分页？前端虚拟滚动？
- 日志结构化字段足够定位问题？
- 关键路径是否有 metric / span（如已接入 telemetry）。

### 6. 分级标注

每条问题：

- **MUST FIX**：正确性 / 安全 / 架构破坏 / 偏离 spec。
- **SHOULD FIX**：性能、可读性、风格违规、缺少边界测试。
- **NICE TO HAVE**：命名建议、注释建议、未来扩展性提示（**不阻塞**）。

每条问题给出：文件:行号、问题描述、建议方向。

### 7. 给 verdict

- `APPROVED`：MUST FIX = 0。
- `REVISION REQUIRED`：MUST FIX > 0。

SHOULD FIX 不阻塞 verdict，但如有未关闭，必须在 review 报告里列出"deferred 列表 + 跟进位置（task id 或 follow-up change）"。

### 8. 写 code_review 报告

按 `coding/review/code_review_v{N}.md` 模板填：

- 范围与作者声明对照结论
- 分级问题列表（MUST / SHOULD / NICE，每条带位置）
- 跨改动观察（如多处出现的同类问题）
- verdict
- 复检指引：作者修完应运行什么命令验证（`uv run mypy ...`、`pnpm typecheck` 等）

## 产出

- `coding/review/code_review_v{N}.md`。
- `summary.md` 阶段 4 子项：v{N} / verdict / MUST FIX 数 / 报告路径。

## 质量门禁

```text
code_review_v{latest}.md 存在
报告包含分级问题列表 + verdict + 复检指引
verdict ∈ {APPROVED, REVISION REQUIRED}
verdict == APPROVED 时：MUST FIX 数 == 0
```

## 失败回退（评审者侧）

- 看不懂改动 → 在 review 里写 MUST FIX：要求 coding_report 补"为什么这样改"的简短说明。
- 无法判定是否为 scope creep → 询问 owner / Application Owner Agent，在报告中标记 BLOCKED 并停顿，不要硬给 verdict。

## 反模式

- 只挑命名风格不看逻辑。
- 把所有问题标 MUST FIX 当成"严谨"。
- "总体不错" + verdict APPROVED 但没逐文件审。
- 评审中提议大面积重构 / 抽象，**这不是本评审的工作**——开新 change。
- 把 NICE TO HAVE 强行升 MUST FIX 阻塞流程。
