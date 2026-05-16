"""`python -m dataplat_worker` 入口。

当前为 bootstrap-monorepo 占位：仅打印一行存活信号便退出。后续变更会引入真正的 RQ
worker.work() loop。
"""

from __future__ import annotations


def main() -> int:
    print("dataplat-worker placeholder: no jobs configured (bootstrap-monorepo skeleton).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
