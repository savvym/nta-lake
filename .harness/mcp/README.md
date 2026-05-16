# .harness/mcp/

> MCP（Model Context Protocol）server 配置占位。

## 当前状态

**Phase 0：空占位**。本目录暂时不包含任何配置文件。

## 何时启用

当出现以下任一需求时，回到这里登记并配置 MCP server：

- **GitHub / GitLab MCP**：让 Agent 直接读 issue / PR / 评论，而不是靠 `gh` CLI 字符串拼接。
- **Linear / Jira MCP**：把外部任务系统同步进 Application Owner 的工作流。
- **内部 Wiki / Confluence MCP**：让 `wiki/` 之外的组织知识也可被 Agent 检索。
- **私有 LLM Gateway MCP**：让其他 Agent / 工具复用我们的 LLM Gateway 而不必直连 provider。

## 落地约定

启用任何 MCP server 必须：

1. **写一份 ADR**（`wiki/adr/`）：为什么引入、解决什么问题、安全边界、权限范围。
2. **配置文件放本目录**：`<server-name>.json` 或 `<server-name>.yaml`，含 endpoint、scopes、是否走 SSO。
3. **secret 不入库**：通过环境变量或 secret manager 注入；本目录配置文件只放 placeholder。
4. **使用文档写在 `wiki/architecture.md`** 的"外部集成"段。

## 不要做的事

- 把 MCP 配置散落在 `apps/api` 或 `worker/` 里。统一进这个目录。
- 用 MCP 接管本来该走 `.harness/skills/` 的流程——MCP 是数据 / 工具通道，不是流程编排器。
