"""从 markdown / HTML 文本里提取 image URL 列表。

抓 `<img src="...">`（HTML）+ `![alt](...)`（markdown）；用 urljoin 解析相对路径。
data: / javascript: / ftp:// 等非 http(s) 跳过。结果按出现顺序去重。
"""

from __future__ import annotations

import re
from urllib.parse import urljoin

_HTML_IMG_RE = re.compile(r"""<img[^>]*\bsrc=["']([^"']+)["']""", re.IGNORECASE)
_MD_IMG_RE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")


def extract_image_urls(content: str, base_url: str) -> list[str]:
    """从 markdown / HTML 内容中提取 image URL，绝对化 + 去重 + 按文档出现顺序保序。"""
    matches = list(_HTML_IMG_RE.finditer(content)) + list(
        _MD_IMG_RE.finditer(content)
    )
    matches.sort(key=lambda m: m.start())
    raw: list[str] = [m.group(1) for m in matches]

    seen: set[str] = set()
    out: list[str] = []
    for src in raw:
        src = src.strip()
        if not src:
            continue
        if src.startswith(("data:", "javascript:", "ftp://", "mailto:")):
            continue
        absolute = urljoin(base_url, src)
        if not absolute.lower().startswith(("http://", "https://")):
            continue
        if absolute in seen:
            continue
        seen.add(absolute)
        out.append(absolute)
    return out
