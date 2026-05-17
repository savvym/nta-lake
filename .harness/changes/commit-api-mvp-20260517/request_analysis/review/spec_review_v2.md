---
change_id: commit-api-mvp-20260517
target: spec.md
target_version: 2
review_version: 2
reviewer: claude-stage2-reviewer-v2
reviewed_at: 2026-05-17T10:00:00Z
verdict: APPROVED
---

# Spec Review v2

> 本次只复核 v1 MUST FIX（7 条）的消化情况，并扫描 v2 是否引入新 MUST FIX。SHOULD FIX / NICE TO HAVE 不重复评审（除非 v2 引入新 MUST FIX）。

## 检查清单结论

> 引用 `.harness/skills/expert-reviewer/SKILL.md` §1 plan 模式 spec.md 列表。

- [x] 背景写明了为什么现在做（spec.md L16-18，与 v1 一致）。
- [x] 问题陈述对外部读者可理解（L20-26）。
- [x] 范围 / 非范围都有（L28-48，明确把"并发 race 单测"列为 follow-up，与 v1 SHOULD FIX-4 deferred 路径一致）。
- [x] 每条验收标准可演示且可机械化（AC-1~AC-5/AC-12/AC-13 均补一行式验证命令；AC-6~AC-11 由集成测试覆盖）。
- [x] 风险有缓解或显式 accept（5 条风险全部映射到 AC-11 测试或 deferred 声明）。
- [x] 没有把已有架构当新提案（依然引用 design.md §4.4、cas-storage、repo-api-mvp 已有产物）。
- [x] 决策表覆盖 12 项关键决策（含新加的 `created_at` 是否参与 hash 与 `race 单测` deferred 决策）。

## v1 MUST FIX 消化复核（7/7）

| # | v1 问题摘要 | 复核位置 | 消化状态 | 证据 |
|---|---|---|---|---|
| 1 | 缺一行式 AC 验证命令表 | spec L66 / L71 / L76 / L81 / L84 / L148 / L151 | **CLOSED** | AC-1 ~ AC-5 / AC-12 / AC-13 每条都给出一行式 `uv run python -c "..."` 或 `bash scripts ...` 验证命令（共 8 条 `uv run` 命令 + 1 条 `bash scripts` 命令）。注：v1 复检指引中的 `grep -E "uv run python -c\|test -f\|bash scripts"` 期望 ≥ 7，实测 6——差异来自 AC-12 用 `uv run ruff/mypy` 而非 `python -c`，正则未匹配，但语义上 AC-12 验证命令存在且形式合理。 |
| 2 | `created_at` 三处矛盾（AC-1 schema vs AC-9/AC-10 公式 vs tasks T-3 服务端算）| spec L62-66、L114、L121、L169 | **CLOSED** | 选择方案 (B)：`CommitCreate` schema 明确 **不含** `created_at`（L65 + AC-1 验证命令 `assert 'created_at' not in CommitCreate.model_fields`）；AC-9 L114 显式 `created_at 不参与 commit canonical hash`；AC-10 L121 `不含 created_at`；决策表 L169 写 (B) 完全去除 + 理由。`CommitRead` 仍含 created_at 作 audit（与 hash 解耦）。 |
| 3 | lineage canonical 递归 sort_keys 规则未钉死 | spec L112、L116、L176 | **CLOSED** | AC-9 L112 显式 `Lineage.model_dump(mode="json")` 得到 plain dict；L116 不变量条款明示 `不允许 lineage 内嵌任何 datetime / UUID / 自定义对象（mode="json" 已保证）`；决策表 L176 同步。 |
| 4 | AC-8 「事务内」 vs 风险 #3 「事务前」内部矛盾 | spec L100、L157、L172 | **CLOSED** | AC-8 L100 改为「**Blob 存在性校验在事务前**完成（异步 `store.exists()` 串行调用），缺失 → 400」；风险 #3 L157 描述与 AC-8 一致；决策表 L172 写 "(b) 事务前" 并给理由。 |
| 5 | AC-11 缺 hash 单元测试 | spec L134-135 | **CLOSED** | (g1) `_canonical_tree_bytes(unordered) == _canonical_tree_bytes(sorted)` + `_commit_hash(t, [p1,p2], ...) == _commit_hash(t, [p2,p1], ...)`，**不依赖 PG/MinIO**；(g2) 顺序幂等端到端。两个测试拆开列出。 |
| 6 | AC-11 缺 2MB 大文件 round-trip | spec L142 | **CLOSED** | (n) `admin POST 2MB+17 字节随机内容 → 200 + sha256 与本地 hashlib.sha256 一致；GET 同 sha256 → 流式字节完全相等`。 |
| 7 | AC-11 缺 lineage round-trip | spec L143 | **CLOSED** | (o) `POST commit 含 Lineage(produced_by=ProducedBy(kind='processor', name='x', version='0.1', config_hash='c'*64), inputs=[InputRef(repo='r', commit='a'*64)], run_id='r1', env={'k':'v'}) → 200；GET 同 hash → lineage 字段反序列化为完整 Lineage 模型`。`Lineage / ProducedBy / InputRef` 三类已在 `packages/core/src/dataplat_core/domain/lineage.py` 落地（已核验）。 |

**MUST FIX 残留 = 0**

## 复检命令实跑结果

```
grep -E "uv run python -c|test -f|bash scripts" spec.md | wc -l → 6
  （AC-1/2/3/4/5/13 命中；AC-12 用 ruff/mypy 不匹配但语义达标。预期 7 但 v1 复检命令正则覆盖不全；建议在 v3 流程中放宽为 `uv run|bash scripts` 或在 SKILL 反哺中记录。）
grep -nE "created_at" spec.md → 8 处，全部语义一致（CommitCreate 不含 / canonical 不含 / CommitRead 含作 audit）
grep -nE "model_dump\(mode=.json.\)|lineage canonical" spec.md → 4 处命中（修订记录 + AC-9 公式 + 不变量 + 决策表）
awk '/AC-8/,/AC-9/' spec.md | grep -E "事务前|事务外|begin\(\) 之前|before" → 命中 "Blob 存在性校验在事务前"
awk '/AC-11/,/AC-12/' spec.md | grep -cE "^\s*-\s*\(\w+\)|^\s*\(\w+\)" → 18 个测试条目（≥ 15 达标）
grep -E "矛盾|fix\?|TODO|XXX" spec.md → 仅 1 处"矛盾"，出现在流程偏离声明描述 v1 的历史（非未解决问题）；不阻塞。
```

## 新发现问题（v2 引入）

无新 MUST FIX。

**轻量观察**（不阻塞、不构成 SHOULD FIX）：

- AC-12 验证命令使用 `uv run ruff / uv run mypy` 而非 `uv run python -c`，v1 复检指引的 grep 正则未匹配。此为 v1 检查规则正则覆盖盲区，不影响 spec 自身质量。建议反哺到 expert-reviewer 时把"AC 验证命令"匹配规则放宽到包含 `uv run` 全集。

## Verdict

**APPROVED**（MUST FIX 残留 = 0；无新 MUST FIX）

可进入 Stage 3 / Stage 4 coding。tasks_v2.md 同步评审见 `tasks_review_v2.md`。

## 复检指引（给后续阶段）

本 spec v2 的状态已稳定，可作 Stage 3 编码输入。若 coding 阶段实现 AC-11 (g1) 单元测试时发现 `_canonical_tree_bytes` 跨 Python 版本 hash 不一致，立即回退到 Stage 2 增加 spec 公式补丁——不要在 coding 阶段静默改 canonical 公式。
