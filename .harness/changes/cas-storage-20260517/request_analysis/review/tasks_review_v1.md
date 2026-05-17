---
change_id: cas-storage-20260517
reviewer: claude-agent:cas-storage-stage2-reviewer
target: request_analysis/tasks.md
target_version: v1
reviewed_at: 2026-05-17T04:00:00Z
mode: plan
verdict: REVISION REQUIRED
must_fix_count: 2
should_fix_count: 4
nice_count: 2
---

# Tasks Review v1 — cas-storage-20260517

## 检查清单结论

- 任务粒度（1-3h）：基本 PASS，但 **T-6 偏重**（5-7h，见 SHOULD FIX-1）
- depends_on 无环：PASS（拓扑序 `{T-1,T-3,T-4} → T-2 → T-6 → T-5 → {T-7,T-8} → T-9`，无环）
- 评审 / 单测 / CI process_tasks 完整：PASS（P-spec/code/test-review + P-push + P-ci + P-deploy(skipped) + P-user-confirm）
- 没有 "做完整个系统" 目标任务：PASS
- 每条 AC 都有 T-* 覆盖：表面 17/17 PASS，但 AC-5 / AC-8 / AC-15 覆盖**质量**有问题（见下）

## 任务粒度

| Task | 估时 | 备注 |
|---|---|---|
| T-1 | 1h | Protocol 5 方法 + Pydantic 模型 |
| T-2 | 0.2h | __all__ 追加 |
| T-3 | 0.2h | pyproject 加依赖 |
| T-4 | 1h | 一个函数 + 输入校验 |
| T-5 | 1h | 工厂 + lazy 单例 |
| **T-6** | **5-7h** | 覆盖 8 AC，6 个组件（HashingStream / _ensure_bucket / put+dedup / get async gen / exists / get_size / delete）|
| T-7 | 1.5h | 3 个 Protocol/Pydantic 用例 |
| T-8 | 3h | 5 个 MinIO 真连 + fixture 隔离 |
| T-9 | 1.5h | 17 AC + SKIP 探针 |

T-6 超 SKILL.md "1-3h" 上限——见 SHOULD FIX-1。

## AC ↔ Task 覆盖质量复核

| AC | 矩阵声明 | 真实覆盖质量 |
|---|---|---|
| AC-5 | T-5,T-6 | **MUST FIX-2**：T-5 工厂与 isinstance 无关联，应单独 T-6 |
| AC-8 | T-6 | **不完整**（dedup 路径未在 description 提）→ 见 MUST FIX-1 |
| AC-13 | T-6 | 部分（"upload_fileobj 单次扫流"已写，但 dedup 临时 key 流程下能否保证流式未明）|
| AC-15 | T-8 | 部分（fixture 隔离描述与 spec §范围段冲突未在 task 层 reflect）→ 见 SHOULD FIX-3 |
| AC-16 | "全部" | 表述偷懒，但语义 OK |

其他 12 AC（AC-1,2,3,4,6,7,9,10,11,12,14,17）覆盖质量 PASS。

## 分级问题列表

### MUST FIX

1. **任务受上游 spec MUST FIX 拖累，必须随 spec_v2 同改**（T-1 / T-6 description）：
   - spec MUST FIX-1（AC-1 永真）→ T-1 description 同步 `_is_runtime_protocol=True` 要求
   - spec MUST FIX-2（dedup 路径）→ T-6 description 必须明示 6 步算法（`_tmp/{uuid}` → upload_fileobj → head_object → copy_object → delete tmp）；当前 description 完全没提
   - spec MUST FIX-3（stream 类型 BinaryIO）→ T-1 description 同步
   - spec MUST FIX-4（iter_keys 一致性）→ 若 summary 删 iter_keys 则 T-1 不动；若加则需拆 T-1a
   - spec MUST FIX-5（delete 去留）→ 若移除则 T-1/T-6 description 删 delete；若加 AC-15(f) 则 T-6/T-8 加测试步骤

2. **T-5 与 AC-5 关联存疑**（line 47-53 + 覆盖矩阵 AC-5）：T-5 description "工厂 `get_blob_store()` 读 env" 与 AC-5 "MinioBlobStore 实现 BlobStore Protocol（isinstance 通过）" 无直接关系；AC-5 应只由 T-6 覆盖。修复方式二选一：(a) 覆盖矩阵 AC-5 删除 T-5；(b) T-5 description 加 "保证 `from dataplat_api.storage import MinioBlobStore` 顶层 import 暴露" 使 T-5 实际服务 AC-5。

### SHOULD FIX

1. **T-6 工作量超 1-3h 上限**：拆分为 T-6a（框架 + `__init__` + `_ensure_bucket` + HashingStream，覆盖 AC-5）/ T-6b（put + dedup 临时 key 路径，覆盖 AC-7,8,12,13）/ T-6c（get/exists/get_size，覆盖 AC-9,10,11；delete 视 spec MUST FIX-5 处置）。拆后每子任务 1.5-2.5h，stage 4 evidence-driven review 更易分块审。

2. **T-6 description 未明示 dedup 算法**（line 56-64）：当前只说 "put 用 HashingStream 包装 → upload_fileobj → 返回 BlobPutResult"，未提 dedup 如何做。spec_v2 闭环后 T-6（或拆分后的 T-6b）追加："1. `tmp_key=_tmp/{uuid4().hex}`；2. upload_fileobj(HashingStream(stream), bucket, tmp_key)；3. `sha256=wrapper.hexdigest()`，`target=storage_key_for(sha256)`；4. head_object(target) 404 → copy_object(tmp→target)，200 → 跳过；5. delete_object(tmp_key) always；6. 返 BlobPutResult(deduplicated=已存在?)"。

3. **T-8 fixture 隔离描述太粗**（line 80-87）：当前 "uuid 前缀 bucket 避免污染" 未说 bucket 命名规则 / setup_create+teardown_delete / 不读 env。改为："fixture `bucket=f'dataplat-test-{uuid4().hex[:8]}'`（lowercase 符合 MinIO 命名）；setup `_ensure_bucket` + teardown 清空后 `delete_bucket`；构造 `MinioBlobStore(endpoint_url=..., bucket=bucket, ...)` 不读 env `DATAPLAT_BLOB_BUCKET`。"

4. **T-9 SKIP 探针函数命名未对齐既有模板**（line 89-94）：scripts/_self_check.sh 已有 `_pg_reachable()` + `run_ac_skipif_no_pg()` 模板。T-9 应明示新增 `_minio_reachable()` + `run_ac_skipif_no_minio()` helper；AC-15/AC-17 用此包装。当前 description 仅说 "socket connect 探针"，命名约定散开。

### NICE TO HAVE

1. **P-deploy reason 偏简**（line 121-123）：当前 "无运行时部署面"。MinIO 集成测试算半个部署验证。改为 "无 service 部署；MinIO 集成由 stage 8 self_check.sh + docker-compose.dev.yml minio service（本机或 CI）覆盖。"

2. **覆盖矩阵 AC-16 "全部" 略偷懒**（line 161）：改为 "全部（lint/type 隐式约束）" 即可。

## Verdict

**REVISION REQUIRED**（2 条 MUST FIX 阻塞）

## 复检指引

Generator 修完 tasks_v2.md 后自查：

```bash
# 1) T-6 description 含 dedup 临时 key 算法关键词
grep -E "tmp_key|_tmp/|copy_object|临时 key" \
    .harness/changes/cas-storage-20260517/request_analysis/tasks.md && echo OK

# 2) T-1 description stream 类型已固化
grep -E "BinaryIO|IO\[bytes\]" \
    .harness/changes/cas-storage-20260517/request_analysis/tasks.md && echo OK

# 3) 覆盖矩阵 AC-5 不再同时挂 T-5（或 T-5 description 已加 import 暴露）
python3 -c "
import re
t = open('.harness/changes/cas-storage-20260517/request_analysis/tasks.md').read()
m = re.search(r'\| AC-5 \| ([^|]+) \|', t)
deps = [x.strip() for x in m.group(1).split(',')]
t5_desc = re.search(r'- id: T-5.*?depends_on', t, re.S).group(0)
if 'T-5' in deps and len(deps) > 1:
    assert 'import' in t5_desc or 'MinioBlobStore' in t5_desc, 'T-5 与 AC-5 关联仍不清'
print('AC-5 mapping OK')
"

# 4) T-6 是否拆分（SHOULD FIX-1）
grep -E "T-6a|T-6b|T-6c" \
    .harness/changes/cas-storage-20260517/request_analysis/tasks.md && echo "T-6 split"

# 5) T-9 SKIP helper 命名对齐
grep -E "_minio_reachable|run_ac_skipif_no_minio" \
    .harness/changes/cas-storage-20260517/request_analysis/tasks.md && echo OK

# 6) DAG 复核：手算或 yaml + toposort 确认无环
```

修完后在 summary.md stage 2 行追加 `v2 / verdict pending`，与 spec_review_v2 同次启 reviewer 子会话。
