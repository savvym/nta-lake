# Rule：data-not-code-pivot

> **硬约束级别**：违反即视为流程失败。stage 2 reviewer 在评审任何新 change 时必须先扫这份清单确认 spec 不违反；stage 4 / stage 6 reviewer 在审 code / test 时复查实现没违反。

## 来源

本 rule 是 change [`platform-north-star-pivot-20260520`](../changes/platform-north-star-pivot-20260520/summary.md) 的硬约束沉淀。详细论证见 `.harness/design.md`：

- [§ 北极星](../design.md#北极星)
- [§ 永不做清单](../design.md#永不做清单)
- [§ 三层算子模型](../design.md#三层算子模型)
- [§ stats-first 设计](../design.md#stats-first-设计)
- [§ 行级血缘](../design.md#行级血缘)
- [§ 迁移路径](../design.md#迁移路径)

## 永不做清单（拷贝自 design.md，方便 reviewer 单文件扫描）

以下功能在本平台上 **永不实现**：

- **不做 branch**：训练数据没有"实验分支"语义；用新建 repo 或 fork 表达"另一份数据"
- **不做 merge**：数据不需要合并冲突解决；用 union Operator 或 Loader 多 input
- **不做 cherry-pick**：snapshot 是原子写入，不存在"挑某几个改动"
- **不做 rollback / force-push**：snapshot 不可改；已被训练用过的 snapshot 永不可删
- **不做 row-level diff**：行没有"修改前/后"语义
- **不做 blob → blob 派生图**：行级 source_ref + `/lineage/reverse?bronze_blob_sha=...` 已够
- **不做 Asset 抽象 / manifest.yaml 强制**：bronze 用文件树就够
- **不做"silver 是文件树"**：silver/gold 强制表形态（Parquet/JSONL + schema）
- **不做强 schema 在 bronze**：schema 只在 silver/gold 强制

## 旧→新术语对照表

老 change（22 个已闭环）用的术语在新 change 评审时必须翻译成 v2 词汇。对照表：

| 旧术语（v1） | 新术语（v2） | 备注 |
|---|---|---|
| Processor（repo→repo） | Loader（bronze→silver row）+ Operator（row→row） | 拆分两层 |
| `processors/` 目录 | `loaders/` + `operators/` 两个目录（实现见 follow-up） | 物理拆分待 `operator-protocol-*` |
| Commit | Snapshot（API rename 见 follow-up） | 心智先转，API/UI 词汇待 `api-snapshot-rename-*` |
| `commit.parents: list[str]`（DAG） | `snapshot.parent: str \| None`（线性单链） | 数据结构待 `api-snapshot-rename-*` |
| Recipe = nodes[] of Processor | Recipe = 1 Loader + N Operators | YAML 形态变更待 `recipe-yaml-v2-*` |
| Asset / manifest.yaml | （不存在；bronze 用文件树） | 永久弃用 |
| Lineage = commit-level DAG | Lineage = commit + row 双层 | 行级 lineage_ops + source_ref 字段 |
| Silver/Gold 推荐 Parquet | Silver/Gold **强制** Parquet/JSONL + schema 注册 | 强制化待 `silver-schema-enforce-*` |

## reviewer 必查项

新 change 在 stage 2 评审时，reviewer 必须完成以下检查并在 review 报告里逐项给 PASS/FAIL：

- [ ] spec 用 v2 词汇引用 design.md（Loader / Operator / Snapshot / source_ref / stats / lineage_ops）；用旧术语必须有理由（如"老 Processor 重写前过渡用"）
- [ ] spec 范围**不**包含 § 永不做清单 中的任何一条（branch / merge / cherry-pick / rollback / row-diff / blob 派生图 / Asset / manifest.yaml 强制 / silver 文件树 / bronze 强 schema）
- [ ] 如果 change 涉及 silver/gold repo 数据形态：spec 必须明确该 repo 走 Parquet/JSONL + schema 注册 + 每行 `source_ref` + 每行 `stats`；不允许往 silver/gold 写裸文件树
- [ ] 如果 change 涉及 Processor 接口扩展：spec 必须说明是"first-gen Processor 过渡保留"还是"应该走 Operator/Loader 新模型"；新模型路径的 spec 要引用 follow-up change（`operator-protocol-*` 等）

如果以上任意一条 FAIL → MUST FIX 打回。

## 松绑流程

如果某条永不做清单未来需要松绑（如真的有 PB 级数据需要 Iceberg 后端）：

1. **不**在单个 feature change 里偷偷松绑
2. 开新 change `platform-pivot-v2-<yyyymmdd>`，重写 design.md 对应段 + 本 rule 文件
3. 走完整 10 阶段流程（特别是 stage 2 reviewer 必须确认论证充分）
4. 老 change 不回写

## 历史

| 时间 | 事件 |
|---|---|
| 2026-05-20 | 本 rule 由 `platform-north-star-pivot-20260520` 创建。来源：22 个 change 闭环后，design.md v0.2 "data 上加 git"路线被业界（lakeFS/Pachyderm 商业证伪）+ 实际 demo 路径（无人用 branch/merge）双重证伪，pivot 为"LLM 训练数据工厂"。详细决策日志见该 change spec |
