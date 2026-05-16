# plugins/

可插拔的 **Source Adapters**（把外部世界变成 Bronze Repository 的 commit）与 **Processors**（把上游 Repository@version 变成下游 Repository@new_version）。

## 当前状态

bootstrap-monorepo 骨架占位——**目录为空**。具体插件由后续变更引入：

- `adapter-raw-upload/`：手动上传文件 → Bronze
- `adapter-firecrawl/`：URL 抓取 → Bronze
- `processor-pdf-to-text/`：PDF 文本抽取
- `processor-html-to-md/`：HTML 转 Markdown
- `processor-dedup-minhash/`：MinHash 去重
- `processor-llm-qa-gen/`：通过 LLM Gateway 生成 QA 对

## 添加新插件

每个 plugin 是独立 Python 包，目录结构：

```
plugins/<adapter|processor>-<name>/
├── pyproject.toml      # entry_points 注册到平台
├── manifest.yaml       # 即便 MVP L1/L2 也写，便于 Phase 2+ 切容器
├── src/<pkg_name>/     # 实现
├── tests/
└── README.md           # 用途 / 输入 schema / 输出 subtype / 示例
```

详见 [.harness/rules/engineering-structure.md](../.harness/rules/engineering-structure.md)
与 [.harness/design.md](../.harness/design.md) §4.1 / §4.2 / §6.
