#!/usr/bin/env bash
# Create a new harness change (v2 3-phase) and switch to its git branch.
#
# Usage:
#   bash scripts/harness_new_change.sh <change-id> [title]
#
# v2 (2026-05-20) 简化流程：
#   - change 目录只含 5 个文件：summary.md / design.md / design_review.md /
#     implementation.md / verify_review.md
#   - 废除 v1 的 request_analysis/ coding/ unit_test/ ci_result/ deployment/ 子目录
#   - git branch 仍是 change/<change-id>
#
# 详见 .harness/rules/development-process.md。

set -euo pipefail

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
  echo "usage: bash scripts/harness_new_change.sh <change-id> [title]" >&2
  exit 2
fi

CHANGE_ID="$1"
TITLE="${2:-$CHANGE_ID}"
BRANCH="change/$CHANGE_ID"

case "$CHANGE_ID" in
  *[!A-Za-z0-9._-]* | "" )
    echo "invalid change-id: $CHANGE_ID" >&2
    echo "allowed characters: A-Z a-z 0-9 . _ -" >&2
    exit 2
    ;;
esac

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "not inside a git worktree" >&2
  exit 1
fi

if [ "${HARNESS_ALLOW_DIRTY:-0}" != "1" ] && [ -n "$(git status --porcelain)" ]; then
  echo "worktree is dirty; commit/stash first, or set HARNESS_ALLOW_DIRTY=1" >&2
  git status --short >&2
  exit 1
fi

CHANGE_DIR=".harness/changes/$CHANGE_ID"
if [ -e "$CHANGE_DIR" ]; then
  echo "change directory already exists: $CHANGE_DIR" >&2
  exit 1
fi

if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
  echo "branch already exists: $BRANCH" >&2
  exit 1
fi

git switch -c "$BRANCH"

cp -R .harness/changes/_template "$CHANGE_DIR"

TS="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
BASE_SHA="$(git rev-parse --short HEAD)"

python3 - "$CHANGE_DIR" "$CHANGE_ID" "$TITLE" "$TS" "$BRANCH" "$BASE_SHA" <<'PY'
from pathlib import Path
import sys

change_dir = Path(sys.argv[1])
change_id, title, ts, branch, base_sha = sys.argv[2:7]

summary = change_dir / "summary.md"
design = change_dir / "design.md"
implementation = change_dir / "implementation.md"


def update_frontmatter(path: Path, values: dict[str, str]) -> None:
    lines = path.read_text().splitlines()
    if not lines or lines[0] != "---":
        raise SystemExit(f"{path} does not start with YAML frontmatter")

    end = None
    for i in range(1, len(lines)):
        if lines[i] == "---":
            end = i
            break
    if end is None:
        raise SystemExit(f"{path} frontmatter is not closed")

    for i in range(1, end):
        for key, value in values.items():
            if lines[i].startswith(f"{key}:"):
                lines[i] = f"{key}: {value}"
    path.write_text("\n".join(lines) + "\n")


update_frontmatter(
    summary,
    {
        "change_id": change_id,
        "title": title,
        "owner": "application-owner-agent",
        "started_at": ts,
        "last_updated": ts,
        "phase": "design",
        "status": "in_progress",
    },
)
summary_text = summary.read_text().replace("Branch：`change/<change-id>`", f"Branch：`{branch}`")
summary.write_text(summary_text)

update_frontmatter(design, {"change_id": change_id, "authored_at": ts})
design_text = design.read_text().replace("# Design：<标题>", f"# Design：{title}", 1)
design.write_text(design_text)

update_frontmatter(implementation, {"change_id": change_id, "base_commit": base_sha, "branch": branch})

# design_review.md / verify_review.md 留空模板，filled when reviewers spawn
for fname in ("design_review.md", "verify_review.md"):
    p = change_dir / fname
    update_frontmatter(p, {"change_id": change_id})
PY

echo "created $CHANGE_DIR"
echo "switched to $BRANCH"
echo ""
echo "next:"
echo "  1. 填 $CHANGE_DIR/design.md（Phase 1 Design，由 application-owner / opus 完成）"
echo "  2. 完成后 spawn opus reviewer 写 $CHANGE_DIR/design_review.md"
echo "  3. APPROVED → spawn sonnet 执行 Phase 2 → 写 implementation.md"
echo "  4. Phase 2 完成后 spawn opus reviewer 写 verify_review.md"
echo "  5. APPROVED → merge to main + close"
echo ""
echo "详见 .harness/rules/development-process.md"
