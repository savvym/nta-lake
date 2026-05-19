# request-analysis Reference: Cross-AC Checklist

本文件保存历史反哺细节。主 `SKILL.md` 只保留硬规则摘要；generator / reviewer 只有在需要判定具体风险或引用依据时才读本文件。

## 1. schema / hash / fixture 四链路

来源：`commit-api-mvp-20260517`。

- schema 字段、canonical hash 输入、idempotency key、测试 fixture 字段集合必须一致。
- 若字段进入 hash，要么 client 可控，要么 hash 公式不含它。
- 测试 fixture 不得引入参与 hash 的不确定字段，例如服务端 `utcnow()`。

## 2. 事务边界一致

来源：`commit-api-mvp-20260517`。

- AC、风险、tasks 里对事务边界的描述必须一致。
- 典型错误：AC 写"事务内校验"，风险或 tasks 写"事务前校验"。

## 3. AC 命令必须可执行

来源：`rq-worker-skeleton-20260517`。

- 每条 AC 的验证命令必须能被 shell dry-parse。
- Python 一行命令不能写 `python -c "import x; for m in [...]: assert ..."`；复合语句不能接在 `;` 后。
- 推荐写成 generator expression：`assert all(hasattr(X, m) for m in [...])`。

## 4. 风险缓解要落到 AC / 测试

- 风险表若写"测试覆盖"，必须列出对应 AC 或测试文件。
- 没有映射就是自然语言承诺，不算缓解措施。

## 5. commit 历史链连续性

来源：`adapter-framework-20260517`。

- 任何自动产 commit 并更新 ref 的路径，都必须说明 `parents` 来源。
- `parents=[]` + 更新 ref 会制造 orphan commit，破坏类 Git 语义。
- spec 至少要有"第二次写入形成父子链"的 behavioral AC 或测试。

## 6. 反向 grep 防空跑

来源：`adapter-framework-20260517` 与多次 harness-lint follow-up。

错误模式：

```bash
! grep -rE "_visibility_visible" missing/path 2>/dev/null
```

目录不存在时 `grep` 返回 2，被 `!` 反转成 0，AC 在零代码状态下误 PASS。

修复模板：

```bash
test -f <target_file> \
  && grep -q "<positive assertion>" <target_file> \
  && ! grep -rE "<negative pattern>" <target_dir>
```

要求：

- `test -f` / `test -d` 前置证明目标存在。
- 正向 grep 证明确实实现了预期。
- 不写 `2>/dev/null` 吞路径错误。

## 7. process_tasks 六节点

来源：`adapter-framework-20260517`。

tasks.md 不能只列实现任务，还要列流程节点：

- stage-2 spec/tasks review
- stage-4 coding review
- stage-6 test report + unit-test review
- stage-7 CI / push gate
- stage-9 deploy verify，noop 也要写
- stage-10 close / user confirmation / SKILL 反哺

## 8. summary frontmatter 先行

来源：`processor-framework-20260517`。

进入 change 目录第一动作是填 `summary.md` frontmatter，再写 spec/tasks。每完成一个阶段，同一次编辑更新 summary 阶段进度和 `last_updated`。

自查：

```bash
grep -cE "<feature-slug>|<YYYY-MM-DDTHH:MM:SSZ>|<复述|<bullet list>|<负责人>" summary.md
```

期望为 0。
