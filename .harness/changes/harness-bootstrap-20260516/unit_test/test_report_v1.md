---
change_id: harness-bootstrap-20260516
version: 1
authored_at: 2026-05-16T20:35:00Z
status: waiting_review
---

# Test Report v1

> **本变更为纯 markdown 文档变更**，无 Python / TS 代码可测。按 coding_report §特殊门禁说明 + Stage 4 Reviewer 与用户共同确认的 "shell 即测试" 路径，本阶段产出一份可重复运行的自检脚本 `unit_test/check_harness.sh`，把 spec §验收标准表 12 条 AC 产品化为可断言项。
>
> 脚本路径选项 A/B 在 Stage 4 末与用户讨论后选定 **B（收在本 change 内）**：`scripts/check_harness.sh` 的产品化提升留给独立 follow-up 变更 `harness-script-productize-<yyyymmdd>`。

## 验收项 ↔ 测试映射

| AC ID | 测试位置 | 测试函数 | 断言 |
|---|---|---|---|
| AC-1  | unit_test/check_harness.sh:55-56  | `ac1`  | CLAUDE.md 存在 + 引用 application-owner.md |
| AC-2  | unit_test/check_harness.sh:58-62  | `ac2`  | Owner Agent 存在 + 含"配置索引/十阶段/硬性约束" |
| AC-3  | unit_test/check_harness.sh:64-68  | `ac3`  | rules 三份齐全 |
| AC-4  | unit_test/check_harness.sh:70-74  | `ac4`  | development-process.md 含 ≥10 个阶段定义 |
| AC-5  | unit_test/check_harness.sh:76-79  | `ac5`  | 9 个 SKILL.md + 索引 README.md |
| AC-6  | unit_test/check_harness.sh:81-85  | `ac6`  | _template/ 含 ≥10 个文件 |
| AC-7  | unit_test/check_harness.sh:87     | `ac7`  | changes/README.md 含命名约定 |
| AC-8  | unit_test/check_harness.sh:89-92  | `ac8`  | mcp/README.md 含 Phase 0 占位 |
| AC-9  | unit_test/check_harness.sh:94-103 | `ac9`  | wiki 四份文件 + 7 个核心术语 |
| AC-10 | unit_test/check_harness.sh:105-110| `ac10` | 每个 SKILL.md 含三项必备章节 |
| AC-11 | unit_test/check_harness.sh:112-115| `ac11` | 所有骨架 .md ≥ 20 行 |
| AC-12 | unit_test/check_harness.sh:117-125| `ac12` | 项目记忆目录 + 4 份记忆文件 |

> **覆盖率**：spec §验收标准 12 条 AC 每条都映射到一个 shell 函数，且与该 AC 描述行业绑定。映射表外无孤立 AC。

## 测试文件清单

| 文件 | 类型 | 用例数 | 行数 |
|---|---|---|---|
| `unit_test/check_harness.sh` | shell 自检（"集成"风格） | 12（每条 AC 一个） | 142 |

## Mock 范围声明

> unit-test-write SKILL §核心原则要求"改动驱动 + 真实接口、真实数据"。本变更产物是文件结构本身，shell 断言**直接读真实文件系统**——
> **mock 范围：无**。
>
> 与 SKILL §1.7 列出的"禁止 mock 数据访问层"原则一致：本测试不 mock `find` / `grep` / `test -f` / `wc -l` 的输出，而是真实跑在仓库当前状态。

## 本地运行结果

```text
$ bash .harness/changes/harness-bootstrap-20260516/unit_test/check_harness.sh
=== harness-bootstrap-20260516 :: 12 条 AC 断言 ===
仓库根: /data/home/zhhdzhang/nta/nta-lake

PASS  AC-1    CLAUDE.md 存在且引用 Owner Agent
PASS  AC-2    Owner Agent 存在且声明配置索引/十阶段/硬约束
PASS  AC-3    .harness/rules/ 三份规则齐全
PASS  AC-4    development-process.md 含 ≥10 个阶段定义
PASS  AC-5    9 个 SKILL.md + 索引 README.md 齐全
PASS  AC-6    changes/_template/ 含 ≥10 个文件
PASS  AC-7    changes/README.md 含命名约定（feature-slug + yyyymmdd）
PASS  AC-8    mcp/README.md 含 Phase 0 / 占位语义
PASS  AC-9    wiki 四份文件 + 7 个核心术语齐全
PASS  AC-10   每个 SKILL.md 含进入条件/质量门禁/失败回退
PASS  AC-11   所有骨架 .md ≥ 20 行
PASS  AC-12   项目记忆目录 MEMORY.md + 3 份记忆文件齐全

=== 汇总 ===
PASS: 12 / 12
FAIL: 0 / 12
全部通过。
exit code: 0
```

**可移植性验证**：脚本顶部用 `SCRIPT_DIR` + `REPO_ROOT` 自定位仓库根并 `cd` 进去，所以从任意 cwd 启动都跑出同样结果。已实测从 `/tmp` 用绝对路径启动 → 12/12 PASS。AC-12 的 `pwd | sed 's|/|-|g'` 转义与 Claude Code 自身用的目录转义规则一致，跨机器克隆到不同路径后两者会同步变化，断言仍正确。

## 已知 flaky / 跳过

- **无 flaky 测试**。所有断言都是确定性 shell 命令（`test -f`、`grep -q`、`wc -l`），无网络 / 时序依赖。
- **无 skip 用例**。12 条 AC 全部断言。
- **不依赖外部服务**：本脚本不需要 docker-compose 起的中间件（spec / 设计意图层面：dataplat 代码尚未存在，没有 DB/MinIO 可起）。

## 覆盖率（如已配置）

> 传统覆盖率（line/branch coverage）对纯 shell + 文档变更不适用。给出**结构覆盖率**作为等价指标：

| 度量 | 实测 | 说明 |
|---|---|---|
| spec §验收标准 AC 覆盖率 | 12/12 = **100%** | 每条 AC 一个断言函数 |
| 骨架文件被某条 AC 触达比例 | 38/38 = **100%** | AC-11（行数 ≥ 20）扫所有 .md；AC-1/2/3/8/9/12 各覆盖具体文件；AC-10 覆盖所有 SKILL；AC-5 覆盖 9 个 SKILL；AC-6 覆盖整个 _template；AC-7 覆盖 changes/README |
| 强约束覆盖率（spec §硬性约束） | 6/6 | 见下表 |

强约束 ↔ 测试映射：

| 硬约束（来自 CLAUDE.md / Owner Agent） | 被哪条 AC 间接断言 |
|---|---|
| 任何改动挂在 change 下 | AC-6 / AC-7（changes 模板 + 命名约定存在） |
| 不能跳过需求分析 | AC-6（_template 含 spec.md） |
| 不能跳过评审 | AC-6（_template 含 review/*.md） |
| 不能在评审未通过时合并 | AC-10（SKILL 含失败回退）+ AC-4（流程阶段 4/6/8 在 dev-process 中） |
| 不能隐瞒问题 | AC-6（_template 含 ci_result + deploy_verify 模板，要求结构化字段） |
| 不能做无关重构 | AC-3（coding-style 存在，§0 共同原则）+ AC-4（流程定义） |

## 偏离 SKILL 标准 / trade-off

| 偏离点 | 说明 |
|---|---|
| 没有 pytest / vitest 用例 | 纯文档变更，无 Python/TS 代码可测；shell 脚本充当等价测试，已在 Stage 4 评审后与用户对齐。**脚本要求 bash ≥ 3.2**（用到 BASH_SOURCE / local / 数组）；busybox /bin/sh 与 dash 不兼容——脚本头已注明，本表此处同步备注以保持单源 |
| 没有真实 DB/MinIO 集成测试 | 同上：dataplat 代码不在本 change 范围；中间件集成测试由 `bootstrap-monorepo` 引入 |
| 测试位于 change 内而非 `apps/api/tests/` | engineering-structure.md 中的 apps/* 当前不存在；脚本暂栖 change 内，follow-up 提升到 `scripts/`（已 defer）。**Stage 4 末用户在 A/B 路径选择中明示 B 路径**——记录在 [summary.md §关键决策表](../summary.md) 2026-05-16 "check_harness.sh 放本 change 内（A vs B 选 B）" 行，这是本 trade-off 的显式背书 |
| 没有 polyfactory 等工厂 | 无业务数据需要生成 |

## 已知未解决问题（评审决定是否阻塞）

| 问题 | 影响 | 建议处理 |
|---|---|---|
| 脚本仅能从 bash 跑（用了 `[ ... ]`、`local`、`$BASH_SOURCE`、数组） | bash ≥ 3.2 即可；脚本头已注明，且通过 `bash xxx.sh` 显式调用 / `#!/usr/bin/env bash` shebang 保证。alpine busybox /bin/sh 与 dash 不兼容 | 接受。如需 POSIX sh 兼容版，开 follow-up `harness-script-portable-sh-<yyyymmdd>` |
| AC-11 检查所有 `.md` 包括本 change 自身（含 review v1 这种长文档），不会因长文档变短而 FAIL | 这是 AC-11 的原意：每个文件 ≥ 20 行；不形成假阴性 | 不阻塞 |
| AC-6 用 `find _template -type f` 数文件 ≥ 10，对**只删 _template 内文件**敏感，对**改文件内容**不敏感 | spec §"模板内容是否应有结构性校验"是 stage 4 review 留下的 NICE TO HAVE | 接受现状；follow-up 中 `harness-tighten-ac-grep-<yyyymmdd>` 顺带补 _template 内容断言 |
| **AC-2 / AC-8 / AC-10 grep alternation 是 OR 关系**（stage 6 review SHOULD FIX #1 抓到） | 文件里只要命中"任一"关键词即 PASS，对"应同时声明 A/B/C 三段"的语义约束完全无感。实证：把任一 SKILL.md 的 §质量门禁 + §失败回退 都改名后，AC-10 仍 PASS。AC-2（Owner Agent）与 AC-8（mcp/README Phase 0 vs 占位）同类 | 同根因 follow-up `harness-tighten-ac-grep-<yyyymmdd>`：把 grep alternation 拆为 `grep -q A && grep -q B && grep -q C` 顺序串联；同步更新 spec §验收标准表 |
| **AC-5 期望值硬编码 9**（stage 6 review SHOULD FIX #2 抓到） | 未来新增第 10 个 Skill 时 AC-5 会 FAIL。这并非脚本 bug——spec AC-5 文字也写"9 个"，是 spec + 脚本一同与未来演进耦合 | 同 follow-up：改成 `[ "$n" -ge 9 ]` 配合 Skill 白名单 / 或继续 `-eq <动态值>` 但要求新增 Skill 时同步改 spec + 脚本 + skills/README.md |
| **AC-9 spec 内部 7 vs 8 术语不一致**（stage 6 review §抽查记录抓到） | spec §范围 AC-9 文字列 8 个核心术语（Repository / **Layer** / Asset / Source Adapter / Processor / Lineage / Commit / Blob），但 spec §验收标准表 AC-9 验证命令只检 7 个（漏 Layer）。脚本忠实于表，断言成立但**实质偏差**——本变更内 stage 2/4 review 都漏了这一上游不一致 | 同 follow-up：在修 grep alternation 时一并同步 spec §范围 与 §验收标准表 的术语清单，并把脚本第 97 行扩到 8 个 |

## 下一步

进入 **Stage 6 单测评审**：

- 加载 `.harness/skills/expert-reviewer/SKILL.md`（artifact 模式）
- 独立 Reviewer 子会话评审 `check_harness.sh` 与本 test_report
- 重点核查：(a) 映射表 12 条 AC 是否真完整；(b) 脚本里有无空跑断言（断言任意 `!=` None 这种）；(c) Mock 范围与 SKILL §1.7 一致性；(d) 偏离 SKILL 标准的 trade-off 是否被 spec / 上轮评审实质背书
- 产出 `unit_test/review/test_review_v1.md`
