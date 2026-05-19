#!/usr/bin/env bash
# Create a new harness change and switch to its git branch.
#
# Usage:
#   bash scripts/harness_new_change.sh <change-id> [title]
#
# Policy:
#   - change artifacts live in .harness/changes/<change-id>/
#   - git branch is change/<change-id>
#   - start from a clean worktree unless HARNESS_ALLOW_DIRTY=1 is set

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
rm -f "$CHANGE_DIR/README.md"

TS="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
BASE_SHA="$(git rev-parse --short HEAD)"

python3 - "$CHANGE_DIR" "$CHANGE_ID" "$TITLE" "$TS" "$BRANCH" "$BASE_SHA" <<'PY'
from pathlib import Path
import sys

change_dir = Path(sys.argv[1])
change_id, title, ts, branch, base_sha = sys.argv[2:7]

summary = change_dir / "summary.md"
spec = change_dir / "request_analysis" / "spec.md"
coding = change_dir / "coding" / "coding_report_v1.md"
ci = change_dir / "ci_result" / "ci_result_v1.md"

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
    },
)
summary_text = summary.read_text().replace("Branch：`change/<change-id>`", f"Branch：`{branch}`")
summary.write_text(summary_text)

update_frontmatter(spec, {"change_id": change_id, "authored_at": ts})
spec_text = spec.read_text().replace("# Spec：<标题>", f"# Spec：{title}", 1)
spec.write_text(spec_text)

update_frontmatter(coding, {"change_id": change_id, "branch": branch, "base_commit": base_sha})
update_frontmatter(ci, {"change_id": change_id, "branch": branch})
PY

echo "created $CHANGE_DIR"
echo "switched to $BRANCH"
