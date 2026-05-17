---
change_id: repo-files-tab-20260517
version: 1
status: waiting_review
---

# Test Report v1

## AC ↔ 测试

- AC-1~8 self_check（grep + python -c）
- AC-9 前端 8 文件 13 测试 PASS
- AC-10 后端 test_refs.py 3 集成（PG + MinIO）
- AC-11~13 self_check

## 运行

```
pytest test_refs.py → 3 PASS
pnpm test → 8 files / 13 tests PASS
```
