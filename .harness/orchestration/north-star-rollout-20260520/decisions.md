---
rollout_id: north-star-rollout-20260520
last_updated: 2026-05-20T16:30:00Z
---

# Decisions Log：北极星 rollout

> application-owner 在无用户介入授权下做出的自主决策。每条 ≤ 5 行；包含 why + when-to-revisit。

## D-1：依据 v2 三阶段，不再用 v1 十阶段

- **决策**：所有 27 个 follow-up changes 一律按 `.harness/rules/development-process.md` v2 走 Design / Implementation / Verify 三阶段
- **依据**：上一个 change `platform-north-star-pivot-20260520` 已并入 main（commit `0e4bf66`），CLAUDE.md 已更新硬约束 #4
- **revisit**：v2 跑 3 个 change 后，如发现 Phase 2 sonnet 端到端 fail rate > 30%，回到本文件加 D-X 评估是否需要中间产物（如先生成代码再单独跑测试）

## D-2：所有 27 changes 都跑完整 reviewer，不允许 self-attest

- **决策**：即使是看起来很小的 change（如 adapter-jsonl-import），也走 opus reviewer 两次
- **依据**：每个 change 都涉及 packages/core 接口或新 schema，按 `application-owner.md` § 何时跳过 reviewer 的"不允许跳过情况"列表都需要 reviewer
- **revisit**：如果 W4 内某 change 真的 < 3 行且不动接口（如 backup-restore 纯脚本），可按 self-attest 走

## D-3：data-not-code-pivot.md 第 47 行旧术语残留不在本 rollout scope

- **决策**：`.harness/rules/data-not-code-pivot.md:47` 用 "新 change 在 stage 2 评审时"（v1 stage 词汇），本 rollout 不修
- **依据**：harness 框架本身改动需要单独 harness-* change；本 rollout 是 dataplat 业务 rollout
- **revisit**：W1 完成后如发现 reviewer 反复因这行困惑，开 `harness-stage-terminology-cleanup-*` 单独处理

## D-4：Wave 1 严格串行，不抢跑

- **决策**：W1-1 / W1-2 / W1-3 / W1-4 必须串行；前一个未 verify APPROVED 不启动下一个
- **依据**：4 个 change 都改 packages/core；并行会导致接口设计相互否决
- **revisit**：仅在 W1-2 完成时评估 W1-3 / W1-4 是否真有依赖（若发现实际可并，更新 roadmap）

## D-5：Wave 3 内最多并行 3 个 change

- **决策**：W3-1 / W3-2 / W3-4 一组（adapter / loader 不互冲突），可并；W3-5 / W3-6 单独串
- **依据**：每个 change 独立目录，无 packages/core 修改
- **revisit**：第一次实测并行 spawn 后看是否冲突；若 sonnet 之间互改同一文件（如 apps/web 路由表）则降为串行

## D-6：image-to-text 走 Operator chain 不走 Loader

- **决策**：图片转文字在 W2-3 实现为 4 个 Operator（triage / caption / mermaid / unicode-art），不在 Loader 阶段做
- **依据**：用户原话"应该在 Operator chain 阶段做，不过这个时候，应该是对文档进行了切分了吧"；Operator 模型支持 stats-first 路由 + 行级 lineage_ops 可追溯
- **revisit**：W2-3 实测如果 VLM 调用成本失控（单 PDF > $1），评估是否前置到 Loader 阶段做"装饰图直接丢"

## D-7：chunker 作为独立 Operator，不嵌进 Loader

- **决策**：W2-2 chunker 是独立 Operator；Loader 输出"整篇文档一行"，由后续 chunker Operator 拆
- **依据**：用户最终目标里"切分"应可调参（按 token / heading / 段落）；不同 recipe 切分策略不同；放 Loader 内会失去灵活性
- **revisit**：如果 90% recipe 第一步都是 chunker，考虑加 syntactic sugar 让 recipe 默认 inject

## D-8：silver row 含图的 schema 用 placeholder + images column

- **决策**：silver row.text 里图片保留 `<image id=N>` 占位；row.images 是 list[ImageRef]；Operator chain 把占位替换成文字
- **依据**：让 Loader 不用关心怎么转图，纯结构化抽取；Operator 才决定转法
- **revisit**：W1-4 实测如果占位语法（< vs Markdown ![]）跟下游 LLM tokenizer 冲突，调整占位语法

## D-9：进度跟踪用 3 个 orchestration 文档而非 git issue / TaskList

- **决策**：roadmap.md（不变骨架）+ dashboard.md（每 change 回写状态）+ decisions.md（自主决策日志）
- **依据**：(a) TaskList 重启会丢；(b) 没接 GH issue write 权限；(c) 文件级状态可被任何 spawn 出来的 sub-agent 读取
- **revisit**：跑完 W1 后看 dashboard 维护成本，必要时合并 / 简化

## D-10：不跑 bootstrap-monorepo（CLAUDE.md 建议的第一个 change）

- **决策**：跳过 `bootstrap-monorepo-<yyyymmdd>`；直接进 W1-1
- **依据**：仓库已有 21 个 dataplat change 闭环，monorepo 目录骨架早已成型（apps/api/web、packages/core/api-types/sdk-py、plugins/、worker、recipes 等都存在）；CLAUDE.md § 当下项目状态那段是 phase 0 时期的指引，已过时
- **revisit**：W1-1 进 design 时如发现某个目录其实不存在（如 packages/api-types 还没建），spawn implementer 时附 monorepo 骨架补建任务

## D-13：harness v2 → v3 流程简化（W1-2 起所有 change 适用）

- **决策**：用户在 W1-1 review 阶段诊断"reviewer 80% 时间在跑无关 grep 命令 + self_check 增信为 0"，授权 pivot 到 v3：
  - **Phase 1 砍 reviewer**：application-owner 直接写 mini-design（≤ 50 行：一句话目标 / 范围+非范围 / 2-3 条 **behavioral AC，每条对应 pytest / vitest 用例** / 1-3 条决策）
  - **Phase 2 sonnet 端到端不变**：编码 + 写单测（业务 AC = 单测）+ push
  - **Phase 3 verify reviewer 保留**：只跑相关 pytest / vitest 验业务正确性 + 看 git diff 是否超范围
  - **self_check 不再每 change 加 block**：业务正确性 100% 靠单测；self_check 仅保留全局 lint（reviewer-lint / ac-kind-lint）做"流程是否完整"层面的快检
  - 每 change agent spawn 从 3 次 → 2 次；design.md 从 100+ 行 → ~50 行；AC 数从 8-12 条 → 2-3 条
- **依据**：W1-1 实测 144 行 design + 12 AC 里 8 条是 grep 命名约定（git diff 一眼可见，AC 化没增信）+ 2 条是 self_check 自身的 meta 检查（不验业务）+ 只有 2-3 条真在验业务；reviewer 90% 时间在 grep 转义 / awk pattern 上踩 harness 自身 bug
- **W1-1 处理**：当前 design + review 不动，直接进 Phase 2；但 AC-11 / AC-12（self_check 相关）豁免，sonnet 不加 `run_api_snapshot_rename` block；业务覆盖完全靠 `test_snapshots_api.py` 单测
- **v3 流程文档**：W1-1 merge 后写 `development-process.md` v3 / `application-owner.md` v3 / `harness_new_change.sh` 模板精简 / 删 design_review.md 默认生成 + 移除 self_check block 强制要求；以独立 harness meta change 提交
- **revisit**：跑完 W1-2 / W1-3 后看 Phase 3 verify 是否还 over-engineered；self_check 全局 lint 部分（reviewer-lint / stage-preflight）是否值得保留

## D-12：v2 template reviewer 字段 hotfix（W1-1 reviewer 发现）

- **决策**：把 `.harness/changes/_template/{design_review,verify_review}.md` 的 `reviewer: opus-phase[13]-reviewer` 改成 `reviewer: claude-agent:opus-phase[13]-reviewer`；同步修复 W1-1 已生成的 review 文件
- **依据**：`scripts/_self_check.sh:1783` reviewer-lint 白名单只接受 `claude` / `self-attest` 起头；v2 模板的原值不在白名单 → 任何 v2 change 跑 `_self_check.sh current` 都会 fail-fast。属 v1→v2 简化遗漏
- **影响**：本 rollout 27 个 change 都受益，无需每 change 手动修
- **revisit**：是否要彻底重构 reviewer-lint 白名单（如加 `^opus-phase` / `^sonnet-phase`）—— 当前 hotfix 已够；若 Wave 末仍觉别扭，开 `harness-reviewer-lint-cleanup-*`

## D-11：每 change 一个 commit（除非 design.md 明确分阶段）

- **决策**：Phase 2 sonnet 默认单 commit；design.md 任务多到必须分时再说
- **依据**：v2 development-process.md § Phase 2 第 5 条"单一 commit（除非 design 明确分多个）"
- **revisit**：每个 wave 末复盘是否需要在 design 模板加"分阶段 commit 建议"
