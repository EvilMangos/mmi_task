#!/bin/bash

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <branch-name>"
    echo "Example: $0 feature/my-feature"
    exit 1
fi

BRANCH_NAME="$1"
REPO_ROOT=$(git rev-parse --show-toplevel)
REPO_NAME=$(basename "$REPO_ROOT")
WORKTREE_DIR="${REPO_ROOT}/../${REPO_NAME}-${BRANCH_NAME//\//-}"

# Check if branch exists locally or remotely
if git show-ref --verify --quiet "refs/heads/$BRANCH_NAME"; then
    echo "Branch '$BRANCH_NAME' exists locally, creating worktree..."
    git worktree add "$WORKTREE_DIR" "$BRANCH_NAME"
elif git show-ref --verify --quiet "refs/remotes/origin/$BRANCH_NAME"; then
    echo "Branch '$BRANCH_NAME' exists on remote, creating worktree..."
    git worktree add "$WORKTREE_DIR" "$BRANCH_NAME"
else
    echo "Branch '$BRANCH_NAME' does not exist, creating new branch and worktree..."
    git worktree add -b "$BRANCH_NAME" "$WORKTREE_DIR"
fi

echo ""
echo "Worktree created at: $WORKTREE_DIR"
echo "To switch to it: cd $WORKTREE_DIR"