# .harness/changes/

每一次对仓库的实质改动都对应这里的一个目录，记录"需求→实现→验证"的完整档案。**所有 commit 都必须能追溯到某个 change**。

## 目录命名

```
<feature-slug>-<yyyymmdd>/
```

- `feature-slug`：kebab-case，简短描述目的，例如 `bootstrap-monorepo`、`add-firecrawl-adapter`、`refactor-llm-gateway-cache`。
- `yyyymmdd`：变更开启的日期（本地时区）。

跨多天的变更**不**改名；新一轮迭代用版本号（spec_v2 / review_v3）表达。

## 启动一个新变更

```bash
# 1. 复制模板
cp -r .harness/changes/_template .harness/changes/<feature-slug>-$(date +%Y%m%d)

# 1.5 立即删除模板自带的"如何用模板"说明（它只对 _template 自身有意义；不删会留孤儿）
rm .harness/changes/<feature-slug>-$(date +%Y%m%d)/README.md

# 2. 编辑 summary.md（填 title / owner / started_at / stage=request_analysis）

# 3. 加载 .harness/skills/request-analysis/SKILL.md，开始写 spec.md / tasks.md
```

## 子目录结构

模板里已经把十阶段的产物布好：

```
<change-id>/
├── summary.md                          # Single Source of Truth
├── request_analysis/
│   ├── spec.md
│   ├── tasks.md
│   └── review/
│       ├── spec_review_v1.md
│       └── tasks_review_v1.md
├── coding/
│   ├── coding_report_v1.md
│   └── review/
│       └── code_review_v1.md
├── unit_test/
│   ├── test_report_v1.md
│   └── review/
│       └── test_review_v1.md
├── ci_result/
│   └── ci_result_v1.md
└── deployment/
    └── deploy_verify_v1.md
```

模板里的 `v1` 文件是占位，**不要直接 commit 占位内容**。要么填实，要么先删（如某变更不涉及部署面，可以删 `deployment/`）。

## summary.md 的作用

`summary.md` 是这个 change 的唯一可信状态。任何会话切换、人员交接、复盘归因都看它。

它必须实时反映：

- 当前阶段（十阶段之一）
- 各阶段评审轮次与结论
- 关键决策（含取舍理由）
- 当前阻塞点
- CI / 部署状态
- 最终交付：合并 commit SHA、PR 链接、部署版本

详见 `_template/summary.md` 的字段说明。

## 版本号约定

review 与 generator 产物都用 `_v{N}.md` 后缀。**只增不改**：

- 第 1 轮 spec：`spec.md`（无后缀，即 v1）；如需迭代则下一版 `spec_v2.md`，原文件保留。
- 第 1 轮 review：`spec_review_v1.md`；不通过 → `spec_review_v2.md`。
- coding_report、test_report、code_review、test_review、ci_result、deploy_verify 同理。

> 实践上，spec.md 与 tasks.md 因为是 Generator 的连续产物，允许直接修改并 git 留版本历史；review 文件**必须**新文件递增。

## 关闭一个变更

满足以下条件可视为关闭：

```text
阶段 10 用户确认完成
summary.md 末段含交付记录：merge commit / PR / 部署版本
所有阶段产物的最终版本 verdict = APPROVED / PASS / SUCCESS
未关闭的 SHOULD FIX 都已转化为 follow-up（新 change 或 task）
```

关闭后**不删目录**——这是项目记忆的一部分。

## 历史 change 的查阅

跨会话恢复上下文时：

1. 找最近修改的 `summary.md` 看当前活跃 change。
2. 想看某个决策为什么这样定 → grep `changes/` 里的 review / summary。
3. 想看类似改动的先例 → 按 feature-slug 关键词搜历史 change。
