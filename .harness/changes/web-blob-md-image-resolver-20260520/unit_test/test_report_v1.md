---
change_id: web-blob-md-image-resolver-20260520
version: 1
status: waiting_review
---

# Test Report v1

## AC 映射

| AC | 测试 |
|---|---|
| AC-6 | blob.test.tsx 6 新 + 3 helper 单测：md image rewrite / 绝对 URL / no commit / resolveImagePath 3 路径模式 |
| AC-7 | typecheck 0 errors |
| AC-8 | 全 vitest 39 passed |

## 文件

| 文件 | 用例 |
|---|---|
| blob.test.tsx | 9（baseline 3 + 新 3 markdown + 3 helper） |
| 其他 | 30 不变 |

## Mock

mockBlobMeta + 新 mockSubtreeByPath（vi.fn）；不 mock react-markdown 让真渲染；vi.spyOn(globalThis, "fetch") 模拟 md 文本。
img 查询用 document.querySelector("img") 因为 react-markdown 渲染的 img alt 为空时 implicit role 非 "img"。

## 本地

39 passed (16 files); typecheck 0 errors; self_check 18/18.
