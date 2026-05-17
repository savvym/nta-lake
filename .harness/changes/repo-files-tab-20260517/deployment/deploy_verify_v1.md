---
change_id: repo-files-tab-20260517
version: 1
env: dev
status: deployed
---

# Deploy Verify v1

- API 已重启含 /refs/{ref_name} + cookie secure env toggle
- Worker 重启（添加 dataplat_api.adapters import 已在前次集成；本次无改动）
- Vite HMR 自动热更 FilesSection
- 浏览器实测：访问 `/repos/{o}/{n}` 看到 Files Card；已 commit 的 repo 显文件表 + 下载链；空 repo 显空状态
