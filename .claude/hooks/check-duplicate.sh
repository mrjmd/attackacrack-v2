#!/bin/bash
# check-duplicate.sh - Prevent duplicate implementations

FILE_PATH="${1:-$CLAUDE_FILE_PATH}"

# Skip if not implementation file
if [[ ! "$FILE_PATH" =~ \.(py|ts|svelte)$ ]]; then
    exit 0
fi

echo "🔍 Checking for duplicate implementations..."

# Extract function/class name being added (simple heuristic)
if [[ "$FILE_PATH" =~ \.py$ ]]; then
    # Look for Python functions and classes
    PATTERN="def |class "
elif [[ "$FILE_PATH" =~ \.(ts|svelte)$ ]]; then
    # Look for TypeScript/JavaScript functions and classes
    PATTERN="function |class |const.*= "
fi

# Check if similar implementations exist elsewhere
if [[ "$FILE_PATH" =~ backend/ ]]; then
    SEARCH_DIR="backend/app"
elif [[ "$FILE_PATH" =~ frontend/ ]]; then
    SEARCH_DIR="frontend/src"
else
    exit 0
fi

# Count similar patterns (this is a simple check)
DUPLICATES=$(grep -r "$PATTERN" "$SEARCH_DIR" 2>/dev/null | grep -v "$FILE_PATH" | head -5)

if [ -n "$DUPLICATES" ]; then
    echo "⚠️ WARNING: Similar implementations found:"
    echo "$DUPLICATES" | head -3
    echo ""
    echo "💡 Check if you're duplicating existing functionality"
    echo "💡 v1 failed due to 3x duplication - let's avoid that!"
fi

exit 0  # Warning only, don't block