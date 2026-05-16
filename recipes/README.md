# recipes/

Pipeline YAML 声明文件。每个 recipe 描述一个 Processor DAG，可被平台执行生成下游数据集。

## 当前状态

bootstrap-monorepo 骨架占位——**目录为空**（仅含子目录 `examples/`）。

## 结构约定

```
recipes/
├── examples/           # 文档型示例，不直接跑生产
└── <team>/<name>.yaml  # 团队级 recipe，归属团队 owner
```

## 示例（设计意图，未实际落地）

```yaml
name: cn-lit-sft-v1
nodes:
  - id: normalize_pdfs
    processor: pdf-to-document@v0.2
    inputs: [bronze/cn-lit/jinyong-wuxia-pdfs@main]
    output: silver/cn-lit/jinyong-normalized@auto
  ...
```

详见 [.harness/design.md](../.harness/design.md) §4.3。
