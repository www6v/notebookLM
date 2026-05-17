#!/bin/bash
# Stage all changes, commit, and push the current branch (skip with -n).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

MESSAGE="add"
DO_PUSH=1

usage() {
    cat <<'EOF'
Usage: gitCommitOnly.sh [-m MESSAGE] [-n] [-h]

  -m MESSAGE   Commit message (default: add)
  -n           Commit only; do not push
  -h           Show this help

Examples:
  ./gitCommitOnly.sh
  ./gitCommitOnly.sh -m "feat: open API"
  ./gitCommitOnly.sh -m "fix: auth" -n
EOF
}

while getopts ":m:nh" opt; do
    case "$opt" in
        m) MESSAGE="$OPTARG" ;;
        n) DO_PUSH=0 ;;
        h)
            usage
            exit 0
            ;;
        *)
            usage >&2
            exit 1
            ;;
    esac
done

if ! git rev-parse --git-dir >/dev/null 2>&1; then
    echo "Error: not a git repository." >&2
    exit 1
fi

SECRET_PATTERN='\.env$|credentials\.json|\.pem$|id_rsa'
if git status --porcelain | grep -qE "$SECRET_PATTERN"; then
    echo "Warning: possible secret files in changes; review before commit." >&2
fi

git add -A

if git diff --cached --quiet; then
    echo "Nothing to commit."
    exit 0
fi

echo "Committing with message: $MESSAGE"
git commit -m "$MESSAGE"

if [ "$DO_PUSH" -eq 1 ]; then
    BRANCH="$(git branch --show-current)"
    if [ -z "$BRANCH" ]; then
        echo "Error: detached HEAD; cannot push." >&2
        exit 1
    fi
    echo "Pushing to origin/$BRANCH"
    git push origin "$BRANCH"
fi
