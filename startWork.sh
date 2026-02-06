#!/bin/bash

# Script to create and push an empty commit with a message starting with "START"
# Usage: ./startWork.sh <repository_path> [optional message suffix]

# Check if repository path is provided
if [ -z "$1" ]; then
    echo "Error: Repository path is required"
    echo "Usage: ./startWork.sh <repository_path> [optional message suffix]"
    exit 1
fi

REPO_PATH="$1"

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
    echo "Please commit all changes before running startWork.sh"
    exit 1
fi

# Default commit message
COMMIT_MSG="START"

# If a message suffix is provided, append it to "START"
if [ -n "$2" ]; then
    COMMIT_MSG="START $2"
fi

# Create an empty commit
git commit --allow-empty -m "$COMMIT_MSG"

# Push to GitHub (origin/main)
git push origin main

echo "Empty commit created and pushed with message: $COMMIT_MSG"
echo "Repository: $REPO_PATH"

