# _template/

> 这是变更目录的标准模板。**不要直接在这里改动**——通过 `cp -r _template <new-change-id>` 复制一份再填。
>
> ⚠️ **本文件不应出现在任何具体 change 目录里**。如果你在 `.harness/changes/<feature-slug>-<yyyymmdd>/README.md` 看到此提示，说明 cp 之后忘了删——立即 `rm` 掉，再编辑 summary.md。

## 使用

```bash
cp -r .harness/changes/_template .harness/changes/<feature-slug>-$(date +%Y%m%d)
rm .harness/changes/<feature-slug>-$(date +%Y%m%d)/README.md   # ⚠️ 不要漏
cd .harness/changes/<feature-slug>-$(date +%Y%m%d)
# 编辑 summary.md，开始阶段 1
```

## 各文件作用

| 文件 | 阶段 | 何时填 |
|---|---|---|
| `summary.md` | 全程 | 每次阶段进出 |
| `request_analysis/spec.md` | 1 | Generator 进入阶段 1 |
| `request_analysis/tasks.md` | 1 | 同上 |
| `request_analysis/review/spec_review_v1.md` | 2 | Reviewer 写第一轮评审 |
| `request_analysis/review/tasks_review_v1.md` | 2 | 同上 |
| `coding/coding_report_v1.md` | 3 | Generator 完成编码 |
| `coding/review/code_review_v1.md` | 4 | Reviewer 写第一轮代码评审 |
| `unit_test/test_report_v1.md` | 5 | Generator 完成单测 |
| `unit_test/review/test_review_v1.md` | 6 | Reviewer 写第一轮单测评审 |
| `ci_result/ci_result_v1.md` | 8 | unit-test-ci Skill 收集 |
| `deployment/deploy_verify_v1.md` | 9 | deploy-verify Skill 执行 |

## 删除规则

- 本 change **不涉及部署面** → 可删 `deployment/` 整目录，并在 `summary.md` 阶段 9 行写 "skipped: no deploy surface"。
- 本 change **不涉及代码** → coding/ unit_test/ ci_result/ deployment/ 都可删，但 spec.md 必须保留。
- 不允许删 `request_analysis/`——所有变更都从需求分析起步。

## 版本递增

review 与 generator 产物用 `_v{N}.md` 后缀。不通过 → 新文件，不要覆盖原文件。
