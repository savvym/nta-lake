---
change_id: bootstrap-monorepo-20260516
target: tasks.md
target_version: 1
review_version: 1
reviewer: claude-agent:bootstrap-monorepo-stage2-reviewer
reviewed_at: 2026-05-16T20:50:00Z
verdict: REVISION REQUIRED
---

# Tasks Review v1

## 检查清单结论

> 引用 `.harness/skills/expert-reviewer/SKILL.md` §1（plan 模式 tasks.md）。

- [x] 每个任务粒度合理（1-3 小时）——18 个 T-* 都是单文件 / 小组文件，目测 30-90 min/个。
- [x] depends_on 形成 DAG，无环（手工拓扑排序：T-1/T-2/T-4/T-5/T-13/T-14/T-15 是 source；T-3 需要 T-1,T-2；T-6 需要 T-1；T-8 需要 T-2；T-7 需要 T-6；T-9/T-10/T-11 需要 T-1；T-12 需要 T-2；T-16 需要 T-6,T-12；T-17 需要 T-3,T-6,T-8,T-16；T-18 需要 T-8——无回边）。
- [x] 评审 / 单测 / CI 阶段对应任务都有（P-spec-review / P-code-review / P-test-review / P-push / P-ci / P-deploy / P-user-confirm 7 项齐全）。
- [x] 没有"做完整个系统"类目标任务——每个 T-* 都对应具体文件/配置。
- [~] 每条 AC 都有 T-* 覆盖——名义上 17/17（见 §AC 覆盖矩阵），但 AC-9 / AC-14 存在"命令 vs 任务"不一致（详见 MUST FIX）。

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | tasks.md T-9 / T-10 / T-11（行 77-99）vs spec.md AC-9（行 77） | T-9/T-10/T-11 均明确 **src layout**（`src/dataplat_core/__init__.py`、`src/dataplat_sdk/__init__.py`、`src/dataplat_worker/__init__.py`），但 spec AC-9 的机械化命令是 `test -f $d/dataplat_*/__init__.py`（无 `src/`）。本地实测：按 tasks 的 src layout 实施 → AC-9 命令 exit 1 → stage 8 自检必失败。这是 tasks 与 spec 矛盾，需在评审阶段对齐。 | 在评审反馈中要求作者二选一：(a) tasks 改为 flat layout（`$d/dataplat_<name>/__init__.py`），同步删 `src layout` 描述；(b) spec AC-9 命令改为含 `src/`。建议 (a)：对仅占位的包 src layout 收益不大且与 AC 更直白。**注意：若选 (b)，spec MUST FIX #1 也需同步修。** |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | tasks.md T-16（行 133-139） | 描述 `python -m scripts.export_openapi` 调用，但未要求创建 `scripts/__init__.py`。Python `-m` 模式需要 package，否则 `ModuleNotFoundError`。当前 AC-14 表用 ast.parse 绕过，但 Makefile codegen target（T-3）与 CI codegen-check（T-17）若改用 `python -m` 会触雷。 | 在 T-16 description 显式加入 `scripts/__init__.py`（空文件即可），或改用 `python scripts/export_openapi.py` 调用方式并同步 Makefile/CI。 |
| 2 | tasks.md T-17 CI（行 141-147）与 spec §非范围（行 62） | T-17 描述含 `python-test` 跑 `pytest --junitxml`，但仓库无远端，CI 不实际触发。若 CI yml 把 `python-test` 写得过细（如 matrix Python 版本、Postgres service），实施时易越界。 | 在 T-17 description 末尾追加 "本变更内 CI yml 仅为静态 yaml；service / matrix / cache 配置允许后续 `harness-remote-push-*` 收紧"，避免实施期 scope creep。 |
| 3 | tasks.md T-3 Makefile（行 30-35） | Makefile recipe 必须以 **tab** 而非空格开头，否则 `make: *** missing separator. Stop.`。这是新成员（含 LLM 代笔）常踩的坑，应在 task description 中显式提醒。 | 在 T-3 description 加一行 "recipe 行须以 tab 开头；可用 `cat -A Makefile \| grep '^\\^I'` 校验"，并把这条作为 T-3 自检步骤。 |
| 4 | tasks.md §process_tasks P-spec-review（行 162-164） | 缺 reason / blocked_by 字段，与 P-push / P-ci / P-deploy / P-user-confirm 不对称；P-test-review / P-code-review 同样无 reason 字段。 | 统一格式：所有 process_tasks 至少含 `id / estimated_stage / status / reason`；可保留空 reason `""` 但字段存在，便于 lint。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | tasks.md §验收覆盖矩阵（行 209-229） | AC-7 列两个任务（T-6, T-7）；AC-9 列三个（T-9, T-10, T-11）；其他 AC 多为 1 任务。建议把 AC 覆盖矩阵从"关联"升级为"主任务 / 测试任务"两列，便于 stage 6 单测评审快速核对。 | 把矩阵分列 `产物任务` / `测试任务`。当前是 nice-to-have，不阻塞 stage 2。 |
| 2 | tasks.md T-14 docker-compose（行 118-123） | description 含 `minio-init` 但 spec AC-12 不门禁它；若实施时省略，AC 仍能通过，未来 onboarding 时建 bucket 步骤会缺失。 | 要么把 `minio-init` 升入 AC-12（见 spec NICE-HAVE #2），要么在 T-14 强调"AC 不门禁但本任务仍必须含 minio-init"。 |
| 3 | tasks.md T-18 测试 / build smoke（行 149-155） | "或仅依赖 `pnpm --filter web build` 作为 smoke（择一）" 留两可。stage 6 评审会想知道选了哪条；建议 spec/tasks 阶段就定。 | 在 T-18 中选定 build smoke（更轻量），把 vitest 留到后续业务变更。 |

## DAG 与覆盖矩阵实测

- 拓扑排序成功：T-1 → T-{3,6,9,10,11} → T-{7,16,17,18} 全部可达，无环。
- 名义覆盖 17/17：每条 AC 至少有一个 T-*；但因 MUST FIX #1，AC-9 的"真实覆盖"待对齐。
- process_tasks 7 项覆盖 stage 2-10 全部阶段（含 stage 9 skipped + stage 10 self-confirm）。

## 风险评估补充

spec §风险与 tasks 隐含风险大体一致；tasks 层面额外提醒：

- T-6（apps/api）+ T-17（CI）+ T-16（codegen）形成关键路径，任一失败会让 AC-15 / AC-16 同时受阻；建议实施时先把 T-6 跑通到 `/healthz` 200 再开 T-16/T-17。
- T-14（docker-compose）独立无依赖，可与 T-1/T-2 并行；建议在 coding stage 排在最前以最大化并行收益。

## Verdict

REVISION REQUIRED（MUST FIX 数 = 1）

> 说明：唯一 MUST FIX 与 spec_review_v1 的 MUST FIX #1 是同一个"AC-9 vs T-9/10/11 layout 矛盾"——任一文件改即可消化两者。Generator 在 v2 中需保证两份文件一致。

## 复检指引

Generator 修完 tasks_v2.md（与 spec_v2.md 同步）后自检：

1. AC-9 与 T-9/T-10/T-11 layout 一致性：
   ```bash
   # 提取 spec AC-9 命令里的路径模式
   grep -nE "dataplat_.*__init__\\.py" .harness/changes/bootstrap-monorepo-20260516/request_analysis/spec.md
   # 提取 tasks T-9/10/11 的 init 文件路径
   grep -nE "(src/)?dataplat_(core|sdk|worker)/__init__\\.py" .harness/changes/bootstrap-monorepo-20260516/request_analysis/tasks.md
   ```
   两侧路径写法必须能用同一条 shell 命令验证。
2. DAG 复检：
   ```bash
   python3 -c "
   import yaml,re,sys
   t=open('.harness/changes/bootstrap-monorepo-20260516/request_analysis/tasks.md').read()
   block=re.search(r'\`\`\`yaml\\n(tasks:.*?)\\n\`\`\`',t,re.S).group(1)
   d=yaml.safe_load(block)
   ids={x['id'] for x in d['tasks']}
   for x in d['tasks']:
       for dep in x.get('depends_on',[]):
           assert dep in ids, f'{x[\"id\"]} -> {dep} missing'
   print('DAG OK')
   "
   ```
3. 覆盖矩阵：每条 AC 至少一个 T-* 关联（无 SHOULD FIX 时 NICE-HAVE #1 不强制）。

提交 v2 后开 `tasks_review_v2.md`。
