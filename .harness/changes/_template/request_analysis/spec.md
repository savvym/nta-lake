---
change_id: <feature-slug>-<yyyymmdd>
version: 1
authored_at: <YYYY-MM-DDTHH:MM:SSZ>
status: draft        # draft | reviewed | approved
---

# Spec：<标题>

## 背景

<为什么现在做？引用相关业务诉求、合规要求、上下游依赖。一两段话。>

## 问题陈述

<目前是什么状况、痛点是什么。可以引用代码 / 截图 / 数据，但不要把所有细节都塞进来。>

## 范围

In scope：

- AC-1: <要做的事情 1>
- AC-2: <要做的事情 2>
- ...

## 非范围

显式列出**不做**的事，避免后续 scope creep：

- <不做 X：理由>
- <不做 Y：理由>

## 验收标准

每条必须可演示且可机械化。命名 `AC-N`，与上面的范围对应。

| ID | 描述 | 验证方式 | 期望 |
|---|---|---|---|
| AC-1 | <e.g. POST /repos 用 bronze layer 创建仓库返回 201> | curl + 单测 | 201 + 返回体含 repo_id |
| AC-2 | <e.g. 上传同一文件两次只产生一个 blob> | 集成测试 | blob count == 1 |

## 风险

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| _e.g. 依赖某 plugin 接口未稳定_ | 中 | 阻塞 | 先和 plugin owner 对齐接口签名 |

## 受影响模块

- `apps/api/...`
- `packages/core/...`
- `plugins/<name>/...`

## 不受影响但易混淆的模块

- `<显式排除的模块>`：理由。

## 待澄清问题

> 在阶段 1 评审前必须清零，或显式标记 deferred。

- [ ] <问题 1>
- [ ] <问题 2>

## 引用

- design.md §x.y
- wiki/architecture.md §x
- 相关 ADR / 历史 change
