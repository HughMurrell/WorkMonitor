#!/bin/bash

# Script to create and push an empty commit to record work start/stop times
# Usage: ./repoMonitor.sh start=<repository_path> or ./repoMonitor.sh stop=<repository_path>

# Check if parameter is provided
if [ -z "$1" ]; then
    echo "Error: Parameter is required"
    echo "Usage: ./repoMonitor.sh start=<repository_path>"
    echo "   or: ./repoMonitor.sh stop=<repository_path>"
    exit 1
fi

# Parse the named parameter
PARAM="$1"
if [[ "$PARAM" =~ ^start=(.+)$ ]]; then
    ACTION="start"
    REPO_PATH="${BASH_REMATCH[1]}"
elif [[ "$PARAM" =~ ^stop=(.+)$ ]]; then
    ACTION="stop"
    REPO_PATH="${BASH_REMATCH[1]}"
else
    echo "Error: Invalid parameter format"
    echo "Usage: ./repoMonitor.sh start=<repository_path>"
    echo "   or: ./repoMonitor.sh stop=<repository_path>"
    exit 1
fi

# Check if the repository path exists
if [ ! -d "$REPO_PATH" ]; then
    echo "Error: Repository path does not exist: $REPO_PATH"
    exit 1
fi

# Check if it's a git repository
if [ ! -d "$REPO_PATH/.git" ]; then
    echo "Error: Not a git repository: $REPO_PATH"
    exit 1
fi

# Change to the repository directory
cd "$REPO_PATH" || exit 1

# Check if there are any staged changes
if ! git diff --cached --quiet; then
    echo "Error: There are staged changes in the repository"
    echo "Please commit all changes before running repoMonitor.sh"
    exit 1
fi

# Extract repository name from local git repository (top-level directory name)
GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [ -z "$GIT_ROOT" ]; then
    echo "Error: Could not determine git repository root"
    exit 1
fi

REPO_NAME=$(basename "$GIT_ROOT")

# Detect the default branch (main or master)
# Try to get the default branch from the remote tracking branch
DEFAULT_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
if [ -z "$DEFAULT_BRANCH" ]; then
    # Fallback: check if main exists, otherwise use master
    if git show-ref --verify --quiet refs/heads/main 2>/dev/null; then
        DEFAULT_BRANCH="main"
    elif git show-ref --verify --quiet refs/heads/master 2>/dev/null; then
        DEFAULT_BRANCH="master"
    else
        # Last resort: try to get current branch
        DEFAULT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
        if [ -z "$DEFAULT_BRANCH" ]; then
            echo "Error: Could not determine default branch"
            exit 1
        fi
    fi
fi

# Create commit message based on action
if [ "$ACTION" = "start" ]; then
    COMMIT_MSG="START work on $REPO_NAME"
else
    COMMIT_MSG="STOP work on $REPO_NAME"
fi

# Create an empty commit
git commit --allow-empty -m "$COMMIT_MSG"

# Push to GitHub using the detected default branch
git push origin "$DEFAULT_BRANCH"

echo "Empty commit created and pushed with message: $COMMIT_MSG"
echo "Repository: $REPO_PATH"

