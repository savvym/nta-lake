"""从 dataplat FastAPI app 导出 OpenAPI JSON，写入 packages/api-types/openapi.json。

被 `make codegen` 调用：
    uv run python -m scripts.export_openapi

接着 pnpm --filter @dataplat/api-types run generate 会把 openapi.json 转成 TS 类型
（当前为占位，待 repo-api-mvp 变更引入 openapi-typescript）。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = REPO_ROOT / "packages" / "api-types" / "openapi.json"


def main() -> int:
    # 把 apps/api 加入 sys.path 才能 import dataplat_api
    api_src = REPO_ROOT / "apps" / "api"
    if str(api_src) not in sys.path:
        sys.path.insert(0, str(api_src))

    try:
        from dataplat_api.main import app  # noqa: PLC0415
    except ImportError as exc:
        print(f"无法 import dataplat_api.main: {exc}", file=sys.stderr)
        print("提示：先 `uv sync` 装好 apps/api 依赖，或者从仓库根 `uv run python -m scripts.export_openapi`", file=sys.stderr)
        return 1

    schema = app.openapi()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(schema, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"OpenAPI 已导出 → {OUTPUT_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
